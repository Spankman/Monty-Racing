"""Monty V7 experimental expert blend. Shadow-only; no betting approval.

Expert file columns: meeting,race,number,expert_score,source,captured_at,race_off_at.
Scores are nonnegative and are normalized within each race. Missing or stale
expert input leaves model probabilities unchanged. No inferred expert picks.
"""
import argparse, json, re
from pathlib import Path
import numpy as np
import pandas as pd

KEY=['meeting','race','number']
def blend(scores, experts=None, weight=0.10, min_coverage=0.60):
    if not 0 <= weight <= 0.20: raise ValueError('Expert weight outside research guardrail')
    df=pd.read_csv(scores,dtype={k:str for k in KEY})
    if df.empty or df.duplicated(KEY).any(): raise ValueError('Invalid scoring identities')
    if not np.isfinite(df['research_prob'].to_numpy(float)).all(): raise ValueError('Invalid model scores')
    df['v7_shadow_prob']=df['research_prob'].astype(float)
    df['expert_weight_used']=0.0
    df['expert_sources']=''
    df['v7_status']='UNAPPROVED V7 SHADOW — NO BET'
    if experts is None: return df
    e=pd.read_csv(experts,dtype={k:str for k in KEY})
    required=set(KEY+['expert_score','source','captured_at','race_off_at'])
    if not required.issubset(e.columns): raise ValueError('Expert input missing required provenance')
    if e.empty: return df
    e['expert_score']=pd.to_numeric(e['expert_score'],errors='raise')
    if not np.isfinite(e.expert_score).all() or (e.expert_score<0).any(): raise ValueError('Invalid expert score')
    if e[KEY+['source','captured_at','race_off_at']].isna().any().any() or e.duplicated(KEY+['source']).any():
        raise ValueError('Expert provenance or duplicate error')
    # Reject undated, timezone-naive, post-off or conflicting race-off evidence.
    tz_pattern=re.compile(r'(?:Z|[+-][0-9]{2}:[0-9]{2})$')
    if not e['captured_at'].map(lambda v: bool(tz_pattern.search(str(v)))).all() or not e['race_off_at'].map(lambda v: bool(tz_pattern.search(str(v)))).all():
        raise ValueError('Expert timestamps require explicit UTC offset')
    captured=pd.to_datetime(e['captured_at'],utc=True,errors='coerce')
    off=pd.to_datetime(e['race_off_at'],utc=True,errors='coerce')
    if captured.isna().any() or off.isna().any() or (captured>=off).any():
        raise ValueError('Expert tips must have valid pre-race capture and off timestamps')
    if e.groupby(['meeting','race']).race_off_at.nunique().gt(1).any():
        raise ValueError('Conflicting race off times')
    # Each source contributes equally regardless of how many horses it selects.
    for (meeting,race),ix in df.groupby(['meeting','race'],sort=False).groups.items():
        sub=df.loc[ix]
        ex=e[(e.meeting==meeting)&(e.race==race)]
        if ex.empty:continue
        if not set(map(tuple,ex[KEY].to_numpy())).issubset(set(map(tuple,sub[KEY].to_numpy()))):
            raise ValueError('Expert horse not in verified model field')
        source_vectors=[]
        for source,g in ex.groupby('source'):
            total=g.expert_score.sum()
            if total<=0:continue
            vals=g.groupby('number').expert_score.sum()/total
            vec=sub.number.map(vals).fillna(0).to_numpy(float)
            source_vectors.append(vec)
        if not source_vectors:continue
        if float(sub.feature_coverage.mean())<min_coverage:continue
        model=sub.research_prob.to_numpy(float)
        if not np.isclose(model.sum(),1,atol=1e-6):raise ValueError('Model probabilities do not sum to one')
        expert=np.mean(source_vectors,axis=0)
        expert=expert/expert.sum()
        blended=(1-weight)*model+weight*expert
        df.loc[ix,'v7_shadow_prob']=blended
        df.loc[ix,'expert_weight_used']=weight
        df.loc[ix,'expert_sources']=';'.join(sorted(ex.source.unique()))
    return df

def main():
    p=argparse.ArgumentParser()
    p.add_argument('scores');p.add_argument('--experts');p.add_argument('--output',default='v7_shadow.csv')
    p.add_argument('--weight',type=float,default=.10);p.add_argument('--min-coverage',type=float,default=.60)
    a=p.parse_args()
    df=blend(a.scores,a.experts,a.weight,a.min_coverage)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(a.output,index=False)
    print(json.dumps({'races':int(df.groupby(['meeting','race']).ngroups),'races_with_experts':int(df.loc[df.expert_weight_used>0].groupby(['meeting','race']).ngroups),'betting_status':'NO BET — UNAPPROVED V7 SHADOW'}))
if __name__=='__main__':main()
)
    if not e['captured_at'].map(lambda v:bool(tz_pattern.search(str(v)))).all() or not e['race_off_at'].map(lambda v:bool(tz_pattern.search(str(v)))).all():
        raise ValueError('Expert timestamps require explicit UTC offset')
    captured=pd.to_datetime(e['captured_at'],utc=True,errors='coerce')
    off=pd.to_datetime(e['race_off_at'],utc=True,errors='coerce')
    if captured.isna().any() or off.isna().any() or (captured>=off).any():
        raise ValueError('Expert tips must have valid pre-race capture and off timestamps')
    if e.groupby(['meeting','race']).race_off_at.nunique().gt(1).any():
        raise ValueError('Conflicting race off times')
    # Each source contributes equally regardless of how many horses it selects.
    for (meeting,race),ix in df.groupby(['meeting','race'],sort=False).groups.items():
        sub=df.loc[ix]
        ex=e[(e.meeting==meeting)&(e.race==race)]
        if ex.empty:continue
        if not set(map(tuple,ex[KEY].to_numpy())).issubset(set(map(tuple,sub[KEY].to_numpy()))):
            raise ValueError('Expert horse not in verified model field')
        source_vectors=[]
        for source,g in ex.groupby('source'):
            total=g.expert_score.sum()
            if total<=0:continue
            vals=g.groupby('number').expert_score.sum()/total
            vec=sub.number.map(vals).fillna(0).to_numpy(float)
            source_vectors.append(vec)
        if not source_vectors:continue
        if float(sub.feature_coverage.mean())<min_coverage:continue
        model=sub.research_prob.to_numpy(float)
        if not np.isclose(model.sum(),1,atol=1e-6):raise ValueError('Model probabilities do not sum to one')
        expert=np.mean(source_vectors,axis=0)
        expert=expert/expert.sum()
        blended=(1-weight)*model+weight*expert
        df.loc[ix,'v7_shadow_prob']=blended
        df.loc[ix,'expert_weight_used']=weight
        df.loc[ix,'expert_sources']=';'.join(sorted(ex.source.unique()))
    return df

def main():
    p=argparse.ArgumentParser()
    p.add_argument('scores');p.add_argument('--experts');p.add_argument('--output',default='v7_shadow.csv')
    p.add_argument('--weight',type=float,default=.10);p.add_argument('--min-coverage',type=float,default=.60)
    a=p.parse_args()
    df=blend(a.scores,a.experts,a.weight,a.min_coverage)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(a.output,index=False)
    print(json.dumps({'races':int(df.groupby(['meeting','race']).ngroups),'races_with_experts':int(df.loc[df.expert_weight_used>0].groupby(['meeting','race']).ngroups),'betting_status':'NO BET — UNAPPROVED V7 SHADOW'}))
if __name__=='__main__':main()
