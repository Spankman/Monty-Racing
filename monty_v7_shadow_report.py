"""Human-readable, clearly unapproved V7 shadow ranks from genuine model output."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

REQUIRED = {"meeting", "race", "number", "horse", "odds", "v7_shadow_prob", "v7_status"}

def render(source):
    with open(source, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError("Missing required V7 shadow fields")
        rows = list(reader)
    if not rows:
        raise ValueError("No V7 shadow scores")
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["meeting"].strip(), row["race"].strip(), row["number"].strip())
        if not all(key) or not row["horse"].strip():
            raise ValueError("Incomplete runner identity")
        if key in seen:
            raise ValueError("Duplicate runner identity")
        seen.add(key)
        if row["v7_status"] != "UNAPPROVED V7 SHADOW — NO BET":
            raise ValueError("Unexpected betting status")
        p, odds = float(row["v7_shadow_prob"]), float(row["odds"])
        if not (0 <= p <= 1 and 1 < odds < float("inf")):
            raise ValueError("Invalid probability or odds")
        row["_p"], row["_odds"] = p, odds
        groups[key[:2]].append(row)
    lines = ["# Monty V7 — experimental shadow ranks", "",
             "**RESEARCH ONLY — NO BET.** These are genuine V7 shadow output ranks, "
             "not an independently validated V7 betting model or betting tips.", "",
             "No fabricated roughies or value bets are supplied. "
             "Ranks are provisional and may use imputed features.", ""]
    for (meeting, race), runners in sorted(groups.items()):
        total = sum(r["_p"] for r in runners)
        if abs(total - 1) > 0.0001:
            raise ValueError("Race probabilities do not sum to one")
        lines += [f"## {meeting} — Race {race}", ""]
        for rank, r in enumerate(sorted(runners, key=lambda x: (-x["_p"], x["number"])), 1):
            lines.append(f'{rank}. #{r["number"]} {r["horse"]} — '
                         f'V7 shadow {r["_p"]:.1%}; quoted win odds ${r["_odds"]:.2f}')
        lines += ["", "**Decision: NO BET — research only.**", ""]
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--output", default="v7_shadow_report.md")
    args = p.parse_args()
    Path(args.output).write_text(render(args.source), encoding="utf-8")

if __name__ == "__main__":
    main()
