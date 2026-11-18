"""Paired FormFav-enrichment sensitivity test; never modifies V6 artifacts.

Requires same complete race fields/quotes in both snapshots. Removes only the
verified jockey_changed feature in the control, retaining all other inputs.
This measures prediction sensitivity, NOT improved accuracy or ROI.
"""
import argparse,json,tempfile
from pathlib import Path
import numpy as np
import pandas as pd

IDENTITY=["meeting","race","number","horse","odds"]

def validate_pairs(control, enriched):
    for label,frame in [("control",control),("enriched",enriched)]:
        if any(c not in frame.columns for c in IDENTITY):
            raise ValueError(label+" missing identity or quote columns")
        if frame.duplicated(["meeting","race","number"]).any():
            raise ValueError(label+" duplicate runner key")
    a=control[IDENTITY].copy()
    b=enriched[IDENTITY].copy()
    for frame in [a,b]:
        for col in IDENTITY:frame[col]=frame[col].astype(str).str.strip()
    a=a.sort_values(IDENTITY).reset_index(drop=True)
    b=b.sort_values(IDENTITY).reset_index(drop=True)
    if not a.equals(b):
        raise ValueError("Field, runner identity or odds changed: not a paired comparison")

def sensitivity(enriched, scorer):
    if "jockey_changed" not in enriched:
        raise ValueError("Missing jockey_changed column; cannot test enrichment")
    control=enriched.copy()
    control["jockey_changed"]=np.nan
    validate_pairs(control,enriched)
    with tempfile.TemporaryDirectory() as tmp:
        before=Path(tmp)/"control.csv";after=Path(tmp)/"enriched.csv"
        control.to_csv(before,index=False);enriched.to_csv(after,index=False)
        p=scorer(before,Path(tmp)/"control_scores.csv")
        q=scorer(after,Path(tmp)/"enriched_scores.csv")
    key=["meeting","race","number"]
    p=p[key+["horse","odds","monty_prob"]].rename(columns={"monty_prob":"control_probability"})
    q=q[key+["horse","odds","monty_prob"]].rename(columns={"monty_prob":"enriched_probability"})
    joined=p.merge(q,on=key,validate="one_to_one",suffixes=("_control","_enriched"))
    if len(joined)!=len(enriched):raise ValueError("Scored runner count mismatch")
    if not (joined.horse_control==joined.horse_enriched).all():
        raise ValueError("Scored horse identities differ")
    joined["delta"]=joined.enriched_probability-joined.control_probability
    changes=[]
    for (meeting,race),rows in joined.groupby(["meeting","race"],sort=True):
        old=rows.sort_values(["control_probability","number"],ascending=[False,True]).iloc[0]
        new=rows.sort_values(["enriched_probability","number"],ascending=[False,True]).iloc[0]
        if str(old.number)!=str(new.number):
            changes.append({"meeting":meeting,"race":str(race),
                "control_top":str(old.number)+" "+str(old.horse_control),
                "enriched_top":str(new.number)+" "+str(new.horse_enriched)})
    return {"status":"FORMFAV_JOCKEY_CHANGE_SENSITIVITY_NOT_ACCURACY",
            "runner_count":len(joined),"race_count":joined.groupby(["meeting","race"]).ngroups,
            "enriched_feature_rows":int(pd.to_numeric(enriched.jockey_changed,errors="coerce").notna().sum()),
            "top_rank_changes":changes,
            "mean_absolute_probability_change":float(joined.delta.abs().mean()),
            "max_absolute_probability_change":float(joined.delta.abs().max()),
            "accuracy_improvement":None,"roi_improvement":None,
            "warning":"Ablation is not a predictive-value test; historical outcomes and point-in-time controls required."}

def main():
    from race_day import run
    parser=argparse.ArgumentParser()
    parser.add_argument("--enriched-inputs",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    data=pd.read_csv(args.enriched_inputs,dtype={"meeting":str,"race":str,"number":str,"horse":str})
    report=sensitivity(data,run)
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
