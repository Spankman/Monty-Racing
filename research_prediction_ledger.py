"""Research-only append-only ledger. No betting settlement or pre-off claims.

This module refuses to rewrite an existing prediction. A persistent write-once
store is still required; local filesystem append alone is NOT immutable.
"""
import argparse, csv, hashlib, json, os
from pathlib import Path

FIELDS=['record_id','evidence_sha256','meeting','race','number','horse','odds','market_prob','research_prob','status','pre_off_proven','results_status']

def stage(scores_path,manifest_path,ledger_path):
    scores_path=Path(scores_path);manifest_path=Path(manifest_path);ledger_path=Path(ledger_path)
    manifest_bytes=manifest_path.read_bytes()
    manifest=json.loads(manifest_bytes)
    if manifest.get('schema')!='monty-research-evidence-v1':raise ValueError('Unknown evidence schema')
    expected=manifest.get('files_sha256',{}).get(scores_path.name)
    if expected!=hashlib.sha256(scores_path.read_bytes()).hexdigest():raise ValueError('Score hash mismatch')
    if manifest.get('pre_off_proven') is not False:raise ValueError('Unapproved pre-off evidence state')
    evidence_hash=hashlib.sha256(manifest_bytes).hexdigest()
    with scores_path.open(newline='') as f:
        reader=csv.DictReader(f)
        required={'meeting','race','number','horse','odds','market_prob','research_prob','status'}
        if not required.issubset(reader.fieldnames or []):raise ValueError('Missing scoring columns')
        source=list(reader)
    if not source:raise ValueError('Empty scoring file')
    seen=set();rows=[]
    for row in source:
        key=tuple(row[k].strip() for k in ('meeting','race','number'))
        if any(not v for v in key) or key in seen:raise ValueError('Invalid or duplicate runner identity')
        seen.add(key)
        if row['status']!='UNAPPROVED RESEARCH — NO BET':raise ValueError('Only research-only rows accepted')
        rid=hashlib.sha256((evidence_hash+'|'+ '|'.join(key)).encode()).hexdigest()
        rows.append({**{k:row[k] for k in ('meeting','race','number','horse','odds','market_prob','research_prob','status')},
            'record_id':rid,'evidence_sha256':evidence_hash,'pre_off_proven':'false','results_status':'NOT_RECONCILED'})
    ledger_path.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation avoids overwriting previous research records. It does
    # not replace write-once remote storage or authenticated timestamps.
    with ledger_path.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader();writer.writerows(rows)
    return {'records':len(rows),'path':str(ledger_path),'pre_off_proven':False,'betting_status':'NO BET'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('scores');p.add_argument('manifest');p.add_argument('--output',default='research_prediction_ledger.csv')
    a=p.parse_args();print(json.dumps(stage(a.scores,a.manifest,a.output)))
