"""Explicit V7 research inference; this is not the V6 operational entry point."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import predict,exotics,value_decision
from .candidate2 import score as score_candidate2
from .evidence import blackbook_matches
from .eligibility import MIN_ACTIVE_RUNNERS, eligibility
from .reconcile import approved_tab_fixture
from monty_v6.monty.normalization import condition, numeric_class


def read_verified_card(path):
    card = json.loads(path.read_bytes())
    fixture_source = card['sources']['fixtures']
    quote_source = card['sources']['fixed_win']
    rows, blackbook = [], []
    for race in card['verified']:
        if not approved_tab_fixture(fixture_source, race['country']):
            raise ValueError('Fixture source is not approved independent TAB for jurisdiction')
        for runner in race['runners'] + race['scratched_runners']:
            if runner['scratched']:
                blackbook.append(dict(runner, race_id=race['race_id'], date=card['date'],
                                      source_url=fixture_source['source_url']))
                continue
            rows.append(dict(
                race_id=race['race_id'], runner_id=runner['runner_id'], horse=runner['horse'],
                number=runner['number'], meeting=race['meeting'], date=card['date'],
                country=race['country'], fixed_win_odds=runner['fixed_win_odds'],
                source_url=fixture_source['source_url'], field_verified=True,
                classification=race['classification'], decision_at=card['decision_at'],
                bookmaker=quote_source['provider'], quote_source_url=quote_source['source_url'],
                quote_captured_at=quote_source['captured_at'], quote_raw_sha256=quote_source['raw_sha256'],
            ))
            # Only these deterministic encodings come from the reconciled race.
            # Form and weight remain missing until independent release evidence exists.
            going = condition(race['going'])
            for name in ('good', 'soft', 'heavy', 'firm', 'synthetic', 'unknown'):
                rows[-1]['going_' + name] = float(name == going)
            rows[-1]['benchmark_class'] = numeric_class(race['classification'])
    return pd.DataFrame(rows), blackbook


def run(model_path,features_path,out,*,allow_restricted=False):
    config=json.loads(model_path.read_text())
    candidate2='candidate1_model' in config
    m=config['candidate1_model'] if candidate2 else config
    reconciled = features_path.suffix == '.json'
    if reconciled:
        d, scratched = read_verified_card(features_path)
    else:
        d = pd.read_csv(features_path, dtype={'race_id':str,'runner_id':str})
        scratched = []
    needed={'race_id','runner_id','horse','date','country','fixed_win_odds','source_url'}
    if not needed.issubset(d):raise ValueError('Missing required field/quote provenance columns')
    if d.empty or d[list(needed)].isna().any().any() or d.duplicated(['race_id','runner_id']).any():raise ValueError('Incomplete or duplicate field records')
    if not d.country.isin(['AU','NZ']).all():raise ValueError('Other jurisdictions need explicit validation')
    if not d.groupby('race_id').date.nunique().eq(1).all() or not d.groupby('race_id').country.nunique().eq(1).all():raise ValueError('Conflicting race metadata')
    classes = d.get('classification', pd.Series('', index=d.index))
    race_reasons = [eligibility(country, label, class_verified=reconciled,
                                allow_restricted=allow_restricted)
                    for country, label in zip(d.country, classes)]
    excluded = d.loc[np.array(race_reasons) == 'restricted race class']
    alerts = blackbook_matches(d.to_dict('records') + scratched)
    d = d.drop(index=excluded.index).reset_index(drop=True)
    if d.empty:
        out.mkdir(parents=True, exist_ok=True)
        (out/'blackbook_next_starts.json').write_text(json.dumps(alerts, indent=2))
        raise ValueError('No eligible race after classification filter')
    if (d.groupby('race_id').size() < MIN_ACTIVE_RUNNERS).any():
        raise ValueError(f'Need at least {MIN_ACTIVE_RUNNERS} active runners')
    if (d.date<=m['calibration_end']).any():raise ValueError('Inference must follow model calibration period')
    odds=pd.to_numeric(d.fixed_win_odds,errors='coerce')
    if not np.isfinite(odds).all() or (odds<=1).any():raise ValueError('Invalid fixed win quote')
    # Require explicit attestation that scratched runners were excluded and field checked.
    if 'field_verified' not in d or not d.field_verified.eq(True).all():raise ValueError('Complete active field verification required')
    inv=1/odds;base=inv/inv.groupby(d.race_id).transform('sum')
    X = np.full((len(d), len(m['names'])), np.nan)
    if reconciled:
        for i, name in enumerate(m['names']):
            if name in d and (name.startswith('going_') or name == 'benchmark_class'):
                X[:, i] = d[name]
    # Current market and field size are deterministic contemporaneous inputs.
    for name,values in [('log_market_probability',np.log(base)),('log_field_size',np.log(d.groupby('race_id').runner_id.transform('size')))]:
        if name in m['names']:X[:,m['names'].index(name)]=values
    d['v7_win_probability']=score_candidate2(config,X,base,d.race_id) if candidate2 else predict(m,X,base,d.race_id)
    d['research_model']='Candidate 2' if candidate2 else 'Candidate 1'
    d['known_feature_count']=np.isfinite(X).sum(1)
    d['within_race_rank']=d.groupby('race_id').v7_win_probability.rank(method='first',ascending=False).astype(int)
    d['status'] = 'RECONCILED RESEARCH' if reconciled else 'PROVISIONAL INPUT — NO BET'
    d['evaluation_cohort'] = np.where(reconciled & d.country.eq('AU'), 'AU', '')
    d['country_warning']=np.where(d.country.eq('NZ'),'NZ_NOT_VALIDATED','AU_RETROSPECTIVE_ONLY')
    d['estimated_top3_probability']=np.nan;pairs=[]
    for race,g in d.groupby('race_id',sort=False):
        top,q=exotics(g.v7_win_probability.to_numpy(),3);d.loc[g.index,'estimated_top3_probability']=top
        rows=list(g.itertuples())
        for i in range(len(rows)):
            for j in range(i+1,len(rows)):
                pairs.append(dict(race_id=race,runner_a=rows[i].runner_id,runner_b=rows[j].runner_id,
                    estimated_quinella_probability=float(q[i,j]),fair_decimal_odds=float(1/q[i,j]),
                    status='UNCALIBRATED_HARVILLE_ESTIMATE'))
    decisions=[value_decision(p,o) for p,o in zip(d.v7_win_probability,odds)]
    d['research_value_label']=[x['decision'] for x in decisions];d['net_edge']=[x['net_edge'] for x in decisions]
    # Deployment remains NO BET until V7 is validated and approved separately.
    d['deployment_decision']='NO BET — V7 UNAPPROVED'
    out.mkdir(parents=True,exist_ok=True);d.to_csv(out/'v7_research_scores.csv',index=False)
    pd.DataFrame(pairs).to_csv(out/'quinella_estimates.csv',index=False)
    (out/'blackbook_next_starts.json').write_text(json.dumps(alerts,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--features',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-restricted', action='store_true')
    a=p.parse_args();run(a.model,a.features,a.output,allow_restricted=a.allow_restricted)
