"""Validate immutable, pre-race Monty prediction records before settlement."""
import csv
from datetime import datetime, timezone

REQUIRED = ("race_id", "version", "meeting", "race", "number", "horse",
            "captured_at", "scheduled_start", "fixed_win_odds", "win_probability")

def parse_time(value):
    if not isinstance(value, str) or not (value.endswith("Z") or
        (len(value) >= 6 and value[-6] in "+-" and value[-3] == ":")):
        raise ValueError("timezone-aware timestamp required")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def validate(records):
    seen = set()
    for row in records:
        missing = [k for k in REQUIRED if row.get(k) in (None, "")]
        if missing:
            raise ValueError("missing fields: " + ", ".join(missing))
        if parse_time(row["captured_at"]) >= parse_time(row["scheduled_start"]):
            raise ValueError("prediction must be captured before scheduled start")
        if row["version"] not in ("V6", "V7"):
            raise ValueError("unknown model version")
        if float(row["fixed_win_odds"]) <= 1:
            raise ValueError("invalid fixed win odds")
        if not 0 <= float(row["win_probability"]) <= 1:
            raise ValueError("invalid probability")
        key = (row["race_id"], row["version"], row["number"])
        if key in seen:
            raise ValueError("duplicate runner prediction")
        seen.add(key)
    return len(seen)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")
    args = p.parse_args()
    with open(args.csv_path, newline="", encoding="utf-8") as f:
        print("Validated pre-race records:", validate(csv.DictReader(f)))
