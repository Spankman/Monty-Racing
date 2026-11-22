"""Point-in-time numeric evidence for Monty's research and model adapters."""
import datetime as dt
import math
from collections.abc import Mapping


def utc_instant(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO-8601 string with timezone")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone required")
    return parsed.astimezone(dt.timezone.utc)


def verified_release(observed, available, cutoff):
    """Return the release time only for evidence strictly before decision."""
    observed, available = utc_instant(observed), utc_instant(available)
    if not observed <= available < cutoff:
        raise ValueError("Evidence unavailable at decision or chronology invalid")
    return available


def _identity(value):
    if isinstance(value, str) and value.strip() and value == value.strip():
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return None


def _key(row):
    """Namespace optional event and provider identities without implicit fallback."""
    runner = _identity(row.get("runner_id"))
    scope = tuple(_identity(row.get(name)) for name in ("country", "namespace", "race_id"))
    if runner is None or any(
        name in row and identity is None
        for name, identity in zip(("country", "namespace", "race_id"), scope)
    ):
        return None
    return (*scope, runner)


def join_asof(runners, history, *, cutoff_utc, feature_names, provenance=None):
    """Join earlier finite observations by exact identity, ignoring unverified supplied values.

    Scope keys country, namespace and race_id must match when used. The caller
    establishes identity and source authenticity. Malformed rows stay missing.
    Latest-release ties remain missing. Optional provenance receives an entry
    per joined feature with the source and original timestamps.
    """
    cutoff = utc_instant(cutoff_utc)
    allowed = set(feature_names)
    output = [{k: v for k, v in row.items() if k not in allowed} for row in runners]
    keys = {_key(row) for row in output} - {None}
    candidates = {}
    for entry in history:
        if not isinstance(entry, Mapping):
            continue
        key = _key(entry)
        feature = entry.get("feature")
        value = entry.get("value")
        source = entry.get("source")
        if key not in keys or not isinstance(feature, str) or feature not in allowed:
            continue
        if not isinstance(source, str) or not source.strip():
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        try:
            if not math.isfinite(value):
                continue
            available = verified_release(entry.get("observed_at"), entry.get("available_at"), cutoff)
        except (ValueError, OverflowError):
            continue
        slot = (key, feature)
        previous = candidates.get(slot)
        if previous is None or available > previous[0]:
            candidates[slot] = (available, entry)
        elif available == previous[0]:
            candidates[slot] = (available, None)
    for result in output:
        key = _key(result)
        for feature in allowed - result.keys():
            _, entry = candidates.get((key, feature), (None, None))
            if entry is None:
                continue
            result[feature] = entry["value"]
            if provenance is not None:
                receipt_fields = (
                    "country", "namespace", "race_id", "runner_id", "feature",
                    "source", "observed_at", "available_at",
                )
                provenance.append({name: entry[name] for name in receipt_fields if name in entry})
    return output
