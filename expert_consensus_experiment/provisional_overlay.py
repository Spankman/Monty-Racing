"""Provisional V7 research overlay; fixed neutral weights, NOT fitted or calibrated.

Joins sourced editorial observations to V6 runner predictions by meeting/race/
saddlecloth, never by horse name alone. Does not replace V6 probabilities.
No unsupported expert coverage claims; overlapping publishers not independent.
"""
import json
from collections import defaultdict
from pathlib import Path
from integrations.race_exclusions import betting_eligibility

def norm_meeting(value):
    x=str(value).lower().replace("-lakeside","").replace(" park","")
    return "".join(c for c in x if c.isalnum())

def overlay(v6_races, observations, classifications=None):
    classifications=classifications or {"races":[]}
    meta={}\n    for item in classifications["races"]:\n        key=(norm_meeting(item["meeting"]),int(item["race"]))\n        if key in meta:\n            raise ValueError("Duplicate race classification: "+str(key))\n        meta[key]=item
    votes=defaultdict(list)
    for item in observations["selections"]:
        key=(norm_meeting(item["meeting"]),int(item["race"]),str(item["number"]))
        votes[key].append(item)
    results=[]
    for race in v6_races:
        # Only unambiguous meeting/race keys can be joined.
        if "meeting" in race and "race" in race:
            meeting,number=race["meeting"],int(race["race"])
        else:
            raw=str(race["race_id"]).split("|")
            if len(raw)!=2:
                raise ValueError("Unrecognized V6 race ID")
            meeting,number=raw[0],int(raw[1])
        key=(norm_meeting(meeting),number)
        category=meta.get(key,{"race_name":str(meeting)+" R"+str(number)})
        eligibility=betting_eligibility(category)
        candidates=[]
        for runner in race["runners"]:
            cloth=str(runner.get("runner_number",runner.get("number","")))
            if not cloth or cloth in seen_cloths:\n                raise ValueError("Missing or duplicate runner number: "+str(key))\n            seen_cloths.add(cloth)\n            matches=votes.get((*key,cloth),[])
            # Deduplicate repeated mentions from same editorial voice.
            sources=sorted({v["source"] for v in matches})
            candidates.append({
                "number":cloth,"horse":runner.get("runner_name",runner.get("horse")),
                "v6_win_probability":runner.get("win_probability",runner.get("monty_prob")),
                "expert_mentions":len(sources),"expert_sources":sources,\n                "verified_independent_sources":[],
                "provisional_expert_weight":1.0 if sources else 0.0,
                "v7_win_probability":None,
                "status":"UNFITTED_RESEARCH_ONLY"})
        results.append({"meeting":meeting,"race":number,
                        "betting_eligibility":eligibility,\n                        "race_metadata_verified":key in meta,
                        "runners":candidates})
    return {"status":"UNFITTED_V7_RESEARCH_OVERLAY","date":observations["date"],
            "weights":"equal provisional descriptive only; no probability adjustment",
            "races":results}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--v6-predictions",required=True)
    p.add_argument("--observations",required=True)
    p.add_argument("--race-metadata",default="")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    result=overlay(load(args.v6_predictions)["races"],load(args.observations),
                   load(args.race_metadata) if args.race_metadata else None)
    Path(args.output).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"race_count":len(result["races"])}))

if __name__=="__main__":
    main()
