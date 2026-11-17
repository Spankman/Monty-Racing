"""Orchestration only: ingest, transform, fit, then report."""
import json,sys
import numpy as np,pandas as pd
from .config import HERE,OUT,dump
from .ingestion import join_sources,add_overlays
from .features import build_features
from .fitting import fit_candidates
from .evaluation import evaluate_diagnostic

def run():
    registry=json.loads((HERE/'experiment_registry.json').read_text());dump('experiment_registry.json',registry)
    d=add_overlays(join_sources());print('Joined',int(d.enriched_eligible.sum()),'rows',flush=True)
    d,X,names=build_features(d);print('Features',X.shape,flush=True)
    np.savez_compressed(OUT/'frozen_feature_matrix.npz',X=X,names=np.array(names))
    fit=fit_candidates(d,X,names,registry)
    result=evaluate_diagnostic(d,fit)
    feature=pd.DataFrame(X,columns=names)
    feature.insert(0,'runner',d.SELECTION_NAME);feature.insert(0,'market_id',d.WIN_MARKET_ID);feature.insert(0,'date',d.date);feature['outcome_y']=d.y.to_numpy()
    feature.to_csv(OUT/'development_features.csv.gz',index=False)
    d.to_csv(OUT/'joined_development_runners.csv.gz',index=False)
    dump('environment.json',dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__))
    print(json.dumps(result,indent=2),flush=True)
