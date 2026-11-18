"""Strict result-matched comparison for frozen paired Monty probabilities.

Input CSV predictions: meeting,race,number,horse,control_prob,monty_prob
Input CSV outcomes: meeting,race,number,horse,finish_position,source_url
Requires complete active fields, one winner per race, and sourced results.
No live betting/ROI claims and no mutation of frozen pre-race predictions.
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd

KEY=["meeting","race","number","horse"]

def evaluate(predictions,outcomes):
    p=predictions.copy();o=outcomes.copy()
    for label,df,cols in [("predictions",p,KEY+["control_prob","monty_prob"]),("outcomes",o,KEY+["finish_position","source_url"])]:
        if not set(cols).issubset(df.columns):raise ValueError(label+" missing required columns")
        for col in KEY:df[col]=df[col].astype(str).str.strip()
        if df.duplicated(KEY[:3]).any():raise ValueError(label+" duplicate runner")
    if o[["finish_position","source_url"]].isna().any().any() or o.source_url.astype(str).str.strip().eq("").any() or not o.source_url.astype(str).str.startswith("https://").all():
        raise ValueError("Results require valid provenance")
    merged=p.merge(o,on=KEY,how="outer",indicator=True,validate="one_to_one")
    if not merged._merge.eq("both").all():raise ValueError("Outcome identity/field mismatch")
    merged=merged.drop(columns="_merge")
    merged["finish_position"]=pd.to_numeric(merged.finish_position,errors="raise")
    if not np.isfinite(merged.finish_position).all() or merged.finish_position.lt(1).any():raise ValueError("Invalid finish position")
    for col in ["control_prob","monty_prob"]:
        merged[col]=pd.to_numeric(merged[col],errors="raise")
        if not np.isfinite(merged[col]).all() or merged[col].le(0).any() or merged[col].gt(1).any():raise ValueError("Invalid probabilities")
        if not np.allclose(merged.groupby(["meeting","race"])[col].sum(),1,atol=1e-7,rtol=0):raise ValueError("Unnormalized race")
    if not merged.assign(win=merged.finish_position.eq(1)).groupby(["meeting","race"]).win.sum().eq(1).all():raise ValueError("Exactly one winner required per race")
    races=[]
    for (meeting,race),g in merged.groupby(["meeting","race"]):
        winner=g[g.finish_position.eq(1)].iloc[0]
        row={"meeting":meeting,"race":race,"winner_number":winner.number,"winner_horse":winner.horse,"source_url":winner.source_url}
        for col,label in [("control_prob","control"),("monty_prob","enriched")]:
            row[label+"_log_loss"]=float(-np.log(winner[col]))
            row[label+"_brier"]=float(((g[col]-g.finish_position.eq(1).astype(float))**2).sum())
            row[label+"_top_hit"]=int(g.sort_values([col,"number"],ascending=[False,True]).iloc[0].number==winner.number)
        races.append(row)
    table=pd.DataFrame(races)
    summary={"status":"RESULT_MATCHED_RESEARCH_ONLY","races":len(table),"runners":len(merged),"control_mean_log_loss":float(table.control_log_loss.mean()),"enriched_mean_log_loss":float(table.enriched_log_loss.mean()),"delta_log_loss":float((table.enriched_log_loss-table.control_log_loss).mean()),"control_mean_brier":float(table.control_brier.mean()),"enriched_mean_brier":float(table.enriched_brier.mean()),"delta_brier":float((table.enriched_brier-table.control_brier).mean()),"control_top_wins":int(table.control_top_hit.sum()),"enriched_top_wins":int(table.enriched_top_hit.sum()),"roi":None,"caveat":"One-day retrospective outcomes do not establish generalizable accuracy or profitability."}
    return summary,table

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--predictions",required=True);ap.add_argument("--outcomes",required=True);ap.add_argument("--output-prefix",required=True)
    a=ap.parse_args()
    s,t=evaluate(pd.read_csv(a.predictions,dtype={k:str for k in KEY}),pd.read_csv(a.outcomes,dtype={k:str for k in KEY}))
    Path(a.output_prefix+".json").write_text(json.dumps(s,indent=2)+"\n")
    t.to_csv(a.output_prefix+"_races.csv",index=False)
    print(json.dumps(s,indent=2))
if __name__=="__main__":main()
