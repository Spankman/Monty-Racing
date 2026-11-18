"""Point-in-time expert ranking features; experimental, never alters V6."""
from datetime import datetime, timezone
from collections import defaultdict

def utc(value):
    d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Timezone required")
    return d.astimezone(timezone.utc)

def consensus_features(race_id, runners, evaluations, cutoff, weights=None, min_experts=5, max_experts=20):
    """Use latest complete published ranking per expert, excluding future updates.

    Records: race_id, runner_id, expert_id, published_at, rank (positive integer),
    optional confidence (0..1). Same expert/time can rank multiple runners.
    An expert's latest published_at is treated as one ranking snapshot.
    """
    if min_experts < 1 or max_experts < min_experts:\n        raise ValueError("Invalid expert coverage thresholds")\n    cutoff = utc(cutoff)
    weights = weights or {}
    runner_set = set(runners)
    snapshots = defaultdict(lambda: defaultdict(list))
    for e in evaluations:
        if e["race_id"] != race_id:
            continue
        published = utc(e["published_at"])
        if published > cutoff:
            continue
        expert = str(e["expert_id"])
        if not expert:
            raise ValueError("Missing expert id")
        rank = int(e["rank"])
        conf = float(e.get("confidence", 1.0))
        if rank < 1 or not 0 <= conf <= 1:
            raise ValueError("Invalid rank/confidence")
        if e["runner_id"] not in runner_set:
            continue
        snapshots[expert][published].append((e["runner_id"], rank, conf))
    latest = {}
    for expert, versions in snapshots.items():
        rows = versions[max(versions)]
        if len({r for r, _, _ in rows}) != len(rows):
            raise ValueError("Duplicate runner within expert snapshot")
        if len({rank for _, rank, _ in rows}) != len(rows):
            raise ValueError("Duplicate ranks within expert snapshot")
        latest[expert] = rows
    # Reject oversized pools rather than silently cherry-picking experts.\n    if len(latest) > max_experts:\n        raise ValueError("More experts than the configured maximum; curate independent sources before scoring")\n    satisfied = min_experts <= len(latest) <= max_experts\n    total_weight = sum(max(0.0, float(weights.get(e, 1.0))) for e in latest) if satisfied else 0.0
    result = {}
    for runner in runners:
        votes = [(expert, rank, conf) for expert, rows in latest.items()
                 for r, rank, conf in rows if r == runner]
        top1 = [(e, rank, conf) for e, rank, conf in votes if rank == 1]
        top3 = [(e, rank, conf) for e, rank, conf in votes if rank <= 3]
        weight_top1 = sum(max(0.0, float(weights.get(e, 1.0))) for e, _, _ in top1)
        result[runner] = {
            "expert_coverage": len(latest),\n            "expert_requirement_satisfied": satisfied,
            "expert_top1_votes": len(top1),
            "expert_top3_votes": len(top3),
            "expert_top1_share": len(top1) / len(latest) if satisfied else None,
            "expert_top3_share": len(top3) / len(latest) if satisfied else None,
            "expert_weighted_top1_share": weight_top1 / total_weight if total_weight else None,
            "expert_mean_confidence": sum(conf for _, _, conf in votes) / len(votes) if satisfied and votes else None,
            "expert_data_missing": not satisfied,
        }
    return result
