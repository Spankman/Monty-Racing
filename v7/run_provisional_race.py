"""Run actual experimental V7 on one provider snapshot race; research only.

This never claims independent verification, betting approval or TAB coverage.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import pandas as pd
from .stage_krok_field import stage
from .predict import run
from .value_watch import select_value_watch

def execute(snapshot, meeting, race, *, date, country, output_dir,
            allow_restricted=False, model_path=Path("v7/artifacts/fold_3_model.json")):
    if country not in ("AU", "NZ"):
        raise ValueError("Country must be AU or NZ")
    snapshot_data=json.loads(Path(snapshot).read_text())
    if str(snapshot_data.get('date','')) != str(date):
        raise ValueError('Snapshot date does not match requested race date')
    out=Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Output directory must be empty to freeze prediction evidence")
    out.mkdir(parents=True,exist_ok=True)
    staged=out/"provider_field.csv"
    stage(snapshot,meeting,str(race),staged,allow_restricted=allow_restricted)
    df=pd.read_csv(staged,dtype={"meeting":str,"race":str,"number":str,"horse":str})
    df["race_id"]=country+"|"+df["meeting"].astype(str).str.upper()+"|"+df["race"].astype(str)
    df["runner_id"]=df["number"].astype(str)
    df["fixed_win_odds"]=pd.to_numeric(df["odds"],errors="raise")
    df["date"]=date
    df["country"]=country
    df["source_url"]="https://krokodds.com.au"
    df["field_verified"]=False
    df.to_csv(out/"provisional_input.csv",index=False)
    run(Path(model_path),out/"provisional_input.csv",out,provisional=True)
    scored=pd.read_csv(out/"v7_research_scores.csv")
    scored=scored.sort_values("v7_win_probability",ascending=False)
    scored_at=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    result={"status":"PROVISIONAL_V7_PROVIDER_UNVERIFIED","betting_authorised":False,
            "scored_at_utc":scored_at,
            "provider_odds_captured_at_utc":None,
            "pre_race_evidence_verified":False,
            "meeting":meeting,"race":str(race),"date":date,"country":country,
            "ordered":[{"number":str(row.runner_id),"horse":str(row.horse),
                        "fixed_win_odds":float(row.fixed_win_odds),
                        "v7_win_probability":float(row.v7_win_probability)}
                       for row in scored.itertuples(index=False)]}
    # Market comparison is diagnostic only: no evidence of a calibrated edge
    # or profitable exotic payout is inferred from a ranking.
    for runner in result["ordered"]:
        odds=runner["fixed_win_odds"]
        probability=runner["v7_win_probability"]
        runner["market_implied_probability"]=1.0/odds
        runner["model_minus_raw_market_probability"]=probability-1.0/odds
        runner["model_expected_win_roi"]=probability*odds-1.0
    result["win_value_diagnostic"]={
        "best_bet_model_expected_win_roi":result["ordered"][0]["model_expected_win_roi"],
        "best_bet_fair_win_odds":1.0/result["ordered"][0]["v7_win_probability"],
        "calibration_unverified":True,
        "betting_decision":"NO BET — provisional probabilities not prospectively validated"}
    # Separate value ranking from the most-likely winner. All probabilities
    # remain uncalibrated: these are diagnostics, never betting approvals.
    result["provisional_value_candidate"]=select_value_watch(result["ordered"])
    result["value_watch_status"]=(
        "UNCALIBRATED POSITIVE MODEL EDGE — NO BET"
        if result["provisional_value_candidate"] is not None
        else "NO POSITIVE MODEL EDGE — NO BET"
    )
    # An apparent positive edge cannot authorise a wager.
    # Exotic progression uses fixed WIN prices only, never exotic dividends.
    ranked=result["ordered"]
    progression={"type":"WIN","numbers":[ranked[0]["number"]]}
    if len(ranked)>=2 and ranked[0]["fixed_win_odds"]<4:
        progression={"type":"QUINELLA","numbers":[x["number"] for x in ranked[:2]]}
        if len(ranked)>=3 and ranked[1]["fixed_win_odds"]<4:
            progression={"type":"BOXED_TRIFECTA","numbers":[x["number"] for x in ranked[:3]]}
            if len(ranked)>=4 and ranked[2]["fixed_win_odds"]<4:
                progression={"type":"BOXED_FIRST_FOUR","numbers":[x["number"] for x in ranked[:4]]}
    result["fixed_win_price_progression"]=progression
    (out/"provisional_selection.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("snapshot",type=Path)
    p.add_argument("--meeting",required=True)
    p.add_argument("--race",required=True)
    p.add_argument("--date",required=True)
    p.add_argument("--country",required=True,choices=["AU","NZ"])
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--allow-restricted",action="store_true")
    p.add_argument("--model",type=Path,default=Path("v7/artifacts/fold_3_model.json"))
    a=p.parse_args()
    print(json.dumps(execute(a.snapshot,a.meeting,a.race,date=a.date,country=a.country,
                             output_dir=a.output_dir,allow_restricted=a.allow_restricted,
                             model_path=a.model),indent=2))
if __name__=="__main__":
    main()
