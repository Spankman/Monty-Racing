"""Shadow-only win approval experiment using externally validated input bounds."""
from math import isfinite


def assess(version, inference_status, verified_field, verification_blockers, rows):
    """Evaluate interval EV at independently verified prices.

    Rows cover the complete active field. Bounds must come from a previously
    validated calibration procedure. The minimum price is a separately
    supported conservative executable-price bound derived from market movement.
    The caller authenticates data provenance. This experiment cannot approve bets.
    """
    if version not in ('V6', 'V7'):
        raise ValueError('Unknown version')
    if inference_status == 'FAILED':
        return {'prediction': 'EXECUTION FAILED', 'decision': 'EXECUTION FAILED'}
    if inference_status == 'EXPIRED':
        return {'prediction': 'EXPIRED', 'decision': 'EXPIRED'}
    if inference_status != 'SCORED':
        return {'prediction': 'DATA BLOCKED', 'decision': 'DATA BLOCKED'}
    prediction = 'RESEARCH ONLY' if version == 'V7' else 'PROVISIONAL'
    result = {'prediction': prediction, 'decision': 'DATA BLOCKED',
              'betting_authorised': False, 'blockers': list(verification_blockers)}
    if result['blockers']:
        return result
    try:
        numbers = {row['number'] for row in rows}
    except (TypeError, KeyError):
        result['blockers'].append('invalid_calibrated_market_field')
        return result
    if not numbers or numbers != set(verified_field) or len(numbers) != len(rows):
        result['blockers'].append('incomplete_calibrated_market_field')
        return result

    edges = {}
    for row in rows:
        number = row['number']
        try:
            p_low, probability, p_high = row['probability_bounds']
            floor, quote = row['price_floor'], row['fixed_win']
        except (TypeError, ValueError, KeyError):
            result['blockers'].append('invalid_calibration_or_executable_price')
            return result
        if (not all(type(v) in (float, int) and isfinite(v)
                    for v in (p_low, probability, p_high, floor, quote))
                or not 0 <= p_low <= probability <= p_high <= 1
                or not 1 < floor <= quote or quote != verified_field[number]):
            result['blockers'].append('invalid_calibration_or_executable_price')
            return result
        edges[number] = {'fair_odds': 1/probability if probability else None,
                         'point_ev': probability*quote-1,
                         'lower_ev': p_low*floor-1,
                         'upper_ev': p_high*quote-1}
    if abs(sum(row['probability_bounds'][1] for row in rows)-1) > 1e-9:
        result['blockers'].append('unnormalized_calibrated_probabilities')
        return result
    result['ev'] = edges
    result['positive_lower_bound'] = [number for number, edge in edges.items()
                                      if edge['lower_ev'] > 0]
    if version == 'V7':
        result['decision'] = 'RESEARCH ONLY'
    else:
        result['decision'] = ('NO BET' if all(edge['upper_ev'] <= 0 for edge in edges.values())
                              else 'PROVISIONAL')
    return result
