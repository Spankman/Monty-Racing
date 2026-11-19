"""Verify research artifact bundles without claiming pre-off proof or immutability."""
import argparse, csv, hashlib, json
from pathlib import Path

def verify(manifest_path, ledger_path, base_dir=None):
    manifest_path=Path(manifest_path);ledger_path=Path(ledger_path)
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('schema')!='monty-research-evidence-v1':raise ValueError('Unknown manifest schema')
    if manifest.get('pre_off_proven') is not False or manifest.get('durably_immutable') is not False:
        raise ValueError('Unverified timing/immutability claims')
    base=Path(base_dir) if base_dir else manifest_path.parent
    hashes=manifest.get('files_sha256')
    if not isinstance(hashes,dict) or len(hashes)<3:raise ValueError('Incomplete evidence hash list')
    for name,expected in hashes.items():
        if Path(name).name!=name:raise ValueError('Unsafe evidence path')
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Evidence hash mismatch: '+name)
    evidence_hash=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    with ledger_path.open(newline='') as f:
        reader=csv.DictReader(f)
        required={'record_id','evidence_sha256','meeting','race','number','pre_off_proven','results_status'}
        if not required.issubset(reader.fieldnames or []):raise ValueError('Incomplete ledger columns')
        rows=list(reader)
    if not rows:raise ValueError('Empty ledger')
    seen=set()
    for row in rows:
        key=tuple(row[k].strip() for k in ('meeting','race','number'))
        if not all(key) or key in seen:raise ValueError('Duplicate or incomplete runner identity')
        seen.add(key)
        rid=hashlib.sha256((evidence_hash+'|'+'|'.join(key)).encode()).hexdigest()
        if row['record_id']!=rid or row['evidence_sha256']!=evidence_hash:
            raise ValueError('Ledger not linked to manifest')
        if row['pre_off_proven']!='false' or row['results_status']!='NOT_RECONCILED':
            raise ValueError('Unverified pre-off or reconciliation claim')
    return {'verified_rows':len(rows),'hashes_checked':len(hashes),
            'pre_off_proven':False,'durably_immutable':False,'betting_status':'NO BET'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('ledger');p.add_argument('--base-dir')
    a=p.parse_args();print(json.dumps(verify(a.manifest,a.ledger,a.base_dir)))
