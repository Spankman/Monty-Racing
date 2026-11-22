"""Strict as-of historical feature join for Monty V6 research.

No historical features are inferred. Inputs must contain provider-backed values
and explicit timestamps. A missing or ambiguous match remains missing.
"""
import datetime as dt
import math


def _instant(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO-8601 string with timezone")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone required")
    return parsed.astimezone(dt.timezone.utc)


def join_asof(runners, history, *, cutoff_utc, feature_names):
    """Return copies of runner rows enriched only with eligible history.

    History records require stable runner_id, feature, value, observed_at,
    available_at and source. Both timestamps must be strictly before cutoff.
    Multiple eligible records for a runner/feature are rejected if the latest
    available timestamp is tied; no arbitrary selection is made.
    """
    cutoff = _instant(cutoff_utc)
    allowed = set(feature_names)
    candidates = {}
    for entry in history:
        required = ("runner_id", "feature", "value", "observed_at", "available_at", "source")
        if any(entry.get(k) is None for k in required):
            continue
        feature = entry["feature"]
        value = entry["value"]
        if feature not in allowed or not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            continue
        if not str(entry["source"]).strip():
            continue
        observed = _instant(entry["observed_at"])
        available = _instant(entry["available_at"])
        if observed >= cutoff or available >= cutoff or available < observed:
            continue
        key = (str(entry["runner_id"]), feature)
        candidates.setdefault(key, []).append((available, observed, value))
    selected = {}
    for key, values in candidates.items():
        values.sort(reverse=True, key=lambda v: (v[0], v[1]))
        if len(values) > 1 and values[0][:2] == values[1][:2]:
            continue  # ambiguous duplicate provenance: do not choose a value
        selected[key] = values[0][2]
    output = []
    for row in runners:
        result = dict(row)
        runner_id = row.get("runner_id")
        if runner_id is not None:
            for feature in allowed:
                if feature not in result and (str(runner_id), feature) in selected:
                    result[feature] = selected[(str(runner_id), feature)]
        output.append(result)
    return output
