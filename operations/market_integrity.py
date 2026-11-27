"""Market evidence gate and arithmetic attribution; never changes frozen scores.

No underround is executable value by default. Missing quote timestamps stay
missing: retrieval time is not the age of an upstream offer. This module cannot
approve betting or release quarantine from an unchecked verification boolean.
"""
from datetime import datetime, timezone
from math import fsum, isfinite

MAX_AGE_SECONDS = 300  # Existing operational freshness window, unchanged.


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:raise ValueError('Timezone required')
    return parsed.astimezone(timezone.utc)


def quote_evidence(runner):
    """Preserve times only on the exact price chosen by the existing adapter."""
    from krok_adapter import price, named_bookmaker
    selected, origin = price(runner)
    times = []
    selected_offer=None
    if origin == 'TAB':
        # price() takes the FIRST valid TAB price, not a later matching offer.
        for quote in runner.get('odds', []) if isinstance(runner.get('odds'), list) else []:
            if not isinstance(quote, dict):continue
            if str(quote.get('bookmaker', '')).strip().lower() == 'tab':
                from krok_adapter import number
                if number(quote.get('win')):
                    selected_offer=quote
                    break
    elif origin:
        times = [runner[k] for k in (origin+'_captured_at',origin+'_quoted_at', origin+'_updated_at') if runner.get(k) is not None]
        if not times:
            from krok_adapter import FIXED_BOOKMAKERS,number
            book=named_bookmaker(runner,selected,origin)
            matches=[q for q in runner.get('odds',[]) if isinstance(q,dict) and number(q.get('win'))==selected
                     and book and FIXED_BOOKMAKERS.get(str(q.get('bookmaker','')).strip().casefold())==book] if isinstance(runner.get('odds'),list) else []
            if len(matches)==1:selected_offer=matches[0]
    basis='OFFER_REPORTED_TIME_UNVERIFIED'
    if selected_offer is not None:
        # Capture and bookmaker update are distinct vintages. Never compare
        # unlike semantics as if they were duplicate timestamps.
        captured=[selected_offer[k] for k in ('captured_at','capturedAt') if selected_offer.get(k) is not None]
        times=captured or [selected_offer[k] for k in ('quoted_at','updated_at') if selected_offer.get(k) is not None]
        if captured:
            collector='PUNTERSEDGE' if selected_offer.get('_collector')=='PuntersEdge' else 'KROK'
            basis=collector+'_PROVIDER_OBSERVATION_NOT_BOOKMAKER_UPDATE'
    elif origin and runner.get(origin+'_captured_at') is not None:
        times=[runner[origin+'_captured_at']];basis='KROK_PROVIDER_OBSERVATION_NOT_BOOKMAKER_UPDATE'
    return dict(number=str(runner.get('number')), horse=runner.get('name'), odds=selected,
                bookmaker=named_bookmaker(runner, selected, origin) if selected else None,
                quote_timestamps=times,quote_time_basis=basis,independent_price_verification=False)


def analyze(rows, *, expected_active, captured_at=None, now=None, context=None):
    """Assess a full price vector; incomplete books have lower bounds only.

    Different timestamps are flagged without inventing a synchronization tolerance.
    This is a quarantine pending evidence, not a new predictive threshold.
    """
    now = now or datetime.now(timezone.utc)
    flags = []
    numbers = [str(r.get('number')) for r in rows]
    valid = [r for r in rows if type(r.get('odds')) in (int,float) and isfinite(r['odds']) and r['odds'] > 1]
    if len(set(numbers)) != len(numbers):flags.append('duplicate_runner_identity')
    if any(not r.get('horse') or r.get('number') is None for r in rows):flags.append('missing_runner_identity')
    if len(valid) != len(rows):flags.append('missing_or_invalid_prices')
    complete = type(expected_active) is int and expected_active > 0 and len(rows) == expected_active and len(valid) == len(rows) and not flags
    if not complete:flags.append('incomplete_active_price_vector')
    if context:
        declared, observed = context.get('declared_count'), context.get('observed_declared_count')
        # Providers may count declared or active runners. Neither convention
        # permits more declarations than supplied rows, or fewer than active.
        if type(declared) is int and (declared > observed or declared < len(context.get('active_identities',rows))):
            flags.append('provider_declared_runner_count_mismatch')
        expected = context.get('active_identities')
        if expected is not None and {(str(r['number']),r['horse']) for r in rows} != {tuple(r) for r in expected}:
            flags.append('missing_or_conflicting_active_runner')
        if context.get('unknown_scratching_status'):flags.append('unknown_scratching_status')
    else:
        flags.append('external_field_completeness_unverified')
    if not (context or {}).get('independent_field_verified'):flags.append('independent_field_unverified')
    if any(x in flags for x in ('provider_declared_runner_count_mismatch','missing_or_conflicting_active_runner','unknown_scratching_status')):complete=False
    lower_bound = fsum(1/r['odds'] for r in valid)
    total = lower_bound if complete else None
    if total is not None and total < 1:flags.append('underround_requires_independent_verification')
    books = sorted({r['bookmaker'] for r in rows if r.get('bookmaker')})
    if len(books)>1:flags.append('mixed_bookmakers')
    if any(not r.get('bookmaker') for r in rows):flags.append('bookmaker_unverified')
    quote_times=[]
    for row in rows:
        values=row.get('quote_timestamps') or []
        if not values:
            flags.append('quote_timestamp_unavailable');continue
        try:
            parsed=[timestamp(v) for v in values]
            if len(set(parsed)) != 1:flags.append('conflicting_runner_quote_timestamps')
            quote_times.extend(parsed)
            if any((now-t).total_seconds()>=MAX_AGE_SECONDS for t in parsed):flags.append('stale_price')
            if any(t>now for t in parsed):flags.append('future_quote_timestamp')
            if captured_at and any(t>timestamp(captured_at) for t in parsed):flags.append('quote_after_capture')
        except (TypeError,ValueError,AttributeError):flags.append('invalid_quote_timestamp')
    if len(set(quote_times))>1:flags.append('inconsistent_quote_timestamps')
    try:
        age=(now-timestamp(captured_at)).total_seconds()
        if not 0<=age<MAX_AGE_SECONDS:flags.append('capture_stale_or_future')
    except (TypeError,ValueError,AttributeError):age=None;flags.append('capture_timestamp_unavailable')
    flags=list(dict.fromkeys(flags))
    return dict(schema='monty.market_integrity.v1',status='QUARANTINED' if flags else 'EVIDENCE_REVIEW_REQUIRED',
        actionable_value_allowed=False,independently_verified=False,
        release_requirement='Independent same-race complete field/scratchings and executable named-bookmaker quote verification; approval evaluator still required',
        expected_active_runners=expected_active,observed_price_runners=len(valid),complete_price_vector=complete,
        observed_book_lower_bound_pct=100*lower_bound,book_percentage=None if total is None else 100*total,
        overround_percentage_points=None if total is None else 100*(total-1),
        underround_percentage_points=None if total is None else 100*max(0,1-total),
        market_only_numerical_edge=None if total is None else 1/total-1,
        market_only_baseline=None if total is None else [dict(number=str(r['number']),horse=r['horse'],odds=r['odds'],
            probability=(1/r['odds'])/total) for r in rows],
        bookmakers=books,quote_timestamp_count=len(quote_times),capture_age_seconds=age,
        quote_timestamp_semantics=sorted({r.get('quote_time_basis') or 'UNVERIFIED' for r in rows}),
        captured_at=captured_at,oldest_quote_at=min(quote_times).isoformat() if quote_times else None,
        latest_quote_at=max(quote_times).isoformat() if quote_times else None,warnings=flags)


def refresh(audit, now):
    from copy import deepcopy
    out=deepcopy(audit)
    for key,flag in (('oldest_quote_at','stale_price'),('captured_at','capture_stale_or_future')):
        if out.get(key):
            age=(now-timestamp(out[key])).total_seconds()
            if key=='captured_at':out['capture_age_seconds']=age
            if not 0<=age<MAX_AGE_SECONDS and flag not in out['warnings']:out['warnings'].append(flag)
    if out['warnings']:out['status']='QUARANTINED'
    return out


def attribute(rows, audit):
    """Raw edge = market-normalization edge + model contribution, exactly."""
    total=audit['book_percentage']/100 if audit['complete_price_vector'] else None
    result=[]
    for row in rows:
        p,odds=row['probability'],row['odds']
        baseline=(1/odds)/total if total else None
        delta=p-baseline if baseline is not None else None
        result.append(dict(row,market_probability=baseline,
            numerical_win_edge=p*odds-1,fair_win_odds=1/p,
            market_only_numerical_edge=1/total-1 if total else None,
            model_probability_uplift=delta,model_edge_contribution=delta*odds if delta is not None else None,
            value_attribution='BASELINE UNAVAILABLE' if baseline is None else
                'NORMALIZATION-DRIVEN APPARENT VALUE' if p*odds>1 and delta<=0 else
                'POSITIVE MODEL CONTRIBUTION — NOT VALIDATED VALUE' if delta>0 else 'NO POSITIVE MODEL CONTRIBUTION',
            actionable_value=False))
    return result


def attach(model, audit):
    """Keep every watch/score. Attach warnings; never promote numerical edges."""
    model['market_integrity']=audit
    model['market_baseline']=dict(kind='normalized inverse captured fixed-win odds',
        complete=audit['complete_price_vector'],book_percentage=audit['book_percentage'],
        market_only_numerical_edge=audit['market_only_numerical_edge'],
        limitation='Diagnostic market control, not independent predictive value or executable return')
    for field in ('ranked_runners','ordered_selections','roughies','best_bets'):
        if field in model:model[field]=attribute(model[field],audit)
    for field in ('best_chance','most_likely','value_selection'):
        if model.get(field):model[field]=attribute([model[field]],audit)[0]
    for row in model.get('roughies',[]):
        row.update(classification='DIAGNOSTIC ROUGHIE WATCH — NO BET',market_warnings=audit['warnings'])
    model['recommended_bet_type']='NO BET'
    model['betting_authorised']=False
    if audit['warnings'] and model.get('betting_decision') not in ('EXPIRED','EXECUTION FAILED'):
        model['betting_decision']='DATA BLOCKED'
    model.setdefault('value_evidence',{}).update(market_quarantined=bool(audit['warnings']),
        edge_decomposition='numerical edge = market-only normalization edge + model edge contribution',
        independent_model_value_verified=False)
    return model


def archived_race(race, captured_at, now):
    """Derived read-time annotation; never rewrites the immutable source forecast.

    Union only consistent saved identities/prices. Missing model probabilities
    stay missing even when the combined views recover a full market vector.
    """
    from copy import deepcopy
    from operations.audit.roughie_concentration import audit_forecast
    audit_forecast({'races':[race]})  # Existing conflict/withdrawal checks.
    out=deepcopy(race);quotes={}
    for model in race['models'].values():
        for field in ('ranked_runners','ordered_selections','roughies','best_bets','best_chance'):
            rows=model.get(field) or []
            for row in ([rows] if isinstance(rows,dict) else rows):
                number=str(row['number'])
                if number in quotes and quotes[number].get('bookmaker') != row.get('bookmaker'):
                    # Different or missing per-runner attribution is not resolved
                    # by a race-level provider label.
                    quotes[number]['bookmaker']=None
                else:quotes[number]=dict(row,number=number)
    audit=analyze(list(quotes.values()),expected_active=race['data_completeness']['active_runners'],
                  captured_at=captured_at,now=now)
    out['market_integrity']=audit
    from operations.assessment import classify
    for version,model in out['models'].items():
        classify(model,version)
        attach(model,audit)
        model['quoted_at']=None
        model['quote_capture_at']=captured_at
    return out
