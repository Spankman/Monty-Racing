#!/usr/bin/env python3
"""Monty V6 race-day scoring; no fabricated inputs. CSV fields: meeting,race,number,horse,odds, optional exact V6 feature names."""
import argparse,json,sys
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent/'monty_v6'
sys.path.insert(0,str(ROOT))
from monty.scoring import score_features
from monty.integrity import verify_artifacts

def run(src,dst):
    model=json.loads((ROOT/'results/frozen_model.json').read_text())
    names=model['input_feature_names']
    df=pd.read_csv(src,dtype={'meeting':str,'race':str,'number':str,'horse':str})
    req=['meeting','race','number','horse','odds']
    missing=[x for x in req if x not in df]
    if missing:raise ValueError('Missing columns: '+','.join(missing))
    if df.empty:raise ValueError('No runners supplied')
    if df[req].isna().any().any():raise ValueError('Missing runner identity or odds')
    df['odds']=pd.to_numeric(df['odds'],errors='raise')
    if (~np.isfinite(df.odds)).any() or (df.odds<=1).any():raise ValueError('Odds must be finite decimal odds > 1')
    df['race_id']=df.meeting.str.strip().str.upper()+'|'+df.race.str.strip()
    if df.duplicated(['race_id','number']).any():raise ValueError('Duplicate saddlecloth within race')
    if 'scratched' in df:
        df=df[~df.scratched.astype(str).str.lower().isin(['true','1','yes'])].copy()
    if df.empty:raise ValueError('No active runners')
    # Do not score partial fields: odds normalization requires all active runners.
    # User explicitly confirms full fields via --complete-fields.
    p=1/df.odds.to_numpy(float)
    ids=df.race_id.to_numpy()
    totals=pd.Series(p).groupby(ids).transform('sum').to_numpy()
    base=p/totals
    X=np.full((len(df),len(names)),np.nan)
    for j,name in enumerate(names):
        if name in df:
            X[:,j]=pd.to_numeric(df[name],errors='coerce').to_numpy(float)
    if 'log_field_size' in names:
        X[:,names.index('log_field_size')]=np.log(df.groupby('race_id')['horse'].transform('size').to_numpy(float))
    # Current market probability feature is observable from provided odds, not an imputed historical value.
    for candidate in ['log_market_probability','market_probability']:
        if candidate in names:
            X[:,names.index(candidate)]=np.log(base) if candidate.startswith('log_') else base
    pred=score_features(X,names,base,ids,root=ROOT)
    df['market_prob']=base;df['monty_prob']=pred
    df['fair_odds']=1/pred;df['edge']=df.odds*pred-1
    df['feature_coverage']=np.isfinite(X).sum(axis=1)/len(names)
    df['category']=np.where((df.odds>=6)&(df.edge>0),'RUFFY',np.where(df.edge>0,'BEST BET','NO BET'))
    df=df.sort_values(['category','edge'],ascending=[True,False])
    cols=['meeting','race','number','horse','odds','market_prob','monty_prob','fair_odds','edge','feature_coverage','category']
    df[cols].to_csv(dst,index=False)
    return df[cols]

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('input');ap.add_argument('--output',default='monty_selections.csv');ap.add_argument('--complete-fields',action='store_true',required=True,help='Confirm all non-scratched runners and odds are present for every included race')
    a=ap.parse_args();print(run(a.input,a.output).to_string(index=False))
