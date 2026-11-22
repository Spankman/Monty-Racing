"""Paired comparison of locked probabilities on independently reconciled fields.

Reads one CSV per quote type. Each row represents an active runner at decision.
The caller supplies the preregistered test window and four frozen probability
columns. Only unchanged, officially verified final fields are supported here.
"""
import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from historical_asof import utc_instant
from v7.eligibility import eligibility

MODELS = ("v6", "candidate1", "candidate2", "market")
GROUP = ["country", "race_id"]


def paired_report(frame, *, start, end, locked_at, quote_type, allow_restricted=False):
    if not date.fromisoformat(start) <= date.fromisoformat(end):
        raise ValueError("Holdout dates out of order")
    if quote_type not in ("exchange_proxy", "bookmaker_fixed_win"):
        raise ValueError("One quote type required per report")
    commission = 0.05 if quote_type == "exchange_proxy" else 0
    locked = utc_instant(locked_at)
    accepted, excluded = [], []
    for (country, race_id), field in frame.groupby(GROUP, dropna=False, sort=False):
        reason = eligibility(country, field.classification.iloc[0],
                             class_verified=bool(field.class_verified.eq(True).all()),
                             allow_restricted=allow_restricted)
        if reason is None:
            try:
                validate_field(field, start=start, end=end, locked=locked, quote_type=quote_type)
            except (ValueError, TypeError, OverflowError) as error:
                reason = str(error)
        if reason:
            excluded.append(dict(country=str(country), race_id=str(race_id), reason=reason))
        else:
            accepted.append(field.sort_values("runner_id"))
    report = dict(quote_type=quote_type, start=start, end=end, locked_at=locked_at,
                  excluded=excluded, by_country={})
    if not accepted:
        return report
    for country, runners in pd.concat(accepted).groupby("country"):
        metrics = {}
        by_model = {model: [] for model in MODELS}
        for _, field in runners.groupby("race_id", sort=False):
            outcomes = field.winner.to_numpy()
            for model in MODELS:
                probs = field[model].to_numpy()
                top = np.argmax(probs)
                odds = float(field.odds.iloc[top])
                p = float(probs[top])
                hit = int(outcomes[top])
                decimal_return = 1 + (odds - 1) * (1 - commission)
                selected = p * decimal_return - 1 >= 0.05
                by_model[model].append(dict(
                    date=field.date.iloc[0], classification=field.classification.iloc[0],
                    going=field.going.iloc[0], field_size=len(field), runner_count=len(field),
                    odds_band="under $4" if odds < 4 else "$4–<$10" if odds < 10 else "$10+",
                    log_loss=-np.log(probs[outcomes == 1][0]), brier=np.square(probs - outcomes).sum(),
                    hit=hit, selected=selected, expected_hit=p,
                    units=(hit * decimal_return - 1) if selected else 0,
                ))
        series = {name: pd.DataFrame(rows) for name, rows in by_model.items()}
        for name, rows in series.items():
            metrics[name] = summarize(rows)
            metrics[name]["breakdowns"] = {
                dimension: {str(key): summarize(group) for key, group in rows.groupby(dimension)}
                for dimension in ("odds_band", "classification", "field_size", "going")
            }
        report["by_country"][country] = dict(
            models=metrics, paired_day_blocks=paired_intervals(series))
    return report


def validate_field(field, *, start, end, locked, quote_type):
    constants = ("date", "classification", "going", "decision_at", "start_at",
                 "result_at", "quote_type", "bookmaker")
    if any(field[name].nunique(dropna=False) != 1 or pd.isna(field[name].iloc[0])
           for name in constants):
        raise ValueError("Conflicting or missing race metadata")
    row = field.iloc[0]
    if not start <= date.fromisoformat(row.date).isoformat() <= end:
        raise ValueError("Outside locked period")
    decision = utc_instant(row.decision_at)
    if not locked < decision < utc_instant(row.start_at) <= utc_instant(row.result_at):
        raise ValueError("Invalid decision or result chronology")
    if row.quote_type != quote_type or (quote_type == "bookmaker_fixed_win"
                                       and row.bookmaker in ("best_win", "fixed_win", "")):
        raise ValueError("Quote type or bookmaker unresolved")
    flags = ["field_verified", "features_verified_asof", "result_verified", "field_unchanged"]
    if not field[flags].eq(True).all().all():
        raise ValueError("Field, features or result unresolved")
    if not all(utc_instant(value) < decision for value in field.quote_captured_at):
        raise ValueError("Quote capture unavailable at decision")
    if (len(field) < 2 or pd.isna(row.race_id) or field.runner_id.isna().any()
            or field.runner_id.duplicated().any() or not field.winner.isin([0, 1]).all()
            or field.winner.sum() != 1):
        raise ValueError("Incomplete field or unsupported outcome")
    probs = field[list(MODELS)].to_numpy(float)
    odds = field.odds.to_numpy(float)
    if not (np.isfinite(probs).all() and (probs > 0).all()
            and np.allclose(probs.sum(axis=0), 1, atol=1e-8, rtol=0)
            and np.isfinite(odds).all() and (odds > 1).all()):
        raise ValueError("Invalid probability or quote")
    inverse = 1 / odds
    if not np.allclose(field.market, inverse / inverse.sum(), atol=1e-8, rtol=0):
        raise ValueError("Market probabilities do not match same-time field quotes")


def summarize(rows):
    bets = rows[rows.selected]
    return dict(races=len(rows), runners=int(rows.runner_count.sum()),
                log_loss=float(rows.log_loss.mean()), race_brier=float(rows.brier.mean()),
                strike_rate=float(rows.hit.mean()), bets=len(bets),
                selected_strike=float(bets.hit.mean()) if len(bets) else None,
                selected_expected_strike=float(bets.expected_hit.mean()) if len(bets) else None,
                units=float(rows.units.sum()), roi=float(bets.units.mean()) if len(bets) else None)


def paired_intervals(series):
    day = series["market"].groupby("date").size()
    if len(day) < 2:
        return {"days": len(day), "intervals": {}}
    sample = np.random.default_rng(700).integers(0, len(day), size=(2000, len(day)))
    summed = {name: rows.groupby("date")[["log_loss", "units"]].sum()
              for name, rows in series.items()}
    intervals = {}
    for name in ("v6", "candidate1", "market"):
        difference = (summed["candidate2"] - summed[name]).to_numpy()
        draws = difference[sample].sum(axis=1) / day.to_numpy()[sample].sum(axis=1)[:, None]
        values = np.quantile(draws, [0.025, 0.975], axis=0).T.tolist()
        intervals["candidate2_minus_" + name] = dict(
            log_loss_95=values[0], units_per_race_95=values[1])
    return {"days": len(day), "intervals": intervals}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    for name in ("start", "end", "locked-at"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--quote-type", required=True, choices=("exchange_proxy", "bookmaker_fixed_win"))
    parser.add_argument("--allow-restricted", action="store_true")
    args = parser.parse_args()
    rows = pd.read_csv(args.input, dtype={"race_id": str, "runner_id": str})
    report = paired_report(rows, start=args.start, end=args.end, locked_at=args.locked_at,
                           quote_type=args.quote_type, allow_restricted=args.allow_restricted)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
