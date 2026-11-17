"""Explicit release preparation; never called automatically by scoring or CI."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXCLUDED={'artifact_hashes.json','tests.log','verification.log'}
def refresh():
    entries={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in EXCLUDED and '.egg-info' not in str(p)}
    (ROOT/'artifact_hashes.json').write_text(json.dumps(entries,indent=2))
    print('Recorded',len(entries),'release hashes; run verification and tests before delivery.')
if __name__=='__main__':refresh()
