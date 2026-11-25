"""Research-only longshot visibility and complete exclusion accounting.

No scoring, betting approval, quota or threshold modification. A positive EV
caused only by normalising an underround is never a model-value candidate.
"""
from datetime import timedelta
import math
from operations.market_integrity import timestamp,MAX_AGE_SECONDS


def audit(race,model,version,now):
    rows=model.get('ranked_runners') or []
    expected=race.get('data_completeness',{}).get('active_runners')
    usable=bool(rows) and len(rows)==expected and len({str(r['number']) for r in rows})==len(rows)
    usable=usable and all(type(r.get('odds')) in (int,float) and math.isfinite(r['odds']) and r['odds']>1
                          and type(r.get('probability')) in (int,float) and 0<r['probability']<=1 for r in rows)
    usable=usable and math.isclose(sum(r['probability'] for r in rows),1,abs_tol=1e-6)
    saved=[]
    if not usable:
        # Legacy archives cannot recover a complete market from short ticket rows.
        seen={}
        for field in ('ordered_selections','roughies','best_bets','best_chance'):
            values=model.get(field) or []
            for row in [values] if isinstance(values,dict) else values:
                seen.setdefault(str(row['number']),row)
        rows=list(seen.values())
    total=sum(1/r['odds'] for r in rows) if usable else None
    market_audit=model.get('market_integrity') or race.get('market_integrity') or {}
    warnings=list(market_audit.get('warnings',[]))
    # Missing independent verification is disclosed, but does not suppress a
    # valid provider-field research comparison. Other anomalies stay blocked.
    essential=[s for s in warnings if s!='independent_field_unverified']
    if not market_audit:essential.append('market_integrity_audit_unavailable')
    if total is not None and total<1:essential.append('underround_requires_independent_verification')
    if usable and len({r.get('bookmaker') for r in rows})!=1:essential.append('mixed_bookmakers')
    legacy={str(r['number']) for r in model.get('roughies',[])}
    try:capture_until=(timestamp(race['captured_at'])+timedelta(seconds=MAX_AGE_SECONDS)).isoformat()
    except (ValueError,TypeError,KeyError,AttributeError):capture_until=None
    evidence=model.get('input_evidence') or model.get('input_summary') or {}
    for rank,row in enumerate(rows,1):
        if type(row.get('odds')) not in (int,float) or row['odds']<10:continue
        odds=row['odds'];p=row.get('probability');market=(1/odds)/total if total else None
        delta=p-market if market is not None and type(p) in (int,float) else None
        edge=p*odds-1 if type(p) in (int,float) else None
        reasons=[]
        if model.get('status')!='SCORED':reasons.append('genuine_model_inference_unavailable')
        if not usable:reasons.append('complete_ranked_field_not_preserved')
        if market is None:reasons.append('normalised_full_market_unavailable')
        elif delta<=1e-12:reasons.append('no_positive_model_advantage_over_market')
        if edge is None or edge<=0:reasons.append('no_positive_captured_price_expected_value')
        # These mirror existing selection() criteria; they are not new cutoffs.
        if version=='V7' and type(p) in (int,float) and p<.06:reasons.append('existing_V7_probability_floor_6pct')
        if not row.get('bookmaker'):reasons.append('named_bookmaker_unverified')
        quotes=row.get('quote_timestamps') or []
        quoted=None;expires=None
        try:
            times=[timestamp(q) for q in quotes]
            if not times or len(set(times))!=1:raise ValueError('No unique offer observation')
            quoted=times[0]
            expires=min(quoted+timedelta(seconds=MAX_AGE_SECONDS),timestamp(race['captured_at'])+timedelta(seconds=MAX_AGE_SECONDS),timestamp(race['scheduled_start']))
            if quoted>now:reasons.append('future_offer_timestamp')
            if now>=expires:reasons.append('expired_offer_or_race_closed')
        except (ValueError,TypeError,KeyError,AttributeError):reasons.append('offer_observation_timestamp_unavailable' if quoted is None else 'capture_or_jump_timing_unavailable')
        reasons.extend(essential)
        reasons=list(dict.fromkeys(reasons))
        candidate=not reasons
        data_blocked=any(r not in ('no_positive_model_advantage_over_market','no_positive_captured_price_expected_value','existing_V7_probability_floor_6pct') for r in reasons)
        numerical_watch=edge is not None and edge>0
        normalisation=1/total-1 if total else None
        # Only existing forecasts are inspected; missing values stay null.
        saved.append(dict(meeting=race['meeting'],race=str(race['race']),number=str(row['number']),horse=row['horse'],
            odds=odds,bookmaker=row.get('bookmaker'),model_version=version,model_probability=p,
            normalised_market_probability=market,predictive_advantage=delta,
            numerical_expected_value=edge,market_normalisation_edge=normalisation,
            model_edge_contribution=delta*odds if delta is not None else None,
            model_rank=rank if usable else None,market_rank=1+sum(r['odds']<odds for r in rows) if usable else None,
            status=('RESEARCH ONLY' if version=='V7' else 'PROVISIONAL RESEARCH') if candidate else 'DATA BLOCKED' if data_blocked else 'EXCLUDED',
            research_candidate=candidate,legacy_watch=str(row['number']) in legacy,
            display_watch=(candidate or numerical_watch) and 'expired_offer_or_race_closed' not in reasons,
            reasons=reasons or ['positive_model_contribution_and_point_EV; independent verification/value approval still absent'],
            data_quality=dict(full_scored_field=bool(usable),historical_form_verified=evidence.get('historical_form_verified',False),
                              fully_observed_active_features=evidence.get('fully_observed_active_features'),active_features=evidence.get('active_features'),warnings=warnings),
            confidence='REDUCED — point probability, not a validated per-runner confidence interval',
            price_observed_at=quoted.isoformat() if quoted else None,price_valid_until=expires.isoformat() if expires else None,
            capture_valid_until=capture_until,
            official_betting_approval='NOT APPROVED',betting_authorised=False,bet_type='WIN ONLY'))
    return dict(schema='monty.ruffies.v1',version=version,complete_scored_field=bool(usable),
        expected_active_runners=expected,observed_ranked_runners=len(rows),
        longshots_identified=len(saved),unknown_unpreserved_runners=max(0,expected-len(rows)) if type(expected) is int else None,
        covered_runner_numbers=[r['number'] for r in saved],
        research_candidates=sum(r['research_candidate'] for r in saved),
        none_reason=None if any(r['research_candidate'] for r in saved) else
          'No $10+ runner passes the unchanged policy and research data checks; see exclusions.' if usable else
          'Full rankings/prices were not preserved; the missing $10+ population and its exclusions cannot be reconstructed.',
        rows=saved)


def attach(race,model,version,now):
    model['ruffies_to_watch']=audit(race,model,version,now)


def text(model):
    section=model.get('ruffies_to_watch')
    if not section:return []
    lines=['RUFFIES TO WATCH — WIN ONLY · RESEARCH · NO BET']
    if section.get('none_reason'):lines.append(section['none_reason'])
    for row in section['rows']:
        if not row['display_watch']:continue
        def percent(v):return 'UNAVAILABLE' if v is None else f'{100*v:.3f}%'
        prefix='RUFFY / VALUE WATCH · ' if row['legacy_watch'] else 'RESEARCH DIAGNOSTIC · '
        lines.extend([prefix+f"{row['meeting']} R{row['race']} · #{row['number']} {row['horse']} · ${row['odds']:.2f} ({row['bookmaker'] or 'BOOK UNVERIFIED'}) · {row['model_version']}",
            f"{row['status']} · model {percent(row['model_probability'])}; market {percent(row['normalised_market_probability'])}; advantage {percent(row['predictive_advantage'])}; point EV {percent(row['numerical_expected_value'])}",
            'Quality: '+row['confidence']+'; history '+('VERIFIED' if row['data_quality']['historical_form_verified'] else 'INCOMPLETE'),
            'Reason: '+'; '.join(row['reasons']),
            'Price observed '+str(row['price_observed_at'] or 'UNKNOWN')+' · expires '+str(row['price_valid_until'] or 'UNVERIFIED')+' · Official approval: NOT APPROVED'])
    return lines


def refresh(section,model,now):
    """Compact retrieval retains hash-bound calculations, never rebuilds a book
    from trimmed ticket rows. Refresh only time/quarantine, never approvals.
    """
    from copy import deepcopy
    out=deepcopy(section)
    warnings=(model.get('market_integrity') or {}).get('warnings',[])
    essential=[x for x in warnings if x!='independent_field_unverified']
    for row in out['rows']:
        try:expired=now>=timestamp(row['price_valid_until'])
        except (ValueError,TypeError,KeyError,AttributeError):expired=False
        if expired:
            row.update(research_candidate=False,display_watch=False,status='EXPIRED')
            if 'expired_offer_or_race_closed' not in row['reasons']:row['reasons'].append('expired_offer_or_race_closed')
        elif essential:
            row.update(research_candidate=False,status='DATA BLOCKED')
            row['reasons']=list(dict.fromkeys(row['reasons']+essential))
        row['official_betting_approval']='NOT APPROVED';row['betting_authorised']=False
    out['research_candidates']=sum(r['research_candidate'] for r in out['rows'])
    if not out['research_candidates']:out['none_reason']='No current research candidates pass the unchanged policy/data checks; inspect exclusions and expiry.'
    return out
