"""Experimental, point-in-time expert consensus features. Does not alter V6."""
from collections import defaultdict
from datetime import datetime, timezone
import math

def _time(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamps must include timezone")
    return dt.astimezone(timezone.utc)

def consensus_features(race_id, runners, evaluations, cutoff, weights=None):
    """Return per-runner features; missing coverage is not a negative vote.

    evaluations: race_id, runner_id, expert_id, published_at, rank (1..),
                 optional confidence (0..1). One latest eligible vote per expert.
    """
    weights = weights or {}
    deadline = _time(cutoff)
    selected = {}
    for e in evaluations:
        if e["race_id"] != race_id or e["runner_id"] not in runners:
            continue
        published = _time(e["published_at"])
        if published > deadline:
            continue
        rank = int(e["rank"])
        confidence = float(e.get("confidence", 1.0))
        if rank < 1 or not 0 <= confidence <= 1:
            raise ValueError("Invalid rank or confidence")
        expert = str(e["expert_id"])
        previous = selected.get(expert)
        if previous is None or published > previous[0]:
            selected[expert] = (published, e)
    experts = {k: v[1] for k, v in selected.items()}
    denominator = sum(max(0.0, float(weights.get(k, 1.0))) for k in experts)
    out = {}
    for runner in runners:
        votes = [(expert, e) for expert, e in experts.items() if e["runner_id"] == runner]
        weighted = sum(max(0.0, float(weights.get(k, 1.0))) for k, _ in votes)
        out[runner] = {
            "expert_coverage": len(experts),
            "expert_top1_votes": sum(int(e["rank"] == 1) for _, e in votes),
            "expert_top3_votes": sum(int(e["rank"] <= 3) for _, e in votes),
            "expert_vote_share": len(votes) / len(experts) if experts else None,
            "expert_weighted_share": weighted / denominator if denominator else None,
            "expert_mean_confidence": sum(e.get("confidence", 1.0) for _, e in votes) / len(votes) if votes else None,
            "expert_data_missing": not bool(experts),
        }
    return out
