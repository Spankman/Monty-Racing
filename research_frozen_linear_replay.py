"""Isolated, unapproved research replay of frozen linear coefficients.

Does NOT claim the original 55-artifact V6 integrity check passed.
Does NOT produce betting recommendations.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'monty_v6'))
from monty.integrity import validate_model_contract
from monty.model_math import probabilities

def run(snapshot_path, output):
    root=ROOT/'monty_v6'
    manifest=json.loads((root/'artifact_hashes.json').read_text())
    name='results/frozen_model.json'
    raw=(root/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest[name]:
        raise ValueError('Frozen model hash mismatch')
    model=json.loads(raw)
    if model['models'][model['selected']]['kind']!='linear':
        raise ValueError('Only verified JSON linear research replay supported')
    names=model['input_feature_names']
    active=validate_model_contract(model,names)
    snapshot=json.loads(Path(snapshot_path).read_text())
    rows=snapshot['runners']
    df=pd.DataFrame(rows)
    if df.empty: raise ValueError('No runners')
    required=['meeting','race','number','horse','odds']
    if df[required].isna().any().any(): raise ValueError('Incomplete identity or odds')
    df['race_id']=df.meeting.astype(str).str.upper()+'|'+df.race.astype(str)
    if df.duplicated(['race_id','number']).any():raise ValueError('Duplicate saddlecloth')
    df['odds']=pd.to_numeric(df.odds,errors='raise')
    if not np.isfinite(df.odds).all() or (df.odds<=1).any():raise ValueError('Invalid odds')
    expected={(str(r['meeting']).upper(),str(r['race'])):int(r['expected_active_runners']) for r in snapshot['races']}
    actual=df.groupby(['meeting','race']).size()
    for (venue,race),count in actual.items():
        if expected.get((str(venue).upper(),str(race)))!=count:raise ValueError('Incomplete field')
    if len(actual)!=len(expected):raise ValueError('Missing races')
    rawprob=1/df.odds.to_numpy(float)
    ids=df.race_id.to_numpy()
    g=pd.factorize(ids)[0]
    base=rawprob/np.bincount(g,weights=rawprob)[g]
    X=np.full((len(df),len(names)),np.nan)
    for j,name in enumerate(names):
        if name in df:X[:,j]=pd.to_numeric(df[name],errors='coerce').to_numpy(float)
    if 'log_field_size' in names:
        X[:,names.index('log_field_size')]=np.log(np.bincount(g)[g])
    if 'log_market_probability' in names:X[:,names.index('log_market_probability')]=np.log(base)
    if 'market_probability' in names:X[:,names.index('market_probability')]=base
    finite=np.isfinite(X)
    Xi=np.where(finite,X,np.asarray(model['imputation_medians']))
    idx=[names.index(n) for n in active]
    Z=np.column_stack([Xi[:,idx],(~finite[:,idx]).astype(float)])
    Z=(Z-np.asarray(model['mean']))/np.asarray(model['scale'])
    sel=model['models'][model['selected']]
    formidx=[i for i,n in enumerate(model['numeric_feature_names']) if n!='log_market_probability']
    pred=probabilities(np.log(base)+Z[:,formidx]@np.asarray(sel['weights']),g)
    if not np.isfinite(pred).all() or not np.allclose(np.bincount(g,weights=pred),1,atol=1e-9):
        raise ValueError('Invalid model probabilities')
    df['market_prob']=base;df['research_prob']=pred
    df['edge']=df.odds*pred-1
    df['feature_coverage']=finite.sum(axis=1)/len(names)
    df['status']='UNAPPROVED RESEARCH — NO BET'
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    df[['meeting','race','number','horse','odds','market_prob','research_prob','edge','feature_coverage','status']].to_csv(output,index=False)
    audit={'date':snapshot['date'],'races':len(actual),'runners':len(df),
        'frozen_model_sha256':manifest['results/frozen_model.json'],
        'full_55_artifact_integrity':'NOT VERIFIED',
        'independent_tab_verification':False,'betting_status':'NO BET — RESEARCH ONLY'}
    output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('snapshot');p.add_argument('--output',default='research_scores.csv')
    a=p.parse_args();run(a.snapshot,a.output)
