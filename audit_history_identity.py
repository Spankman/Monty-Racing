"""Report historical identity candidates without making a name-only model join."""
import argparse
import json
from pathlib import Path
import pandas as pd
from race_day import ROOT
from monty.normalization import normal


def audit(bundle,history):
    required={'SELECTION_ID','SELECTION_NAME'}
    if not required.issubset(history):raise ValueError('Historical identity columns missing')
    d=history.copy();d['_name']=d.SELECTION_NAME.map(normal)
    rows=[]
    for r in bundle['snapshot']['runners']:
        matched=d[d['_name'].eq(normal(r['horse']))]
        ids=sorted(set(matched.SELECTION_ID.dropna().astype(str)))
        rows.append(dict(number=r['number'],candidate_count=len(ids),
            status='absent' if not ids else 'ambiguous' if len(ids)>1 else 'candidate_requires_cross_source_verification',
            identity_verified=False))
    return dict(runners=rows,verified_joins=0,predictions_generated=False,
                note='Exact normalized name matches are candidates only, never authorization to combine different horse IDs.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bundle');p.add_argument('history');p.add_argument('--output',required=True)
    a=p.parse_args();b=json.loads(Path(a.bundle).read_text())
    report=audit(b,pd.read_csv(a.history,dtype={'SELECTION_ID':str}))
    Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
