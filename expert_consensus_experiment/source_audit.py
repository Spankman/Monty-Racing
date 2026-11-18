"""Audit manually captured expert tips before admitting them to consensus.

No scraping, fabricated timestamps or implied permission to reuse data.
"""
from collections import defaultdict
from urllib.parse import urlparse
from .expert_consensus import utc

def audit_tips(records, cutoff, min_experts=5, max_experts=20):
    """Return (eligible_records, report). Independence is keyed by analyst_origin_id.

    Every tip must identify an original analyst, a source URL, and its publication time.
    The same original analyst republished across sites counts once.
    Conflicting duplicated records are rejected rather than cherry-picked.
    """
    if not 1 <= min_experts <= max_experts:
        raise ValueError("Invalid thresholds")
    end = utc(cutoff)
    rejected = []
    groups = defaultdict(list)
    for i, row in enumerate(records):
        try:
            for key in ("race_id", "runner_id", "expert_id", "analyst_origin_id", "source_url", "published_at", "rank"):
                if not row.get(key) and row.get(key) != 0:
                    raise ValueError("missing " + key)
            url = urlparse(row["source_url"])
            if url.scheme not in ("https", "http") or not url.netloc:
                raise ValueError("invalid source URL")
            stamp = utc(row["published_at"])
            if stamp > end:
                raise ValueError("published after cutoff")
            rank = int(row["rank"])
            if rank < 1 or str(rank) != str(row["rank"]):
                raise ValueError("invalid rank")
            groups[(row["race_id"], str(row["analyst_origin_id"]))].append((stamp, row))
        except (TypeError, ValueError, KeyError) as e:
            rejected.append({"index": i, "reason": str(e)})
    eligible = []
    coverage = {}
    for (race, origin), versions in groups.items():
        latest_time = max(t for t, _ in versions)
        latest = [r for t, r in versions if t == latest_time]
        unique = {}
        for row in latest:
            rank = int(row["rank"])
            runner = row["runner_id"]
            if rank in unique and unique[rank] != runner:
                rejected.append({"race": race, "origin": origin, "reason": "conflicting syndicated rank"})
                unique = None
                break
            unique[rank] = runner
        if unique is None or len(set(unique.values())) != len(unique):
            rejected.append({"race": race, "origin": origin, "reason": "duplicate runner"})
            continue
        for rank, runner in sorted(unique.items()):
            exemplar = next(r for r in latest if int(r["rank"]) == rank and r["runner_id"] == runner)
            eligible.append({**exemplar, "expert_id": origin})
        coverage.setdefault(race, set()).add(origin)
    report = {
        "races": {race: {"independent_experts": len(origins),
                         "feature_available": min_experts <= len(origins) <= max_experts}
                  for race, origins in coverage.items()},
        "rejected": rejected,
        "eligible_rows": len(eligible),
    }
    return eligible, report
