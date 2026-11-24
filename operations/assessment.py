"""Evidence and delivery classifications, independent of frozen model scoring.

A numerical edge is not a validated betting opportunity. This layer cannot
manufacture an approval or change any model probability or progression rule.
"""
import math


class OutputContractError(ValueError):
    """An allowlisted public error code; never carries provider data or stderr."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_output(rows, runners):
    expected = {(r['number'], r['horse']): r['odds'] for r in runners}
    observed = {(r['number'], r['horse']): r['odds'] for r in rows}
    if len(observed) != len(rows) or observed.keys() != expected.keys():
        raise OutputContractError('model_output_identity_mismatch')
    if observed != expected:
        raise OutputContractError('model_output_price_mismatch')


def feature_evidence(runners, names, active):
    """Count only actual adapter inputs and the two deterministic market features."""
    counts = {name: len(runners) if name in ('log_field_size', 'log_market_probability') else
              sum(type(r.get(name)) in (int, float) and math.isfinite(r[name]) for r in runners)
              for name in names}
    missing = [name for name in active if counts[name] != len(runners)]
    return dict(total_features=len(names), active_features=len(active), runners=len(runners),
                observed_counts=counts, imputed_active_features=missing,
                fully_observed_active_features=len(active)-len(missing),
                historical_form_verified=False,
                historical_form_reason='No compatible as-of historical feature join in this runner; frozen imputation applies',
                expert_weight_used=0.0, model_weight_used=1.0,
                expert_weight_reason='Operational inference does not invoke the research expert blender')


def classify(model, version):
    """Add orthogonal prediction and approval outcomes; retain legacy reason keys."""
    status = model.get('status')
    if status == 'SCORED':
        model['prediction_classification'] = 'RESEARCH ONLY' if version == 'V7' else 'PROVISIONAL'
        # No production approval evaluator is wired into the existing runner.
        # Do not infer an approval from positive edge or from a boolean supplied
        # by a provider. Retain every missing-evidence gate explicitly.
        model['betting_decision'] = 'DATA BLOCKED'
        model['official_classification'] = 'DATA BLOCKED'
        model['assessment_level'] = 'RESEARCH ONLY' if version == 'V7' else 'PROVISIONAL'
    else:
        outcome = 'EXECUTION FAILED' if status == 'FAILED' else 'DATA BLOCKED'
        model['prediction_classification'] = outcome
        model['betting_decision'] = outcome
        model['official_classification'] = outcome
    model['model_inference'] = status == 'SCORED'
    model['betting_authorised'] = False
    return model


def diagnostic(model):
    """A standard command may expose labelled evidence, never an approved ticket."""
    if model.get('status') != 'SCORED':
        return None
    return dict(classification=model.get('prediction_classification', 'PROVISIONAL'),
                betting_authorised=False, ranked_runners=model.get('ranked_runners', []),
                ordered_selections=model.get('ordered_selections', []),
                progression_bet_type=model.get('progression_bet_type'),
                roughies=model.get('roughies', []), limitations=model.get('no_bet_reasons', []))


def provider_inventory(payload, day):
    """Aggregate observed availability, never confuse availability with validation."""
    from collections import Counter
    from krok_adapter import price, named_bookmaker
    meetings=[];fields=Counter();conditions=0;named=0;priced=0;unknown_scratchings=0
    for meeting in payload.get('data',[]):
        if str(meeting.get('date',''))[:10]!=day or meeting.get('type') not in ('T','R'):continue
        races=meeting.get('races') or []
        meetings.append(dict(meeting=meeting.get('venue'),country=meeting.get('country'),races=len(races)))
        for race in races:
            conditions+=bool(race.get('track_condition') or meeting.get('track_hint'))
            for runner in race.get('runners') or []:
                for key in ['jockey','trainer','form','recent_form','history','career','form_stats','weight','claim_kg','age']:
                    if runner.get(key) not in (None,'',[]):fields[key]+=1
                if type(runner.get('is_scratched')) is not bool:unknown_scratchings+=1
                if runner.get('is_scratched') is not False:continue
                quote,origin=price(runner)
                if quote is not None:
                    priced+=1;named+=named_bookmaker(runner,quote,origin) is not None
    return dict(pages_fetched=(payload.get('meta') or {}).get('pages_fetched'),meetings=meetings,
                provider_condition_observations=conditions,runner_field_availability=dict(fields),
                priced_active_runners=priced,named_selected_price_runners=named,
                unknown_scratching_statuses=unknown_scratchings,
                historical_feature_compatibility_verified=False,
                limitation='Presence counts only; form strings, BSP and aggregates are not original V6 residual features')
