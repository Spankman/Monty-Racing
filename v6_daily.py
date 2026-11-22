"""Publish a V6 NO BET report and freeze eligible pre-race research output."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd

from monty_daily_price_ladder import format_daily
from monty_prospective_ledger import parse_time, validate
from run_day import run


def race_key(meeting, number):
    return (" ".join(str(meeting).upper().split()), str(number))


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def provider_card(payload, date):
    fields = {}
    for meeting in payload.get("data", []):
        if str(meeting.get("date", ""))[:10] != date or meeting.get("type") not in ("T", "R"):
            continue
        if meeting.get("country") not in (None, "AU", "NZ"):
            continue
        for race in meeting.get("races", []):
            if race.get("number") is None:
                continue
            key = race_key(meeting.get("venue"), race["number"])
            entries = race.get("runners") or []
            scratches = [str(row["number"]) for row in entries
                         if row.get("is_scratched") is True and row.get("number") is not None]
            unknown = sum(type(row.get("is_scratched")) is not bool for row in entries)
            if key in fields:
                fields[key]["conflicting_identity"] = True
                continue
            fields[key] = dict(country=meeting.get("country"), jump_time=race.get("jump_time"),
                               provider_status=race.get("status"), provider_scratched=scratches,
                               unconfirmed_scratching_count=unknown, conflicting_identity=False)
    return fields


def coverage(date, fixtures, fields, readiness, audit=None):
    expected = set()
    if fixtures:
        if fixtures["date"] != date:
            raise ValueError("Independent fixture list does not match requested card date")
        expected = {race_key(venue, number) for venue, count in fixtures["meetings"].items()
                    for number in range(1, count + 1)}
    assessed = {race_key(row["meeting"], row["race"]): row for row in readiness.get("races", [])}
    skips = {}
    for reason in (audit or {}).get("skipped", []):
        identity, separator, message = reason.partition(": ")
        meeting, race_marker, race = identity.rpartition(" R")
        if separator and race_marker:
            skips[race_key(meeting, race)] = message
    records = []
    for key in sorted(expected | fields.keys() | assessed.keys(), key=lambda k: (k[0], k[1].zfill(5))):
        if key not in fields:
            status, reasons = "SKIPPED", ["missing_from_provider_capture"]
        elif key not in assessed:
            status, reasons = "SKIPPED", [skips.get(key, "provider_field_not_accepted")]
        else:
            status, reasons = "PROVISIONAL", list(assessed[key]["reasons"])
        if key not in expected:
            reasons.append("outside_available_independent_fixture_list")
        field = fields.get(key, {})
        records.append(dict(meeting=key[0], race=key[1], expected=key in expected, **field,
                            independently_verified=False, status=status, decision="NO BET",
                            reasons=reasons))
    return dict(date=date, fixture_scope="available dated meeting/race counts only" if fixtures
                else "no dated independent fixture list available",
                fixture_source=fixtures.get("source") if fixtures else None,
                complete_au_nz_coverage_verified=False, expected=len(expected), provider_races=len(fields),
                independently_verified=0, counts=dict(Counter(row["status"] for row in records)),
                no_bet=len(records), races=records)


def publish(date, intake, assessment, output, *, commit, fixtures=None, clock=None):
    """Score only unique, provably pre-off provider fields; publish NO BET throughout."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    output.mkdir(parents=True, exist_ok=False)
    fields = provider_card(json.loads((intake / "provider_response.json").read_bytes()), date)
    bundle = json.loads((intake / "assessment_bundle.json").read_bytes())
    card = coverage(date, fixtures, fields, assessment, bundle["audit"])
    snapshot = bundle["snapshot"]
    captured = parse_time(bundle["captured_at_utc"])
    card["provider_capture_at_utc"] = captured.isoformat()
    card["provider"] = "Krok Odds API"
    card["provider_capture_sha256"] = sha(intake / "provider_response.json")
    captured_prices = {}
    for row in snapshot["runners"]:
        key = race_key(row["meeting"], row["race"])
        captured_prices.setdefault(key, []).append(dict(
            number=row["number"], fixed_win_odds=row["odds"], source=row["_price_source"]))
    now = clock()
    forward = {}
    for row in card["races"]:
        key = race_key(row["meeting"], row["race"])
        prices = captured_prices.get(key, [])
        row["named_price_counts"] = dict(Counter(p["source"] for p in prices))
        row["named_prices"] = [p for p in prices if p["source"] == "TAB"]
        row["frozen"] = False
        if row["status"] != "PROVISIONAL":
            continue
        # The provider timestamp can rule a race out. It cannot establish TAB verification.
        try:
            jump = parse_time(row.get("jump_time"))
        except (TypeError, ValueError):
            jump = None
        if (jump and captured <= now < jump and 0 <= (now - captured).total_seconds() <= 300
                and row.get("country") in ("AU", "NZ") and not row["conflicting_identity"]
                and prices and all(p["source"] == "TAB" for p in prices)):
            forward[key] = jump
        else:
            row["reasons"].append("freeze_requires_upcoming_unique_field_and_named_fixed_win")
    ledger, shortlists = [], []
    if forward:
        eligible = {name: [row for row in snapshot[name] if race_key(row["meeting"], row["race"]) in forward]
                    for name in ("runners", "races")}
        private_work = intake / "v6_scoring"
        private_work.mkdir()
        selected = private_work / "input.json"
        write_json(selected, dict(date=date, **eligible))
        run(str(selected), date, str(private_work))
        scored = pd.read_csv(private_work / "monty_selections.csv",
                             dtype={name: str for name in ("meeting", "race", "number")})
        decision = clock()
        indexed = {race_key(row["meeting"], row["race"]): row for row in card["races"]}
        for (meeting, number), field in scored.groupby(["meeting", "race"], sort=False):
            key = race_key(meeting, number)
            jump = forward[key]
            if decision >= jump or (decision - captured).total_seconds() > 300:
                indexed[key]["reasons"].append("race_due_or_snapshot_expired_during_scoring")
                continue
            ranked = field.sort_values("monty_prob", ascending=False, kind="stable").to_dict("records")
            indexed[key]["frozen"] = True
            country = indexed[key]["country"]
            for index, runner in enumerate(ranked, 1):
                ledger.append(dict(race_id=f"{date}|{country}|{key[0]}|{number}", version="V6",
                                   meeting=meeting, race=number, number=runner["number"],
                                   horse=runner["horse"], rank=index, captured_at=captured.isoformat(),
                                   scheduled_start=jump.isoformat(), decision_at=decision.isoformat(),
                                   fixed_win_odds=runner["odds"], bookmaker="TAB (Krok attributed)",
                                   win_probability=runner["monty_prob"], bet_authorised=False))
            shortlists.append(dict(meeting=meeting, race=number, classification="Class unverified",
                                   qualified=True, ranked=ranked))
    card["frozen_races"] = len(shortlists)
    write_json(output / "coverage.json", card)
    detail = format_daily(shortlists, details=True) if shortlists else "No pre-race V6 predictions frozen."
    (output / "report.md").write_text(f"# Monty V6 daily — {date}\n\n**NO BET**\n\n{detail}\n",
                                     encoding="utf-8")
    if not ledger:
        return card
    validate(ledger)
    ledger_path = output / "forecast.json"
    model = Path(__file__).parent / "monty_v6/results/frozen_model.json"
    write_json(ledger_path, dict(date=date, model_commit=commit, model_sha256=sha(model),
                                 captured_at=captured.isoformat(), decision_at=decision.isoformat(),
                                 rows=ledger))
    write_json(output / "receipt.json", dict(date=date, model_commit=commit, model_sha256=sha(model),
                 captured_at=captured.isoformat(), decision_at=decision.isoformat(),
                 source_sha256=sha(intake / "provider_response.json"), races=len(shortlists),
                 runners=len(ledger), forecast_sha256=sha(ledger_path), report_sha256=sha(output / "report.md")))
    return card


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
