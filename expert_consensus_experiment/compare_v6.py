"""Join frozen Monty V6 research scores with independently audited expert consensus.

No fitted fusion weights exist yet: this emits a side-by-side diagnostic,
never a claimed combined model probability or betting recommendation.
"""
import argparse
import csv
import json
from collections import defaultdict
from .source_audit import audit_tips
from .expert_consensus import consensus_features

def compare(v6_rows, tip_rows, cutoff, min_experts=5, max_experts=20):
    clean, audit = audit_tips(tip_rows, cutoff, min_experts, max_experts)
    grouped = defaultdict(list)
    for row in v6_rows:
        key = str(row["meeting"]).strip().upper() + "|" + str(row["race"]).strip()
        grouped[key].append(row)
    output = []
    for race, rows in grouped.items():
        ids = [str(r["number"]).strip() for r in rows]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate runner number in " + race)
        # Tips must use the same canonical meeting|race and saddlecloth identifiers.
        relevant = [{**t, "runner_id": str(t["runner_id"]).strip()}
                    for t in clean if t["race_id"] == race]
        features = consensus_features(race, ids, relevant, cutoff,
                                      min_experts=min_experts, max_experts=max_experts)
        for row in rows:
            runner = str(row["number"]).strip()
            f = features[runner]
            output.append({
                "race_id": race,
                "number": runner,
                "horse": row["horse"],
                "v6_probability": float(row["monty_prob"]),
                "v6_feature_coverage": float(row.get("feature_coverage", 0)),
                "expert_coverage": f["expert_coverage"],
                "expert_requirement_satisfied": f["expert_requirement_satisfied"],
                "expert_top1_share": f["expert_top1_share"],
                "expert_top3_share": f["expert_top3_share"],
                "status": "RESEARCH_ONLY_UNTRAINED_FUSION",
            })
    return output, audit

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--v6", required=True, help="V6 race_day.py scored CSV")
    p.add_argument("--tips", required=True, help="JSON list of audited source records")
    p.add_argument("--cutoff", required=True, help="ISO timestamp with timezone")
    p.add_argument("--output", default="v7_comparison.json")
    args = p.parse_args()
    with open(args.v6, newline="", encoding="utf-8") as f:
        v6 = list(csv.DictReader(f))
    with open(args.tips, encoding="utf-8") as f:
        tips = json.load(f)
    rows, audit = compare(v6, tips, args.cutoff)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "audit": audit}, f, indent=2)
    print(json.dumps({"runners": len(rows), "races": len({r["race_id"] for r in rows}),
                      "consensus_eligible_races": len({r["race_id"] for r in rows if r["expert_requirement_satisfied"]}),
                      "status": "RESEARCH_ONLY_UNTRAINED_FUSION"}))

if __name__ == "__main__":
    main()
