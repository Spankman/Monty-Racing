"""Select a single race from a genuine Monty research score CSV.

This is a diagnostic view, NOT a betting recommendation. No fabricated runners.
"""
import argparse
import csv
import json
from pathlib import Path

def select(path, track, race):
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    matches=[r for r in rows if r["meeting"].strip().casefold()==track.strip().casefold() and str(r["race"]).strip()==str(race)]
    if not matches:
        raise ValueError(f"Race not found in scored data: {track} R{race}")
    if any(r.get("status")!="UNAPPROVED RESEARCH — NO BET" for r in matches):
        raise ValueError("Unexpected scoring status; refusing to label as approved")
    if len({r["number"] for r in matches})!=len(matches):
        raise ValueError("Duplicate saddlecloth numbers")
    for r in matches:
        r["research_prob"]=float(r["research_prob"])
        r["edge"]=float(r["edge"])
    matches.sort(key=lambda r:(-r["research_prob"],int(r["number"])))
    return {"meeting":matches[0]["meeting"],"race":str(race),
            "status":"NO BET — UNAPPROVED RESEARCH",
            "source":"research_frozen_linear_replay.py",
            "runners":[{"number":r["number"],"horse":r["horse"],
                        "research_probability":r["research_prob"],
                        "edge":r["edge"]} for r in matches]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("scores")
    p.add_argument("--track",required=True)
    p.add_argument("--race",required=True,type=int)
    p.add_argument("--output",default="single_race_research.json")
    a=p.parse_args()
    result=select(a.scores,a.track,a.race)
    Path(a.output).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"race":result["meeting"]+" R"+result["race"],
                      "runners":len(result["runners"]),"status":result["status"]}))

if __name__=="__main__":main()
