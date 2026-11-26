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
    supplied_values=X.copy()
    for name,values in [('log_market_probability',np.log(base)),('log_field_size',np.full(len(d),np.log(len(d))))]:
        if name in names:X[:,names.index(name)]=values
    finite=np.isfinite(X);filled=np.where(finite,X,np.array(medians));ix=[names.index(n) for n in active]
    Z=np.column_stack([filled[:,ix],(~finite[:,ix]).astype(float)])
    Z=(Z-np.array(m['mean']))/np.array(m['scale'])
    all_terms=Z.copy()
    term_names=m['numeric_feature_names'] if version=='V6' else active+[n+'_missing' for n in active]
    term_weights=np.zeros(len(term_names))
    selected_terms=[i for i,n in enumerate(term_names) if version!='V6' or n!='log_market_probability']
    term_weights[selected_terms]=weights
    if version=='V6':Z=Z[:,selected_terms]
    correction=Z@weights
    logits=(np.log(base)+correction)/temperature
    expected=np.exp(logits-logits.max());expected/=expected.sum()
    observed=dict(zip(scored['number' if version=='V6' else 'runner_id'],scored['monty_prob' if version=='V6' else 'v7_win_probability']))
    if not np.allclose(expected,[observed[n] for n in d.number],rtol=0,atol=1e-12):
        raise OutputContractError('model_component_reconciliation_failed')
    # Private numerical audit only. Do not put individual inputs/contributions
    # in public score_trace or infer an independently trained form-only model.
    from operations.evidence.store import write,encoded,sha
    import io
    values=all_terms*term_weights
    centered=values-values.mean(axis=0)
    pure_market=np.exp(np.log(base)/temperature-np.max(np.log(base)/temperature));pure_market/=pure_market.sum()
    uncal=np.exp(np.log(base)+correction-np.max(np.log(base)+correction));uncal/=uncal.sum()
    raw_only=np.exp(correction-correction.max());raw_only/=raw_only.sum()
    packet=io.BytesIO()
    np.savez_compressed(packet,feature_names=np.array(names),term_names=np.array(term_names),numbers=d.number.to_numpy(str),
        supplied_column_values=supplied_values,original_values=X,observed=finite,imputed_values=filled,missing_indicators=~finite,
        transformed_terms=all_terms,term_weights=term_weights,term_contributions=values,
        within_race_centered_contributions=centered,fully_cancelled_terms=np.ptp(values,axis=0)<=1e-12,
        market_probability=base,feature_correction=correction,temperature=np.array(temperature),
        selected_decimal_odds=d.odds.to_numpy(float),model_probability_uplift=expected-base,
        gross_point_expected_value=expected*d.odds.to_numpy(float)-1,
        model_edge_contribution=(expected-base)*d.odds.to_numpy(float),market_normalisation_edge=np.array(1/(1/d.odds.to_numpy(float)).sum()-1),
        calibrated_term_contributions=values/temperature,market_log_scores=np.log(base),calibrated_market_log_scores=np.log(base)/temperature,
        uncalibrated_logits=np.log(base)+correction,calibrated_logits=logits,
        model_probability=expected,reported_probability=np.array([observed[n] for n in d.number]),
        market_temperature_only_probability=pure_market,uncalibrated_model_probability=uncal,
        conditional_feature_probability_effect=expected-pure_market,market_temperature_probability_effect=pure_market-base,
        full_model_calibration_probability_effect=expected-uncal,
        correction_only_counterfactual_not_independent_form=raw_only)
    write(directory/'feature-audit.npz',packet.getvalue())
    model_path=Path(v6_root)/'results/frozen_model.json' if version=='V6' else Path(v7_root)/'v7/artifacts/fold_3_model.json'
    write(directory/'frozen-model.json',model_path.read_bytes())
    write(directory/'feature-audit.json',encoded(dict(schema='monty.feature-audit.v1',model=version,
        model_sha256=sha(model_path.read_bytes()),rows=len(d),features=len(names),terms=len(term_names),
        temperature=temperature,expert_weight=0.0,model_vs_expert_weight=1.0,
        adaptive_weighting=False,market_logit_coefficient=1/temperature,correction_logit_coefficient=1/temperature,
        feature_audit_sha256=sha(packet.getvalue()),source_input_sha256=sha((directory/('validated_runners.csv' if version=='V6' else 'provisional_input.csv')).read_bytes()),
        maximum_reconstruction_error=float(np.max(np.abs(expected-np.array([observed[n] for n in d.number])))),
        independent_form_model=False,correction_only_warning='Counterfactual score component of a model trained conditional on market, not independent form-only predictions',
        interpretation='Linear logit contributions; within-race constants cancel. Not causal feature effects or probability-additive attribution')))
    return {number:dict(market_probability=float(base[i]),market_log_score=float(np.log(base[i])),
                feature_log_correction=float(correction[i]),temperature=float(temperature),
                reconstructed_probability=float(expected[i]),reported_probability=float(observed[number]),
                absolute_difference=float(abs(expected[i]-observed[number])),
                observed_feature_count=int(finite[i].sum()),total_features=len(names),
                expert_weight_used=0.0)
            for i,number in enumerate(d.number)}
