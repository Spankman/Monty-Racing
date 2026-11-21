"""Provisional fixed-WIN-odds value diagnostic, not betting advice.

A positive model ROI is not evidence of a calibrated edge.
"""
import math

def select_value_watch(runners):
    """Return highest positive model-ROI runner, or None if no positive edge.

    All runners must have finite probabilities in (0,1) and fixed odds > 1.
    No candidate is ever betting-authorised.
    """
    if not runners:
        return None
    ranked = []
    for runner in runners:
        p = float(runner["v7_win_probability"])
        odds = float(runner["fixed_win_odds"])
        if not (math.isfinite(p) and 0 < p < 1 and math.isfinite(odds) and odds > 1):
            raise ValueError("invalid probability or fixed win odds")
        ranked.append((p * odds - 1, runner, p, odds))
    edge, runner, p, odds = max(ranked, key=lambda item: item[0])
    if edge <= 0:
        return None
    return {
        "number": str(runner["number"]),
        "horse": str(runner["horse"]),
        "fixed_win_odds": odds,
        "v7_win_probability": p,
        "model_expected_win_roi": edge,
        "model_fair_win_odds": 1 / p,
        "same_as_best_bet": str(runner["number"]) == str(runners[0]["number"]),
        "positive_model_edge": True,
        "betting_authorised": False,
        "warning": "Uncalibrated model-only value diagnostic; NO BET",
    }
