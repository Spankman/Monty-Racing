"""Audit extracted article candidates against a frozen race-day field.

Research-only matching. A matching horse is NOT an authenticated tip:
article publication time, race-off time, source/author and page evidence
must be verified separately. Never output an expert blend input CSV.
"""
import argparse
import json
import re
from pathlib import Path
import pandas as pd

KEY = ("meeting", "race", "number")
def norm(value):
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())

def audit(capture_data, scores):
    fields = pd.read_csv(scores, dtype={k: str for k in KEY})
    required = set(KEY + ("horse",))
    if not required.issubset(fields.columns):
        raise ValueError("Field data lacks horse identity columns")
    if fields.duplicated(list(KEY)).any():
        raise ValueError("Duplicate field runner identity")
    results = []
    for article in capture_data.get("articles", []):
        for candidate in article.get("candidates", []):
            record = dict(candidate)
            record["status"] = "UNVERIFIED_NO_BET"
            record["field_match"] = False
            record["reason"] = "No unambiguous matching runner"
            race = candidate.get("race")
            number = candidate.get("number")
            horse = candidate.get("horse_text")
            if race and number and horse:
                matching = fields[(fields.race == str(race)) & (fields.number == str(number))]
                matching = matching[matching.horse.map(norm) == norm(horse)]
                # Without a trustworthy meeting in the article, multiple
                # matching meetings are ambiguous even if horse/number agree.
                if len(matching) == 1:
                    record["field_match"] = True
                    record["meeting_candidate"] = str(matching.iloc[0].meeting)
                    record["reason"] = "Identity matched; provenance and pre-off evidence still unverified"
            results.append(record)
    return {"status": "RESEARCH_ONLY_NO_BET", "verified_tip_count": 0,
            "candidates": results, "field_matches": sum(x["field_match"] for x in results)}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("captures")
    p.add_argument("scores")
    p.add_argument("--output", default="expert_candidate_field_audit.json")
    a = p.parse_args()
    result = audit(json.loads(Path(a.captures).read_text()), a.scores)
    Path(a.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"candidates": len(result["candidates"]),
                      "field_matches": result["field_matches"], "verified_tip_count": 0}))
