"""Reconcile linear scoring components against actual engine output, no fitting.

Reads the exact staged engine CSVs. These diagnostics never replace a model's
predictions, mutate its inputs, or load a research pickle.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from operations.assessment import OutputContractError


def trace(version, directory, v7_root, v6_root):
    directory=Path(directory)
    if version == 'V6':
        m=json.loads((Path(v6_root)/'results/frozen_model.json').read_text())
        if m['models'][m['selected']]['kind'] != 'linear':
            raise OutputContractError('unexpected_frozen_model_kind')
        d=pd.read_csv(directory/'validated_runners.csv',dtype={'number':str})
        scored=pd.read_csv(directory/'monty_selections.csv',dtype={'number':str})
        names=m['input_feature_names']; active=m['numeric_feature_names'][:len(m['numeric_feature_names'])//2]
        medians=m['imputation_medians']; weights=np.array(m['models'][m['selected']]['weights'])
        temperature=1.0
    else:
        m=json.loads((Path(v7_root)/'v7/artifacts/fold_3_model.json').read_text())
        d=pd.read_csv(directory/'provisional_input.csv',dtype={'number':str})
        scored=pd.read_csv(directory/'v7_research_scores.csv',dtype={'runner_id':str})
        names=m['names']; active=[n for n,a in zip(names,m['active']) if a]
        medians=m['medians']; weights=np.array(m['weights']);temperature=m['temperature']
    base=1/d['odds'].to_numpy(float);base=base/base.sum()
    X=np.column_stack([pd.to_numeric(d[n],errors='coerce').to_numpy(float) if n in d else np.full(len(d),np.nan) for n in names])
    for name,values in [('log_market_probability',np.log(base)),('log_field_size',np.full(len(d),np.log(len(d))))]:
        if name in names:X[:,names.index(name)]=values
    finite=np.isfinite(X);filled=np.where(finite,X,np.array(medians));ix=[names.index(n) for n in active]
    Z=np.column_stack([filled[:,ix],(~finite[:,ix]).astype(float)])
    Z=(Z-np.array(m['mean']))/np.array(m['scale'])
    if version=='V6':Z=Z[:,[i for i,n in enumerate(m['numeric_feature_names']) if n!='log_market_probability']]
    correction=Z@weights
    logits=(np.log(base)+correction)/temperature
    expected=np.exp(logits-logits.max());expected/=expected.sum()
    observed=dict(zip(scored['number' if version=='V6' else 'runner_id'],scored['monty_prob' if version=='V6' else 'v7_win_probability']))
    if not np.allclose(expected,[observed[n] for n in d.number],rtol=0,atol=1e-12):
        raise OutputContractError('model_component_reconciliation_failed')
    return {number:dict(market_probability=float(base[i]),market_log_score=float(np.log(base[i])),
                feature_log_correction=float(correction[i]),temperature=float(temperature),
                reconstructed_probability=float(expected[i]),reported_probability=float(observed[number]),
                absolute_difference=float(abs(expected[i]-observed[number])),
                observed_feature_count=int(finite[i].sum()),total_features=len(names),
                expert_weight_used=0.0)
            for i,number in enumerate(d.number)}
