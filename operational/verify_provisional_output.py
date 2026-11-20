"""Fail-closed audit of provisional Monty outputs; never authorises bets.

Usage: python operational/verify_provisional_output.py OUTPUT_DIRECTORY
"""
import argparse
import csv
import json
import math
from pathlib import Path


def verify(directory):
    root = Path(directory)
    record = json.loads((root / "prediction_record.json").read_text())
    provenance = json.loads((root / "snapshot_provenance.json").read_text())
    for name, obj in (("prediction record", record), ("provenance", provenance)):
        if obj.get("betting_authorised") is not False:
            raise ValueError(f"{name}: betting must be explicitly unauthorised")
    for key in ("pre_off_proven", "independent_field_verification_proven", "artifact_integrity_verified"):
        if record.get(key) is not False:
            raise ValueError(f"prediction record: {key} must be false")
    if provenance.get("independent_field_verification_proven") is not False:
        raise ValueError("provenance: independent verification cannot be claimed")
    if record.get("status") != "PROVISIONAL_OPERATIONAL_V6":
        raise ValueError("Unexpected model status")
    fields = {}
    with (root / "operational_predictions.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        needed = {"race_id", "number", "horse", "odds", "monty_prob", "market_prob", "betting_authorised"}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError("Missing mandatory prediction columns")
        count = 0
        restricted_column = "research_only_restricted_race" in (reader.fieldnames or [])
        unknown_column = "race_classification_unknown" in (reader.fieldnames or [])
        for row in reader:
            if row["betting_authorised"].strip().lower() not in ("false", "0"):
                raise ValueError("A runner is marked betting-authorised")
            if restricted_column and row["research_only_restricted_race"].strip().lower() not in ("true", "false", "1", "0"):
                raise ValueError("Invalid research-only restriction flag")
            if unknown_column and row["race_classification_unknown"].strip().lower() not in ("true", "false", "1", "0"):
                raise ValueError("Invalid unknown race classification flag")
            rid = row["race_id"]
            if not rid or not row["number"] or not row["horse"]:
                raise ValueError("Missing race or runner identity")
            odds = float(row["odds"])
            p = float(row["monty_prob"])
            market = float(row["market_prob"])
            if not all(map(math.isfinite, (odds, p, market))) or odds <= 1 or not 0 < p < 1 or not 0 < market < 1:
                raise ValueError("Invalid odds or probabilities")
            group = fields.setdefault(rid, {"sum": 0.0, "market_sum": 0.0, "runners": set()})
            if row["number"] in group["runners"]:
                raise ValueError("Duplicate saddlecloth in output")
            if restricted_column:
                restricted = row["research_only_restricted_race"].strip().lower() in ("true", "1")
                if "restricted" in group and group["restricted"] != restricted:
                    raise ValueError("Inconsistent restricted-race flags within race")
                group["restricted"] = restricted
            if unknown_column:
                unknown = row["race_classification_unknown"].strip().lower() in ("true", "1")
                if "unknown" in group and group["unknown"] != unknown:
                    raise ValueError("Inconsistent unknown classification flags within race")
                group["unknown"] = unknown
            group["runners"].add(row["number"])
            group["sum"] += p
            group["market_sum"] += market
            count += 1
    if not fields or count != record.get("runner_count") or len(fields) != record.get("race_count"):
        raise ValueError("Prediction counts do not match record")
    for race, group in fields.items():
        if len(group["runners"]) < 2 or not math.isclose(group["sum"], 1.0, abs_tol=1e-6) or not math.isclose(group["market_sum"], 1.0, abs_tol=1e-6):
            raise ValueError(f"Probabilities or field size invalid for {race}")
    restricted_count = sum(bool(group.get("restricted", False)) for group in fields.values())
    unknown_count = sum(bool(group.get("unknown", False)) for group in fields.values())
    return {"status": "PROVISIONAL_AUDIT_PASSED", "races": len(fields), "runners": count,
            "restricted_flat_research_races": restricted_count, "unknown_classification_races": unknown_count, "betting_authorised": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    args = parser.parse_args()
    print(json.dumps(verify(args.directory), indent=2))
