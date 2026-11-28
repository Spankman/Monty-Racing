#!/usr/bin/env python3
"""Monty V8 — Simplified Reliable Baseline.
Grok skeleton, transcribed with formatting condensed. NOT production ready.
See HANDOVER.md. Provider and model integrations are intentionally missing.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
log = logging.getLogger("monty_v8")
RESULTS_DIR = Path(os.environ.get("MONTY_RESULTS_DIR", "monty_v8_results"))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
V6_MODEL_PATH = os.environ.get("V6_MODEL_PATH", "monty_v6/frozen_model.pkl")
PRIMARY_PROVIDER = os.environ.get("MONTY_PRIMARY_PROVIDER", "puntersedge")

class Snapshot:
    def __init__(self, data: Dict[str, Any], source: str):
        self.data = data
        self.source = source
        self.captured_at = datetime.now(timezone.utc).isoformat()
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        raw = json.dumps(self.data, sort_keys=True, default=str).encode()
        return hashlib.sha256(raw).hexdigest()

class ScoreResult:
    def __init__(self, race_id: str, runners: List[Dict], status: str = "SCORED"):
        self.race_id = race_id
        self.runners = runners
        self.status = status
        self.model = "V6"

def capture_snapshot(date: str, track: Optional[str] = None, race: Optional[int] = None) -> Optional[Snapshot]:
    log.info("Capturing snapshot | date=%s track=%s race=%s provider=%s", date, track, race, PRIMARY_PROVIDER)
    # TODO: Implement real provider client.
    log.warning("Provider capture not implemented — returning None (DATA_BLOCKED)")
    return None

def validate_snapshot(snapshot: Snapshot, track: Optional[str] = None, race: Optional[int] = None) -> bool:
    if snapshot is None:
        log.error("No snapshot to validate")
        return False
    meetings = snapshot.data.get("meetings", [])
    if not meetings:
        log.error("Snapshot contains no meetings")
        return False
    for meeting in meetings:
        for race_data in meeting.get("races", []):
            runners = race_data.get("runners", [])
            active = [r for r in runners if not r.get("scratched")]
            if len(active) < 2:
                log.error("Race has fewer than 2 active runners")
                return False
            for r in active:
                if not r.get("odds") or r.get("odds") <= 1.0:
                    log.error("Missing or invalid odds for runner %s", r.get("name"))
                    return False
    log.info("Snapshot validation passed | hash=%s", snapshot.hash[:12])
    return True

def score_with_v6(snapshot: Snapshot) -> List[ScoreResult]:
    # TODO: Restore verified archive and call genuine frozen V6 scoring.
    # Safety change from original: disable placeholder market-as-model scoring.
    raise NotImplementedError("Genuine V6 scoring not integrated")

def apply_betting_gates(results: List[ScoreResult]) -> List[ScoreResult]:
    # TODO: Wire existing policy, distinguish daily and single-race requests.
    for result in results:
        result.status = "NO BET"
        for r in result.runners:
            r["selection"] = "NO BET"
    return results

def write_result(command: str, snapshot: Optional[Snapshot], results: List[ScoreResult], status: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = RESULTS_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "command": command, "status": status,
        "captured_at": snapshot.captured_at if snapshot else None,
        "snapshot_hash": snapshot.hash if snapshot else None,
        "provider": PRIMARY_PROVIDER,
        "results": [{"race_id": r.race_id, "status": r.status, "runners": r.runners} for r in results],
    }
    forecast_path = out_dir / "forecast.json"
    forecast_path.write_text(json.dumps(payload, indent=2, default=str))
    receipt = {"timestamp": timestamp, "forecast_sha256": hashlib.sha256(forecast_path.read_bytes()).hexdigest(), "status": status}
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2))
    log.info("Wrote result to %s", out_dir)
    return out_dir

def handle_daily(date: Optional[str] = None):
    date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log.info("RM6 daily | date=%s", date)
    snapshot = capture_snapshot(date)
    if not snapshot or not validate_snapshot(snapshot):
        write_result("RM6", snapshot, [], "DATA_BLOCKED")
        return
    results = score_with_v6(snapshot)
    results = apply_betting_gates(results)
    write_result("RM6", snapshot, results, "NO BET")

def handle_single_race(track: str, race: int, date: Optional[str] = None):
    date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log.info("RM6 single-race | %s R%s | date=%s", track, race, date)
    snapshot = capture_snapshot(date, track=track, race=race)
    if not snapshot or not validate_snapshot(snapshot, track, race):
        write_result(f"RM6 {track} {race}", snapshot, [], "DATA_BLOCKED")
        return
    results = score_with_v6(snapshot)
    results = apply_betting_gates(results)
    write_result(f"RM6 {track} {race}", snapshot, results, "NO BET")

def handle_status():
    # TODO: Read latest request receipt from private archive.
    log.info("Status check (C) — not yet implemented")
    print("Latest result: (placeholder)")

def main():
    parser = argparse.ArgumentParser(description="Monty V8")
    parser.add_argument("command", nargs="?", help="RM6 | RM6 <Track> <Race> | C")
    parser.add_argument("track", nargs="?", help="Track name (single-race)")
    parser.add_argument("race", nargs="?", type=int, help="Race number (single-race)")
    args = parser.parse_args()
    cmd = (args.command or "").upper()
    if cmd == "C":
        handle_status()
    elif cmd == "RM6" and args.track and args.race:
        handle_single_race(args.track, args.race)
    elif cmd == "RM6":
        handle_daily()
    else:
        print("Usage: python monty_v8.py RM6 [Track Race] | C")
        sys.exit(1)

if __name__ == "__main__":
    main()
