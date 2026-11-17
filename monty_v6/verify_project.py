"""Verify shipped artifacts and replay historical predictions, without fitting."""
import json
import numpy as np,pandas as pd
from monty.config import HERE
from monty.integrity import verify_artifacts
from monty.scoring import score_features

def verify_project():
    count=verify_artifacts()
    with np.load(HERE/'results/frozen_feature_matrix.npz',allow_pickle=False) as z:X,names=z['X'],z['names'].tolist()
    d=pd.read_csv(HERE/'results/joined_development_runners.csv.gz',dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    expected=pd.read_csv(HERE/'results/diagnostic_predictions.csv.gz',dtype={'WIN_MARKET_ID':str})
    p=score_features(X,names,d.market_probability,d.WIN_MARKET_ID)
    mask=d.date.ge('2025-05-01');actual=d.loc[mask,['date','WIN_MARKET_ID','TAB_NUMBER','SELECTION_NAME']].reset_index(drop=True)
    for c in actual:
        if not actual[c].equals(expected[c]):raise AssertionError('Prediction identity/order mismatch: '+c)
    error=float(np.max(np.abs(p[mask]-expected.selected_probability.to_numpy())))
    if error>1e-12:raise AssertionError('Historical prediction replay changed: '+str(error))
    return dict(artifact_hashes=count,replayed_runners=len(expected),replayed_races=expected.WIN_MARKET_ID.nunique(),maximum_probability_difference=error,refitted=False)

if __name__=='__main__':print(json.dumps(verify_project(),indent=2))
