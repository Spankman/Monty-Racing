"""Audit-only daily price-ladder preview from research scores.

No race is promoted to a betting recommendation. All rows remain unapproved.
"""
import argparse
from pathlib import Path
import pandas as pd
from monty_single_race_ladder import price_ladder

def preview(scores):
    df=pd.read_csv(scores,dtype={"meeting":str,"race":str,"number":str,"horse":str})
    needed={"meeting","race","number","horse","odds","research_prob","status"}
    if not needed.issubset(df.columns):raise ValueError("Missing required scoring fields")
    if df.empty or not df.status.eq("UNAPPROVED RESEARCH — NO BET").all():
        raise ValueError("Research scores are not valid or not research-only")
    rows=[]
    for (meeting,race),g in df.groupby(["meeting","race"],sort=False):
        ranked=[{"number":r.number,"horse":r.horse,"odds":float(r.odds),"research_prob":float(r.research_prob)} for r in g.itertuples(index=False)]
        ranked.sort(key=lambda r:(-r["research_prob"],str(r["number"])))
        choice=price_ladder(ranked)
        rows.append({"meeting":meeting,"race":race,"research_ladder":choice["bet_type"],
                     "runner_numbers":"-".join(str(r["number"]) for r in choice["selections"]),
                     "status":"UNAPPROVED RESEARCH — NO BET"})
    return pd.DataFrame(rows,columns=["meeting","race","research_ladder","runner_numbers","status"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("scores")
    p.add_argument("--output",default="daily_ladder_research_preview.csv")
    a=p.parse_args()
    preview(a.scores).to_csv(Path(a.output),index=False)
