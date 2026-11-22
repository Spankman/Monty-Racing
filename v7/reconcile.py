"""Reconcile Krok with independently sourced TAB fields and bookmaker captures.

Each input is a normalized JSON capture with provider, source_url, published_at,
captured_at, date and races. Race records carry country, race_id, meeting, number,
scheduled_start, classification, going and a complete runners list. Runner
records carry runner_id, number, horse, and scratched. The TAB capture also
carries krok_race_id, tier and, per runner, krok_runner_id from a verified crosswalk.
A normalized bookmaker capture carries country and TAB race_id per race and
TAB runner_id and fixed_win_odds per runner. Each capture receipt identifies
the original raw bytes and the normalized file separately.
"""
import argparse
from datetime import date as calendar_date
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from historical_asof import utc_instant
from v7.eligibility import eligibility


def capture(receipt_path, cutoff):
    receipt = json.loads(receipt_path.read_bytes())
    raw = (receipt_path.parent / receipt["raw_file"]).read_bytes()
    normalized = (receipt_path.parent / receipt["normalized_file"]).read_bytes()
    for content, key in ((raw, "raw_sha256"), (normalized, "normalized_sha256")):
        if hashlib.sha256(content).hexdigest() != receipt[key]:
            raise ValueError(f"Capture digest mismatch: {key}")
    data = json.loads(normalized)
    url = urlsplit(data["source_url"])
    if url.scheme != "https" or not url.hostname or not identity(data["provider"]):
        raise ValueError("Capture source identity missing")
    if not utc_instant(data["published_at"]) <= utc_instant(data["captured_at"]) < cutoff:
        raise ValueError("Capture was not available before decision")
    data["raw_sha256"] = receipt["raw_sha256"]
    data["normalized_sha256"] = receipt["normalized_sha256"]
    return data


def identity(value):
    return isinstance(value, str) and bool(value) and value == value.strip()


def unique_index(records, *keys):
    index = {}
    for record in records:
        key = tuple(record.get(name) for name in keys)
        if not all(map(identity, key)) or key in index:
            raise ValueError(f"Invalid or duplicate identity for {keys}: {key}")
        index[key] = record
    return index


def odds_valid(value):
    return type(value) in (float, int) and math.isfinite(value) and value > 1


def evidence_fields(source):
    keys = ("provider", "source_url", "published_at", "captured_at", "raw_sha256",
            "normalized_sha256")
    return {key: source[key] for key in keys}


def reconcile(krok, fixtures, quotes, *, date, decision_at, allow_restricted=False):
    """Produce separate accepted fields and traceable rejection records."""
    calendar_date.fromisoformat(date)
    cutoff = utc_instant(decision_at)
    sources = (krok, fixtures, quotes)
    providers = [source["provider"].casefold() for source in sources]
    if providers[0] != "krok" or providers[0] in providers[1:] or providers[2] in ("", "best_win", "fixed_win"):
        raise ValueError("Independent TAB and named bookmaker evidence required")
    for source in sources:
        if source["date"] != date:
            raise ValueError("Dated capture mismatch")
        if not utc_instant(source["published_at"]) <= utc_instant(source["captured_at"]) < cutoff:
            raise ValueError("Capture was not available before decision")

    provider_races = unique_index(krok["races"], "race_id")
    tab_races = unique_index(fixtures["races"], "country", "race_id")
    price_races = unique_index(quotes["races"], "country", "race_id")
    unique_index([r for r in tab_races.values() if r.get("krok_race_id")],
                 "krok_race_id")
    accepted, audit = [], []
    matched = set()
    for key, tab in tab_races.items():
        provider_id = tab.get("krok_race_id")
        provider = provider_races.get((provider_id,))
        matched.add(provider_id)
        reason = eligibility(tab["country"], tab.get("classification"),
                             class_verified=tab.get("class_verified"),
                             allow_restricted=allow_restricted)
        status = "PROVISIONAL"
        if reason == "restricted race class":
            status = "EXCLUDED"
        elif tab.get("status") in ("ABANDONED", "CANCELLED"):
            status, reason = "EXCLUDED", "official fixture void"
        elif provider is None:
            status, reason = "MISSING", "Krok race missing"
        elif reason is None:
            try:
                runners = verify_field(tab, provider, price_races.get(key), cutoff)
            except (KeyError, TypeError, ValueError, OverflowError) as error:
                reason = str(error)
            else:
                status = "VERIFIED"
                accepted.append({
                    **{k: v for k, v in tab.items() if k != "runners"},
                    "runners": runners, "decision_at": decision_at,
                    "bookmaker": quotes["provider"],
                    "scratched_runners": [r for r in tab["runners"] if r["scratched"]],
                })
        audit.append(dict(country=key[0], race_id=key[1], krok_race_id=provider_id,
                          meeting=tab.get("meeting"), number=tab.get("number"),
                          status=status, reason=reason))
    for (race_id,), race in provider_races.items():
        if race_id not in matched:
            audit.append(dict(krok_race_id=race_id, country=race.get("country"),
                              meeting=race.get("meeting"), number=race.get("number"),
                              status="PROVISIONAL", reason="independent TAB fixture missing"))
    return dict(date=date, decision_at=decision_at, sources={
        role: evidence_fields(source)
        for role, source in zip(("krok", "fixtures", "fixed_win"), sources)
    }, verified=accepted, audit=audit)


def verify_field(tab, provider, prices, cutoff):
    for key in ("country", "number", "classification", "going"):
        if not identity(tab[key]) or tab[key] != provider.get(key):
            raise ValueError(f"Krok and TAB disagree or lack evidence for {key}")
    if tab.get("status") not in ("OPEN", "SCHEDULED") or provider.get("status") not in ("OPEN", "SCHEDULED"):
        raise ValueError("Pre-race status unresolved")
    if tab.get("tier") not in ("metro", "provincial", "country"):
        raise ValueError("TAB meeting tier unresolved")
    start = utc_instant(tab["scheduled_start"])
    if start <= cutoff or start != utc_instant(provider["scheduled_start"]):
        raise ValueError("Jump time has passed or disagrees with TAB")
    if prices is None:
        raise ValueError("Named bookmaker field missing")
    official = unique_index(tab["runners"], "krok_runner_id")
    unique_index(tab["runners"], "runner_id")
    unique_index(tab["runners"], "number")
    offered = unique_index(provider["runners"], "runner_id")
    if official.keys() != offered.keys():
        raise ValueError("Krok and TAB runner sets differ")
    priced = unique_index(prices["runners"], "runner_id")
    active = []
    for key, runner in official.items():
        provider_runner = offered[key]
        if type(runner.get("scratched")) is not bool or any(
            runner.get(k) != provider_runner.get(k) for k in ("number", "horse", "scratched")
        ) or type(provider_runner.get("scratched")) is not bool:
            raise ValueError("Krok and TAB runner or scratching disagreement")
        if not identity(runner.get("horse")):
            raise ValueError("Runner name missing")
        if runner["scratched"]:
            continue
        quote = priced.get((runner["runner_id"],), {})
        odds = quote.get("fixed_win_odds")
        if not odds_valid(odds):
            raise ValueError("Active runner missing named fixed-win odds")
        active.append(dict(runner, fixed_win_odds=odds))
    if len(active) < 2 or priced.keys() != {(r["runner_id"],) for r in active}:
        raise ValueError("Bookmaker and TAB active fields differ")
    return active


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("krok", "fixtures", "quotes", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--decision-at", required=True)
    parser.add_argument("--allow-restricted", action="store_true")
    args = parser.parse_args()
    cutoff = utc_instant(args.decision_at)
    inputs = [capture(path, cutoff) for path in (args.krok, args.fixtures, args.quotes)]
    result = reconcile(*inputs, date=args.date, decision_at=args.decision_at,
                       allow_restricted=args.allow_restricted)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
