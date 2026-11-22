"""Freeze one research-only race from independently reviewed, fresh capture receipts."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from historical_asof import utc_instant
from v7.reconcile import capture, reconcile
from v7.shadow import freeze


def attempt(*, date, country, race_id, krok, fixtures, quotes, scored, output, now=None):
    now = now or datetime.now(timezone.utc)
    output.mkdir(parents=True, exist_ok=False)
    audit = dict(status="SKIPPED — NO BET", date=date, country=country,
                 race_id=race_id, decision_at=now.isoformat())
    try:
        sources = [capture(path, now) for path in (krok, fixtures, quotes)]
        card = reconcile(*sources, date=date, decision_at=now.isoformat())
        field = next((r for r in card["verified"]
                      if (r["country"], r["race_id"]) == (country, race_id)), None)
        if field is None:
            reason = next((r["reason"] for r in card["audit"]
                           if (r["country"], r.get("race_id")) == (country, race_id)),
                          "Race absent from independent fixture")
            raise ValueError(reason)
        start = utc_instant(field["scheduled_start"])
        window_open = start - timedelta(minutes=5)
        cutoff = start - timedelta(minutes=1)
        if not window_open < now <= cutoff:
            raise ValueError("Decision must be between five and one minutes before scheduled jump")
        if any(utc_instant(source["captured_at"]) < window_open for source in sources):
            raise ValueError("Stale provider, scratching or fixed-win capture")
        payload = json.loads(scored.read_bytes())
        rows = payload["rows"]
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            raise ValueError("Expected a list of scored runner records")
        by_id = {r["runner_id"]: r for r in rows}
        expected = {runner["runner_id"]: runner["fixed_win_odds"] for runner in field["runners"]}
        prices = {key: row["odds"] for key, row in by_id.items()}
        if len(by_id) != len(rows) or prices != expected:
            raise ValueError("Scored runners or odds differ from fresh evidence")
        quote_source = card["sources"]["fixed_win"]
        expected_time = utc_instant(quote_source["captured_at"])
        if any(r["race_id"] != race_id or r.get("country") != country
               or utc_instant(r["scheduled_start_utc"]) != start
               or utc_instant(r["odds_captured_at_utc"]) != expected_time
               or r["source_url"] != quote_source["source_url"] for r in rows):
            raise ValueError("Scored race or quote provenance differs from fresh evidence")
        evidence = dict(cutoff_utc=cutoff.isoformat(), sources=card["sources"],
                        scratched_runners=field["scratched_runners"])
        receipt = freeze(rows, output / "forecast.json", payload["models"], now,
                         fresh_evidence=evidence)
        audit.update(status="FROZEN — NO BET", receipt=receipt)
    except (OSError, KeyError, TypeError, ValueError) as error:
        audit["reason"] = str(error)
    (output / "attempt.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--country", choices=("AU", "NZ"), required=True)
    parser.add_argument("--race-id", required=True)
    for name in ("krok", "fixtures", "quotes", "scored", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    audit = attempt(**vars(parser.parse_args()))
    print(audit["status"])
    if "reason" in audit:
        parser.exit(1, audit["reason"] + "\n")
    # The attempt audit embeds the forecast receipt for later settlement.
    print(audit["receipt"]["sha256"])


if __name__ == "__main__":
    main()
