"""Settle frozen Monty win predictions using independently verified results.

Input predictions must pass monty_prospective_ledger.validate.
Results CSV columns: race_id,number,finish_position,result_verified_at.
Only rows explicitly marked bet_authorised=yes are staked.\nReturns are one-unit win stakes at captured fixed odds, NOT exotic payouts.
"""
import argparse
import csv
import json
from collections import defaultdict
from monty_prospective_ledger import validate, parse_time

def settle(predictions, results):
    validate(predictions)
    indexed = {}
    for row in results:
        key = (row["race_id"], row["number"])
        if key in indexed:
            raise ValueError("duplicate verified result")
        if not row.get("result_verified_at"):
            raise ValueError("missing verification timestamp")
        parse_time(row["result_verified_at"])
        if int(row["finish_position"]) < 1:
            raise ValueError("invalid finish position")
        indexed[key] = row
    totals = defaultdict(lambda: {"bets": 0, "wins": 0, "staked": 0.0, "returned": 0.0})
    for row in predictions:
        result = indexed.get((row["race_id"], row["number"]))
        if result is None:
            continue  # Unverified result is never silently counted as a loss
        if parse_time(result["result_verified_at"]) <= parse_time(row["scheduled_start"]):
            raise ValueError("result verification predates race")
        if str(row.get("bet_authorised", "")).strip().lower() not in ("yes", "true", "1"):
            continue  # Shadow rankings and NO BET are not actual wagers
        t = totals[row["version"]]
        t["bets"] += 1
        t["staked"] += 1
        if int(result["finish_position"]) == 1:
            t["wins"] += 1
            t["returned"] += float(row["fixed_win_odds"])
    for t in totals.values():
        t["profit"] = round(t["returned"] - t["staked"], 4)
        t["roi_pct"] = round(100 * t["profit"] / t["staked"], 2)
        t["returned"] = round(t["returned"], 4)
    return dict(totals)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("predictions_csv")
    p.add_argument("verified_results_csv")
    args = p.parse_args()
    def read(path):
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    print(json.dumps(settle(read(args.predictions_csv), read(args.verified_results_csv)), indent=2))
