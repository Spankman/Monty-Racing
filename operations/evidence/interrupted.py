"""Always-step reconciliation. No inference, acquisition, secret reads or retry.

Encrypted checkpoints are salvage evidence only. We never fabricate a forecast
or overwrite a completed receipt after a worker interruption.
"""
from pathlib import Path
import json,shutil,sys
from operations.evidence.store import encoded,sha,write


def reconcile(root):
    results=[]
    root=Path(root)
    if root.is_symlink():raise ValueError('Symlink output root')
    for run in root.iterdir() if root.exists() else []:
        if run.is_symlink() or not run.is_dir():continue
        marker=run/'evidence-intent.json'
        if not marker.is_file() or marker.is_symlink():continue
        intent=json.loads(marker.read_text())
        if intent.get('schema')!='monty.evidence-intent.v1':continue
        target=run/'evidence-recovery.json'
        if target.exists():results.append(json.loads(target.read_text()));continue
        receipt=run/'public/receipt.json';completed=False
        if receipt.is_file() and not receipt.is_symlink():
            r=json.loads(receipt.read_text());forecast=run/'public/forecast.json'
            completed=(r.get('run_id')==intent['run_id'] and forecast.is_file() and not forecast.is_symlink() and sha(forecast.read_bytes())==r.get('forecast_sha256'))
        checkpoints=[]
        for index in sorted((run/'evidence-checkpoints').glob('*.json')):
            if index.is_symlink():continue
            item=json.loads(index.read_text());cipher=index.with_suffix('.cms')
            if item.get('run_id')!=intent['run_id'] or not cipher.is_file() or cipher.is_symlink() or sha(cipher.read_bytes())!=item.get('cipher_sha256'):continue
            checkpoints.append(dict(index=index.name,cipher_sha256=item['cipher_sha256'],manifest_sha256=item['manifest_sha256']))
        private=run/'private';cleanup='NOT_CREATED'
        if private.exists():
            if private.is_symlink():private.unlink()
            else:shutil.rmtree(private)
            cleanup='REMOVED'
        status='FINAL_RECEIPT_PRESENT' if completed else 'INTERRUPTED_INCOMPLETE_EVIDENCE' if checkpoints else 'INTERRUPTED_NO_RECOVERABLE_CHECKPOINT'
        value=dict(schema='monty.interruption-receipt.v1',run_id=intent['run_id'],status=status,
            expires_at=intent['expires_at'],checkpoints=checkpoints,plaintext_cleanup=cleanup,
            original_execution_status=r.get('status') if completed else None,
            selections_available=False,reason='Recovery evidence is not a completed model forecast; original request requires honest terminal failure handling')
        write(target,encoded(value));results.append(value)
    return results

if __name__=='__main__':print(json.dumps(reconcile(sys.argv[1])))


def recover_checkpoint(cipher,index_path,recovery_path,expected_recovery_sha,key,output,clock=None):
    """Recover interrupted files only; never upgrade them to a valid forecast."""
    import subprocess
    from datetime import datetime,timezone
    from operations.evidence.store import timestamp
    from operations.evidence.verify import safe_archive
    clock=clock or datetime.now(timezone.utc)
    b=Path(recovery_path).read_bytes()
    if sha(b)!=expected_recovery_sha:raise ValueError('Recovery receipt anchor mismatch')
    recovery=json.loads(b);index_bytes=Path(index_path).read_bytes();index=json.loads(index_bytes)
    anchored=next((x for x in recovery['checkpoints'] if x['index']==Path(index_path).name),None)
    if not anchored or any(index.get(k)!=anchored[k] for k in ('cipher_sha256','manifest_sha256')):raise ValueError('Checkpoint not bound to recovery receipt')
    if clock>=timestamp(recovery['expires_at']) or clock>=timestamp(index['expires_at']):raise ValueError('Recovery evidence expired')
    raw=Path(cipher).read_bytes()
    if sha(raw)!=index['cipher_sha256']:raise ValueError('Checkpoint cipher changed')
    result=subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-inkey',str(key)],input=raw,capture_output=True)
    if result.returncode:raise ValueError('Authenticated checkpoint decryption failed')
    z=safe_archive(result.stdout);manifest=json.loads(z.read('manifest.json'))
    if sha(z.read('manifest.json'))!=index['manifest_sha256'] or manifest['run_id']!=recovery['run_id']:raise ValueError('Checkpoint manifest identity mismatch')
    expected={'manifest.json'}|{'private/'+r['path'] for r in manifest['files']}
    if set(z.namelist())!=expected:raise ValueError('Checkpoint file set differs')
    for row in manifest['files']:
        raw=z.read('private/'+row['path'])
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Checkpoint file integrity failure')
    output=Path(output).resolve();repo=Path(__file__).resolve().parents[2]
    if output.exists() or output==repo or repo in output.parents:raise ValueError('New private directory outside repository required')
    output.mkdir(parents=True,mode=0o700)
    for row in manifest['files']:write(output/row['path'],z.read('private/'+row['path']))
    write(output/'interrupted-manifest.json',z.read('manifest.json'))
    return dict(run_id=manifest['run_id'],files=len(manifest['files']),status='INTERRUPTED_EVIDENCE_ONLY',selections_available=False)
