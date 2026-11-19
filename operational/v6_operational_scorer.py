"""Provisional public-artifact V6 linear scorer; NEVER authorises betting."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from monty_v6.monty.integrity import validate_model_contract

STATUS = "PROVISIONAL_OPERATIONAL_V6"

def score_operational(df, root=Path("monty_v6")):
    required = ["meeting", "race", "number", "horse", "odds"]
    if df.empty or any(k not in df for k in required):
        raise ValueError("Nonempty runner data with meeting,race,number,horse,odds required")
    if df[required].isna().any().any():
        raise ValueError("Missing runner or odds")
    df = df.copy()
    for k in required[:4]:
        df[k] = df[k].astype(str).str.strip()
        if df[k].eq("").any():
            raise ValueError("Blank runner identity")
    df["odds"] = pd.to_numeric(df["odds"], errors="raise")
    if not np.isfinite(df["odds"]).all() or (df["odds"] <= 1).any():
        raise ValueError("Odds must be finite and greater than one")
    if "scratched" in df:
        df = df[~df["scratched"].astype(str).str.lower().isin(("true","1","yes"))].copy()
    if df.empty:
        raise ValueError("No active runners")
    df["race_id"] = df["meeting"].str.upper() + "|" + df["race"]
    if df.duplicated(["race_id","number"]).any():
        raise ValueError("Duplicate saddlecloth")
    model_path = Path(root) / "results" / "frozen_model.json"
    model = json.loads(model_path.read_text())
    if model.get("selected") != "linear_1.0" or model["models"]["linear_1.0"]["kind"] != "linear":
        raise ValueError("Unexpected frozen model")
    names = model["input_feature_names"]
    active = validate_model_contract(model, names)
    ids = df["race_id"].to_numpy()
    implied = 1.0 / df["odds"].to_numpy(float)
    base = implied / pd.Series(implied).groupby(ids).transform("sum").to_numpy()
    X = np.full((len(df),len(names)),np.nan)
    for j,name in enumerate(names):
        if name in df:
            X[:,j] = pd.to_numeric(df[name],errors="coerce").to_numpy(float)
    if "log_field_size" in names:
        X[:,names.index("log_field_size")] = np.log(df.groupby("race_id")["horse"].transform("size").to_numpy(float))
    if "log_market_probability" in names:
        X[:,names.index("log_market_probability")] = np.log(base)
    finite = np.isfinite(X)
    Xi = np.where(finite,X,np.asarray(model["imputation_medians"]))
    ix = [names.index(n) for n in active]
    Z = np.column_stack([Xi[:,ix],(~finite[:,ix]).astype(float)])
    Z = (Z-np.asarray(model["mean"]))/np.asarray(model["scale"])
    formidx = [i for i,n in enumerate(model["numeric_feature_names"]) if n!="log_market_probability"]
    logits = np.log(base)+Z[:,formidx]@np.asarray(model["models"]["linear_1.0"]["weights"])
    pred = np.empty(len(df),float)
    for _,positions in df.groupby("race_id",sort=False).indices.items():
        values=logits[positions]
        exp=np.exp(values-values.max())
        pred[positions]=exp/exp.sum()
    out=df[["meeting","race","number","horse","odds","race_id"]].copy()
    out["market_prob"]=base
    out["monty_prob"]=pred
    out["fair_odds"]=1/pred
    out["edge"]=pred/base-1
    out["feature_coverage"]=finite.mean(axis=1)
    out["status"]=STATUS
    out["betting_authorised"]=False
    return out
