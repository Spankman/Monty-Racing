"""Immutable prospective shadow records; results never overwrite forecasts."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from .evidence import utc


def freeze(rows,path,models,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('Timezone required')
    rows=list(rows)
    if not rows:
        raise ValueError('Empty shadow card')
    groups=defaultdict(list)
    seen=set()
    for r in rows:
        key=(r['race_id'],r['runner_id'])
        if key in seen:raise ValueError('Duplicate runner')
        seen.add(key)
        if utc(r['scheduled_start_utc'])<=now:raise ValueError('Race already started or start unverified')
        if utc(r['odds_captured_at_utc'])>now:raise ValueError('Future quote capture')
        if not math.isfinite(r['odds']) or r['odds']<=1 or not r.get('source_url'):
            raise ValueError('Quote provenance required')
        groups[r['race_id']].append(r)
    models_to_check=['v6','v7','market']
    if any('candidate2_probability' in row for row in rows):
        models_to_check.append('candidate2')
    for field in groups.values():
        if len(field)<2 or len({utc(row['scheduled_start_utc']) for row in field})!=1:
            raise ValueError('Incomplete field or conflicting start times')
        for model in models_to_check:
            p=[row.get(model+'_probability',math.nan) for row in field]
            if not np.isfinite(p).all() or min(p)<=0 or not math.isclose(sum(p),1,abs_tol=1e-8):
                raise ValueError('Incomplete normalized field')
    payload=dict(status='PROSPECTIVE_SHADOW_NO_REAL_BETS',frozen_at_utc=now.isoformat(),models=models,
        quote_warning='Cached TAB fixed-win quotes, not refreshed at freeze. Recheck scratchings before practical use.',
        missing_features='Saved training defaults used. Sparse-input research comparison only.',
        odds_contract='TAB fixed win, zero bookmaker commission; no execution or liquidity guarantee',rows=rows)
    encoded=json.dumps(payload,sort_keys=True,indent=2,allow_nan=False).encode()
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as h:h.write(encoded)
    return dict(path=str(path),sha256=hashlib.sha256(encoded).hexdigest(),races=len(groups),runners=len(rows),frozen_at_utc=payload['frozen_at_utc'],first_start_utc=min(utc(r['scheduled_start_utc']) for r in rows).isoformat())


def record_results(forecast_path,results,path,now=None,*,expected_sha256=None):
    """Append a separate verified-result file, preserving original probabilities.

    results are one per race with verified=True, source_url, available_at,
    status FINAL/ABANDONED, winner_runner_id for FINAL, and scratched_runner_ids.
    Settlement/coverage comparisons must void scratched original picks; never
    re-rank remaining horses after the outcome to manufacture a replacement.
    """
    now=now or datetime.now(timezone.utc)
    raw=Path(forecast_path).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and digest!=expected_sha256:
        raise ValueError('Frozen forecast differs from its receipt')
    forecast=json.loads(raw)
    if forecast.get('status')!='PROSPECTIVE_SHADOW_NO_REAL_BETS':
        raise ValueError('Expected an immutable shadow forecast')
    frozen_at=utc(forecast['frozen_at_utc'])
    races=defaultdict(list)
    for row in forecast['rows']:
        races[row['race_id']].append(row)
    results=list(results)
    if not results:
        raise ValueError('No verified results supplied')
    seen=set()
    for result in results:
        race=result['race_id']
        if race not in races or race in seen:raise ValueError('Unknown/duplicate race result')
        seen.add(race)
        if result.get('verified') is not True or not result.get('source_url'):raise ValueError('Verified source required')
        available=utc(result['available_at'])
        if available>now:raise ValueError('Future result availability')
        if result['status'] not in ('FINAL','ABANDONED'):raise ValueError('Unsettled/unsupported result')
        if available<=frozen_at or (
            result['status']=='FINAL'
            and available<max(utc(r['scheduled_start_utc']) for r in races[race])
        ):
            raise ValueError('Result predates forecast or recorded start')
        ids={r['runner_id'] for r in races[race]}
        if result['status']=='FINAL' and result.get('winner_runner_id') not in ids:raise ValueError('Winner not in frozen field')
        if not set(result.get('scratched_runner_ids',[]))<=ids:raise ValueError('Unknown scratching')
        if result.get('winner_runner_id') in result.get('scratched_runner_ids',[]):raise ValueError('Winner marked scratched')
    output=dict(forecast_sha256=digest,recorded_at_utc=now.isoformat(),results=results,
                probability_comparison=_compare(races,results))
    path=Path(path)
    if path.resolve()==Path(forecast_path).resolve():
        raise ValueError('Results require a separate file')
    encoded=json.dumps(output,indent=2,allow_nan=False)
    with path.open('x') as handle:
        handle.write(encoded)
    return output


def _compare(races, results):
    """Score paired, unchanged fields and account explicitly for omitted races."""
    scores=defaultdict(lambda: defaultdict(list))
    omitted=defaultdict(int)
    for result in results:
        if result['status']=='ABANDONED':
            omitted['abandoned']+=1
            continue
        scratchings=result.get('scratched_runner_ids')
        if scratchings != []:
            omitted['scratchings_present' if scratchings else 'scratchings_unverified']+=1
            continue
        field=races[result['race_id']]
        countries={runner.get('country') for runner in field}
        if countries not in ({'AU'},{'NZ'}):
            omitted['country_unverified']+=1
            continue
        model_names=['v6','v7','market']
        if all('candidate2_probability' in runner for runner in field):
            model_names.append('candidate2')
        winner=result['winner_runner_id']
        for model in model_names:
            probabilities=[runner[model+'_probability'] for runner in field]
            outcomes=[int(runner['runner_id']==winner) for runner in field]
            loss=-math.log(probabilities[outcomes.index(1)])
            brier=sum((p-y)**2 for p,y in zip(probabilities,outcomes))
            top=max(range(len(field)),key=probabilities.__getitem__)
            scores[next(iter(countries))][model].append((loss,brier,outcomes[top]))
    comparison={}
    for country, models in scores.items():
        comparison[country]={}
        for model, rows in models.items():
            loss,brier,strike=np.mean(rows,axis=0)
            comparison[country][model]=dict(races=len(rows),log_loss=float(loss),
                                            brier_per_race=float(brier),top_pick_strike=float(strike))
    return dict(by_country=comparison,excluded=dict(omitted),results_pending=len(races)-len(results))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forecast',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--results',type=Path,required=True,help='Verified result records as a JSON list')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    receipt=json.loads(args.receipt.read_text())
    results=json.loads(args.results.read_text())
    if not isinstance(results,list) or any(not isinstance(result,dict) for result in results):
        parser.error('results must be a JSON list of objects')
    output=record_results(args.forecast,results,args.output,expected_sha256=receipt['sha256'])
    print(f"Recorded {len(output['results'])} verified race results against {output['forecast_sha256']}")


if __name__=='__main__':
    main()
