"""Audit-only daily price-ladder preview from research scores.

No race is promoted to a betting recommendation. All rows remain unapproved.
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from monty_single_race_ladder import price_ladder

def preview(scores):
    df=pd.read_csv(scores,dtype={"meeting":str,"race":str,"number":str,"horse":str})
    needed={"meeting","race","number","horse","odds","research_prob","status"}
    if not needed.issubset(df.columns):raise ValueError("Missing required scoring fields")
    if df.empty or not df.status.eq("UNAPPROVED RESEARCH — NO BET").all():
        raise ValueError("Research scores are not valid or not research-only")
    if df[list(needed)].isna().any().any():
        raise ValueError("Incomplete race identity, prices, or research scores")
    if df.duplicated(["meeting","race","number"]).any():
        raise ValueError("Duplicate saddlecloth in race")
    df["odds"]=pd.to_numeric(df.odds,errors="raise")
    df["research_prob"]=pd.to_numeric(df.research_prob,errors="raise")
    if not np.isfinite(df[["odds","research_prob"]].to_numpy(float)).all() or (df.odds<=1).any() or (df.research_prob<0).any():
        raise ValueError("Invalid odds or probabilities")
    if not df.groupby(["meeting","race"]).research_prob.sum().between(.999999,1.000001).all():
        raise ValueError("Unnormalized race probabilities")
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
