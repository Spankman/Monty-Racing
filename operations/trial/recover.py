"""Verify an exported trial artifact and decrypt it into a private directory.

Download via the supported GitHub artifact connector first. No API secrets used.
Never use a repository or public output directory for licensed raw data.
"""
import argparse,hashlib,io,json,os,stat,subprocess,zipfile
from pathlib import Path

def safe_zip(raw,maximum=100_000_000):
    archive=zipfile.ZipFile(io.BytesIO(raw))
    if sum(x.file_size for x in archive.infolist())>maximum:raise ValueError('Archive expansion limit')
    for item in archive.infolist():
        p=Path(item.filename)
        if p.is_absolute() or '..' in p.parts or stat.S_ISLNK(item.external_attr>>16):raise ValueError('Unsafe archive member')
    if archive.testzip() is not None:raise ValueError('Archive CRC mismatch')
    return archive

def recover(archive_path,expected,key,output):
    blob=Path(archive_path).read_bytes()
    if hashlib.sha256(blob).hexdigest()!=expected:raise ValueError('GitHub artifact digest mismatch')
    output=Path(output).resolve()
    repo=Path(__file__).resolve().parents[2]
    if output==repo or repo in output.parents:raise ValueError('Licensed evidence must remain outside repository')
    if output.exists():raise FileExistsError('Private recovery destination must be new')
    archive=safe_zip(blob);receipts=[x for x in archive.namelist() if x.endswith('receipt.json')]
    if len(receipts)!=1:raise ValueError('Exactly one checkpoint receipt expected')
    name=receipts[0];prefix=str(Path(name).parent);prefix='' if prefix=='.' else prefix+'/'
    raw=archive.read(name);receipt=json.loads(raw);expected_receipt=archive.read(prefix+'receipt.sha256').decode().split()[0]
    if hashlib.sha256(raw).hexdigest()!=expected_receipt:raise ValueError('Receipt digest mismatch')
    sealed=archive.read(prefix+'private-evidence.cms')
    if hashlib.sha256(sealed).hexdigest()!=receipt['encrypted_evidence_sha256']:raise ValueError('Encrypted evidence digest mismatch')
    # Pass ciphertext on stdin; key is a local path, never printed or embedded.
    opened=subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-inkey',str(key)],input=sealed,capture_output=True)
    if opened.returncode:raise ValueError('Authenticated decryption failed')
    private=safe_zip(opened.stdout)
    output.mkdir(mode=0o700,parents=True)
    for item in private.infolist():
        if item.is_dir():continue
        target=output/item.filename;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with target.open('xb') as file:file.write(private.read(item))
        target.chmod(0o600)
    return dict(receipt_sha256=expected_receipt,verified_private_files=len(private.infolist()),raw_data_published=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('artifact');p.add_argument('--sha256',required=True);p.add_argument('--key',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(recover(a.artifact,a.sha256,a.key,a.output)))
if __name__=='__main__':main()
