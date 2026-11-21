"""Audit frozen V6 artifact availability without weakening integrity gates."""
import argparse
import hashlib
import json
from pathlib import Path

def audit(root):
    root=Path(root).resolve()
    manifest=json.loads((root/'artifact_hashes.json').read_text())
    missing=[];mismatch=[];verified=[]
    for name,expected in manifest.items():
        target=(root/name).resolve()
        if not target.is_relative_to(root):raise ValueError('Unsafe manifest path')
        if not target.is_file():missing.append(name);continue
        actual=hashlib.sha256(target.read_bytes()).hexdigest()
        (verified if actual==expected else mismatch).append(name)
    return {'expected':len(manifest),'verified':len(verified),
            'missing':missing,'hash_mismatches':mismatch,
            'integrity_complete':not missing and not mismatch,
            'restoration_required':bool(missing or mismatch)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='monty_v6')
    a=p.parse_args()
    result=audit(a.root)
    print(json.dumps(result,indent=2))
    if not result['integrity_complete']:raise SystemExit(2)
