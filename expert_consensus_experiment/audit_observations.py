"""Audit sourced V7 expert observations without inventing votes or predictions.

Usage: python -m expert_consensus_experiment.audit_observations \
  expert_consensus_experiment/observations/2026-11-18.json
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from integrations.race_exclusions import betting_eligibility

def audit(document):
    grouped=defaultdict(list)
    for item in document["selections"]:
        for key in ("meeting","race","number","horse","source","url"):
            if not item.get(key):
                raise ValueError("Missing observation field: "+key)
        if not str(item["url"]).startswith("https://"):
            raise ValueError("Source URL must be HTTPS")
        grouped[(str(item["meeting"]),int(item["race"]))].append(item)
    races=[]
    for (meeting,race),items in sorted(grouped.items()):
        # One editorial source can vote once per race. Do not count syndication as independence.
        unique_sources={i["source"] for i in items}
        exclusions={i.get("exclusion") for i in items if i.get("exclusion")}
        recognized={"MAIDEN","TWO_YEAR_OLD","HURDLE"}
        if exclusions-recognized:
            raise ValueError("Unknown exclusion")
        metadata={"is_maiden":"MAIDEN" in exclusions,
                  "is_two_year_old":"TWO_YEAR_OLD" in exclusions,
                  "is_hurdle":"HURDLE" in exclusions} if exclusions else {"race_name":f"{meeting} R{race}"}
        eligibility=betting_eligibility(metadata)
        races.append({"meeting":meeting,"race":race,"observations":len(items),
                      "named_editorial_sources":len(unique_sources),
                      "independence_verified":False,
                      "expert_consensus_eligible":False,
                      "betting_eligibility":eligibility,
                      "candidates":[{"number":i["number"],"horse":i["horse"],
                                     "source":i["source"],"url":i["url"]} for i in items]})
    return {"date":document["date"],"status":"EVIDENCE_AUDIT_ONLY_NOT_V7_MODEL",
            "race_count":len(races),"races":races}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("observations")
    p.add_argument("--output",default="")
    args=p.parse_args()
    result=audit(json.loads(Path(args.observations).read_text(encoding="utf-8")))
    data=json.dumps(result,indent=2)+"\n"
    if args.output:
        Path(args.output).write_text(data,encoding="utf-8")
    else:
        print(data)

if __name__=="__main__":
    main()
