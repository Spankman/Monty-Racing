"""Research-only evidence manifest. Metadata does NOT prove pre-off capture or immutability."""
import argparse, datetime, hashlib, json, os, subprocess
from pathlib import Path

def build(snapshot, scores, audit, output, now=None, commit=None, run_id=None):
    files=[Path(snapshot),Path(scores),Path(audit)]
    for path in files:
        if not path.is_file():raise FileNotFoundError(path)
    stamp=now or datetime.datetime.now(datetime.timezone.utc)
    if stamp.tzinfo is None:raise ValueError('UTC-aware capture time required')
    revision=commit or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if not revision or len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision.lower()):
        raise ValueError('Full git commit SHA required')
    snap=json.loads(files[0].read_text())
    if not isinstance(snap.get('races'),list) or not snap['races']:raise ValueError('Missing race list')
    evidence={
        'schema':'monty-research-evidence-v1',
        'created_at_utc':stamp.astimezone(datetime.timezone.utc).isoformat(),
        'git_commit_sha':revision,
        'workflow_run_id':str(run_id or os.environ.get('GITHUB_RUN_ID') or 'LOCAL'),
        'snapshot_date':snap.get('date'),
        'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'race_off_time_verified':False,
        'quote_capture_time_verified':False,
        'pre_off_proven':False,
        'durably_immutable':False,
        'status':'UNAPPROVED RESEARCH — NO BET',
        'warning':'Manifest is an ephemeral artifact, not write-once storage. No provider off-times or per-quote timestamps verified.'
    }
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    return evidence

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('snapshot');p.add_argument('scores');p.add_argument('audit')
    p.add_argument('--output',default='research_evidence_manifest.json')
    a=p.parse_args()
    print(json.dumps(build(a.snapshot,a.scores,a.audit,a.output)))
