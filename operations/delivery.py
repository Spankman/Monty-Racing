"""Small, hash-bound forecast previews for GitHub connector inline retrieval."""
import json
from copy import deepcopy
from pathlib import Path

ROW_KEYS={'number','horse','odds','probability','bookmaker','fair_win_odds','numerical_win_edge','bet_type','classification','price_source'}
ROW_KEYS.update({'market_probability','market_only_numerical_edge','model_probability_uplift',
                 'model_edge_contribution','value_attribution','actionable_value','market_warnings'})


def compact(view):
    out=deepcopy(view)
    for race in out['races']:
        model=race['result']
        evidence=model.pop('input_evidence',{})
        if evidence:model['input_summary']={k:evidence.get(k) for k in ('total_features','active_features','fully_observed_active_features','expert_weight_used','model_weight_used')}
        model.pop('ranked_runners',None)
        if model.get('ruffies_to_watch'):
            section=model['ruffies_to_watch']
            section['rows']=[r for r in section['rows'] if r['display_watch']]
            section['full_exclusions_location']='Hash-bound full forecast; compact view retains display watches only'
        for key in ['best_chance','most_likely','value_selection']:
            if isinstance(model.get(key),dict):model[key]={k:v for k,v in model[key].items() if k in ROW_KEYS}
        def trim(container):
            for field in ('ordered_selections','roughies','best_bets'):
                if field in container:container[field]=[{k:v for k,v in row.items() if k in ROW_KEYS} for row in container[field]]
            container.pop('ranked_runners',None)
        trim(model)
        if model.get('diagnostic_assessment'):trim(model['diagnostic_assessment'])
    out['compact_delivery']=True
    return out


def manifest(public,forecast,views):
    from monty_operations import write,sha
    public=Path(public);previews=[]
    for filename,view in views:
        name='compact-'+filename
        value=compact(view)
        write(public/name,value)
        size=(public/name).stat().st_size
        if size>=900_000:raise ValueError('Compact delivery exceeds connector size budget')
        previews.append(dict(path=name,sha256=sha(public/name),bytes=size,version=view['version'],view=view['view']))
    value=dict(schema='monty.delivery.v1',run_id=forecast['run_id'],date=forecast['date'],forecast_sha256=sha(public/'forecast.json'),
        captured_at=forecast.get('captured_at'),valid_until=forecast.get('valid_until'),previews=previews,
        instruction='Verify receipt and preview hashes, then enforce capture expiry and each scheduled jump before displaying selections')
    write(public/'delivery-manifest.json',value)
    return sha(public/'delivery-manifest.json')
