"""Fail-closed daily research summary; NEVER generates betting recommendations."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

def assess(scores,model_audit,source_audit):
    df=pd.read_csv(scores)
    model=json.loads(Path(model_audit).read_text())
    source=json.loads(Path(source_audit).read_text())
    if len(df)!=model['runners'] or len(df)!=source['runners_accepted']:
        raise ValueError('Runner-count mismatch')
    if df.groupby(['meeting','race']).ngroups!=model['races'] or model['races']!=source['races_accepted']:
        raise ValueError('Race-count mismatch')
    if df.empty or not np.isfinite(df[['odds','market_prob','research_prob','edge','feature_coverage']].to_numpy(float)).all():
        raise ValueError('Empty or invalid scores')
    if not (df.status=='UNAPPROVED RESEARCH — NO BET').all():
        raise ValueError('Unexpected status')
    if not df.groupby(['meeting','race']).research_prob.sum().between(0.999999,1.000001).all():
        raise ValueError('Research probabilities not normalized by race')
    return {
        'date':model['date'],'meetings':int(df.meeting.nunique()),'races':int(model['races']),
        'runners':int(len(df)),'feature_coverage_mean':round(float(df.feature_coverage.mean()),4),
        'feature_coverage_min':round(float(df.feature_coverage.min()),4),
        'positive_edge_runners':int((df.edge>0).sum()),
        'full_original_artifact_integrity_verified':False,
        'independent_TAB_verified':False,'complete_AU_NZ_coverage_verified':False,
        'approved_bets':0,'status':'NO BET — RESEARCH ONLY',
        'reason':'Incomplete historical features and independent market/field validation'
    }
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('scores');p.add_argument('model_audit');p.add_argument('source_audit')
    p.add_argument('--output',default='daily_summary.json')
    a=p.parse_args()
    result=assess(a.scores,a.model_audit,a.source_audit)
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
