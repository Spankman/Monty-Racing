"""Restore original artifacts from a local archive without changing the manifest."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parent/'monty_v6'

def restore(archive, root=ROOT):
    root=Path(root).resolve()
    manifest=json.loads((root/'artifact_hashes.json').read_text())
    planned=[]
    with ZipFile(archive) as z:
        for name,want in manifest.items():
            target=(root/name).resolve()
            if not target.is_relative_to(root):raise ValueError('Unsafe manifest path')
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest()!=want:
                    raise ValueError('Existing artifact differs: '+name)
                continue
            candidates=[i for i in z.infolist() if i.filename.endswith('/monty_v6/'+name) or i.filename=='monty_v6/'+name]
            if len(candidates)!=1:raise ValueError('Expected one original archive entry: '+name)
            info=candidates[0]
            if info.file_size>100_000_000:raise ValueError('Artifact exceeds size limit: '+name)
            content=z.read(info)
            if hashlib.sha256(content).hexdigest()!=want:raise ValueError('Archive hash mismatch: '+name)
            planned.append((target,content))
    # Complete preflight before writing any artifacts. Never regenerate a manifest.
    for target,content in planned:
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    return len(planned)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive');a=p.parse_args()
    print('Restored original artifacts:',restore(a.archive))
