"""Partial-artifact V6 linear recovery, strictly research-only.

Verifies the exact frozen model SHA256 against the unchanged V6 manifest.
Never claims full V6 artifact integrity or authorises betting.
Historical/current inputs still pass the canonical history_bridge checks.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from history_bridge import build

ROOT=Path(__file__).resolve().parent/'monty_v6'
sys.path.insert(0,str(ROOT))
from monty.integrity import ArtifactError, validate_model_contract
from monty.model_math import probabilities

def load_verified_linear(root=ROOT):
    root=Path(root)
    manifest=json.loads((root/'artifact_hashes.json').read_text())
    name='results/frozen_model.json'
    raw=(root/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest[name]:
        raise ArtifactError('Frozen V6 model hash mismatch')
    model=json.loads(raw)
    validate_model_contract(model,model['input_feature_names'])
    if model['models'][model['selected']]['kind']!='linear':
        raise ArtifactError('Partial recovery supports only the frozen linear model')
    return model

def score_recovery(X,names,market,ids,root=ROOT):
    model=load_verified_linear(root)
    names=list(names)
    active=validate_model_contract(model,names)
    X=np.asarray(X,dtype=float)
    base=np.asarray(market,dtype=float)
    ids=np.asarray(ids)
    if X.ndim!=2 or X.shape!=(len(base),len(names)) or not len(base) or pd.isna(ids).any():
        raise ArtifactError('Invalid input shape or race identity')
    g=pd.factorize(ids)[0]
    if not np.isfinite(base).all() or (base<=0).any():
        raise ArtifactError('Invalid market probabilities')
    if not np.allclose(np.bincount(g,weights=base),1,atol=1e-9,rtol=0):
        raise ArtifactError('Market probabilities must sum to one per race')
    finite=np.isfinite(X)
    imputed=np.where(finite,X,np.asarray(model['imputation_medians']))
    indices=[names.index(n) for n in active]
    Z=np.column_stack([imputed[:,indices],(~finite[:,indices]).astype(float)])
    Z=(Z-np.asarray(model['mean']))/np.asarray(model['scale'])
    formidx=[i for i,n in enumerate(model['numeric_feature_names']) if n!='log_market_probability']
    weights=np.asarray(model['models'][model['selected']]['weights'])
    p=probabilities(np.log(base)+Z[:,formidx]@weights,g)
    if not np.isfinite(p).all() or not np.allclose(np.bincount(g,weights=p),1,atol=1e-9):
        raise ArtifactError('Invalid recovered probabilities')
    return p

def run(history,current,day,root=ROOT):
    rows,X,names=build(history,current,day)
    if rows.empty:raise ValueError('No current runners')
    base=rows.market_probability.to_numpy(float)
    pred=score_recovery(X,names,base,rows.WIN_MARKET_ID.to_numpy(),root)
    out=rows[['date','WIN_MARKET_ID','SELECTION_ID','SELECTION_NAME','TRACK']].copy()
    out['market_probability']=base
    out['recovered_v6_probability']=pred
    out['feature_coverage']=np.isfinite(X).mean(axis=1)
    out['betting_authorised']=False
    out['status']='RECOVERED_V6_LINEAR_RESEARCH_ONLY_NO_BET'
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('history');p.add_argument('current');p.add_argument('--date',required=True)
    p.add_argument('--output-dir',default='race_day_output/recovered_v6')
    a=p.parse_args()
    h=pd.read_csv(a.history,dtype={'SELECTION_ID':str,'WIN_MARKET_ID':str})
    c=pd.read_csv(a.current,dtype={'SELECTION_ID':str,'WIN_MARKET_ID':str})
    result=run(h,c,a.date)
    output=Path(a.output_dir);output.mkdir(parents=True,exist_ok=True)
    result.to_csv(output/'research_predictions.csv',index=False)
    audit={'date':a.date,'runners':len(result),'verified_frozen_model_hash':True,
           'full_55_artifact_integrity':False,'independent_live_data_verification':False,
           'betting_authorised':False,'status':'RESEARCH_ONLY_NO_BET'}
    (output/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit))
