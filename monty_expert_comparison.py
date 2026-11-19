"""Audit genuine expert input against frozen Monty research rankings.

No inferred tips, fabricated timestamps, retrospective bets or performance claims.
"""
import argparse, json
from pathlib import Path
import pandas as pd
from monty_v7_shadow_blend import blend, KEY

def audit(scores, experts):
    scored=pd.read_csv(scores,dtype={k:str for k in KEY})
    # The production blend validates source identity, timing and race matching.
    checked=blend(scores,experts,weight=0.10,min_coverage=0.0)
    e=pd.read_csv(experts,dtype={k:str for k in KEY})
    if e.empty:return {'races_with_experts':0,'source_count':0,'overlap':[]}
    # A positive source score is a source's actual nominated runner, not a
    # manufactured probability estimate.
    e=e[pd.to_numeric(e.expert_score,errors='raise')>0].copy()
    if e.empty:return {'races_with_experts':0,'source_count':0,'overlap':[]}
    scored['model_rank']=scored.groupby(['meeting','race']).research_prob.rank(method='min',ascending=False)
    top=scored[scored.model_rank==1][KEY].drop_duplicates()
    matches=e.merge(top.assign(model_top=True),on=KEY,how='left')
    matches['model_top']=matches.model_top.fillna(False).astype(bool)
    rows=[]
    for (meeting,race),g in matches.groupby(['meeting','race'],sort=True):
        rows.append({'meeting':meeting,'race':race,'sources':sorted(g.source.unique().tolist()),
          'expert_runner_count':int(g.number.nunique()),
          'model_top_overlap':sorted(g.loc[g.model_top,'number'].unique().tolist()),
          'source_tip_count':int(len(g))})
    return {'races_with_experts':len(rows),'source_count':int(e.source.nunique()),
       'source_tips':int(len(e)),'races':rows,
       'note':'Pre-race provenance checked; agreement is not proof of betting edge'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('scores');p.add_argument('experts')
    p.add_argument('--output',default='expert_comparison_audit.json')
    a=p.parse_args()
    report=audit(a.scores,a.experts)
    Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'races_with_experts':report['races_with_experts'],'source_count':report['source_count']}))
if __name__=='__main__':main()
