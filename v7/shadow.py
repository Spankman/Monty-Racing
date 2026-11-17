"""Immutable prospective shadow records; results never overwrite forecasts."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from .evidence import utc


def freeze(rows,path,models,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('Timezone required')
    seen=set()
    for r in rows:
        key=(r['race_id'],r['runner_id'])
        if key in seen:raise ValueError('Duplicate runner')
        seen.add(key)
        if utc(r['scheduled_start_utc'])<=now:raise ValueError('Race already started or start unverified')
        if utc(r['odds_captured_at_utc'])>now:raise ValueError('Future quote capture')
        if r['odds']<=1 or not r.get('source_url'):raise ValueError('Quote provenance required')
    for race in {r['race_id'] for r in rows}:
        g=[r for r in rows if r['race_id']==race]
        for model in ('v6','v7','market') + (('candidate2',) if 'candidate2_probability' in g[0] else ()):
            p=[r[model+'_probability'] for r in g]
            if not np.isfinite(p).all() or min(p)<=0 or not np.isclose(sum(p),1):raise ValueError('Incomplete normalized field')
    payload=dict(status='PROSPECTIVE_SHADOW_NO_REAL_BETS',frozen_at_utc=now.isoformat(),models=models,
        quote_warning='Cached TAB fixed-win quotes, not refreshed at freeze. Recheck scratchings before practical use.',
        missing_features='Saved training defaults used. Sparse-input research comparison only.',
        odds_contract='TAB fixed win, zero bookmaker commission; no execution or liquidity guarantee',rows=rows)
    encoded=json.dumps(payload,sort_keys=True,indent=2,allow_nan=False).encode()
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as h:h.write(encoded)
    return dict(path=str(path),sha256=hashlib.sha256(encoded).hexdigest(),races=len({r['race_id'] for r in rows}),runners=len(rows),frozen_at_utc=payload['frozen_at_utc'],first_start_utc=min(r['scheduled_start_utc'] for r in rows))


def record_results(forecast_path,results,path,now=None):
    """Append a separate verified-result file, preserving original probabilities.

    results are one per race with verified=True, source_url, available_at,
    status FINAL/ABANDONED, winner_runner_id for FINAL, and scratched_runner_ids.
    Settlement/coverage comparisons must void scratched original picks; never
    re-rank remaining horses after the outcome to manufacture a replacement.
    """
    now=now or datetime.now(timezone.utc)
    raw=Path(forecast_path).read_bytes();forecast=json.loads(raw)
    rows=forecast['rows'];races={r['race_id'] for r in rows};seen=set()
    for result in results:
        race=result['race_id']
        if race not in races or race in seen:raise ValueError('Unknown/duplicate race result')
        seen.add(race)
        if result.get('verified') is not True or not result.get('source_url'):raise ValueError('Verified source required')
        if utc(result['available_at'])>now:raise ValueError('Future result availability')
        if utc(result['available_at'])<max(utc(r['scheduled_start_utc']) for r in rows if r['race_id']==race):raise ValueError('Result predates start')
        ids={r['runner_id'] for r in rows if r['race_id']==race}
        if result['status'] not in ('FINAL','ABANDONED'):raise ValueError('Unsettled/unsupported result')
        if result['status']=='FINAL' and result.get('winner_runner_id') not in ids:raise ValueError('Winner not in frozen field')
        if not set(result.get('scratched_runner_ids',[]))<=ids:raise ValueError('Unknown scratching')
        if result.get('winner_runner_id') in result.get('scratched_runner_ids',[]):raise ValueError('Winner marked scratched')
    output=dict(forecast_sha256=hashlib.sha256(raw).hexdigest(),recorded_at_utc=now.isoformat(),results=results)
    with Path(path).open('x') as h:json.dump(output,h,indent=2)
    return output
