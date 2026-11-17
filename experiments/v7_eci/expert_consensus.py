"""Leakage-safe expert consensus feature builder for Monty V7 experiments.

Input rows: race_id, runner_id, expert_id, published_at (ISO timezone-aware),
cutoff_at (ISO timezone-aware), rank (positive integer or blank),
best_bet (bool), roughie (bool). Missing opinions are not negative votes.
"""
from collections import defaultdict
from datetime import datetime

def _time(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamps must have a timezone")
    return dt

def build_consensus(opinions, runner_ids, race_id, cutoff_at, expert_weights=None):
    """Return per-runner features. Weights must be fitted on prior races only."""
    cutoff = _time(cutoff_at)
    weights = expert_weights or {}
    by_expert = {}
    for row in opinions:
        if str(row["race_id"]) != str(race_id):
            continue
        published = _time(row["published_at"])
        if published > cutoff or _time(row["cutoff_at"]) > cutoff:
            continue
        expert = str(row["expert_id"])
        runner = str(row["runner_id"])
        if runner not in {str(x) for x in runner_ids}:
            continue
        key = (expert, runner)
        if key in by_expert:
            raise ValueError("Duplicate expert/runner opinion: " + str(key))
        by_expert[key] = row
    experts = {e for e, _ in by_expert}
    result = {}
    for runner_id in runner_ids:
        runner = str(runner_id)
        rows = [(e, row) for (e, r), row in by_expert.items() if r == runner]
        picks = [(e, row) for e, row in rows if row.get("rank") is not None]
        total_weight = sum(float(weights.get(e, 1.0)) for e in experts)
        support = sum(float(weights.get(e, 1.0)) for e, row in picks if int(row["rank"]) <= 3)
        first = sum(int(row["rank"]) == 1 for _, row in picks)
        result[runner] = {
            "eci_experts_observed": len(experts),
            "eci_experts_ranking_runner": len(picks),
            "eci_top3_votes": sum(int(row["rank"]) <= 3 for _, row in picks),
            "eci_first_votes": first,
            "eci_best_bet_votes": sum(bool(row.get("best_bet")) for _, row in rows),
            "eci_roughie_votes": sum(bool(row.get("roughie")) for _, row in rows),
            "eci_weighted_top3_share": support / total_weight if total_weight else None,
            "eci_coverage_share": len(picks) / len(experts) if experts else None,
            "eci_missing": not bool(experts),
        }
    return result
