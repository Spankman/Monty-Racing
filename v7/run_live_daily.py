"""Generate genuine provisional V7 rankings for all eligible races in one dated Krok snapshot."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from krok_adapter import fetch, normalize
from v7.run_provisional_race import execute

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",default=dt.datetime.now(ZoneInfo("Australia/Brisbane")).date().isoformat())
    p.add_argument("--output-dir",default="output_v7_daily")
    p.add_argument("--verified-fixtures",required=True,type=Path)
    args=p.parse_args()
    dt.date.fromisoformat(args.date)
    fixtures=json.loads(args.verified_fixtures.read_text())
    if fixtures.get("date") != args.date or not fixtures.get("meetings"):
        raise ValueError("Missing or mismatched independently verified fixtures")
    verified={str(k).upper():int(v) for k,v in fixtures["meetings"].items()}
    key=os.environ.get("KROK_API_KEY")
    if not key:
        raise RuntimeError("KROK_API_KEY missing")
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    snapshot,audit=normalize(fetch(args.date,key),args.date)
    snapshot_path=out/"provider_snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot,indent=2))
    (out/"provider_audit.json").write_text(json.dumps(audit,indent=2))
    results=[]
    failures=[]
    for race in snapshot["races"]:
        meeting=race["meeting"]
        number=str(race["race"])
        if meeting.strip().upper() not in verified or not number.isdigit() or not 1<=int(number)<=verified[meeting.strip().upper()]:
            failures.append({"meeting":meeting,"race":number,"error":"Excluded: not on independently verified dated fixture"})
            continue
        country="NZ" if any(r.get("country")=="NZ" for r in snapshot["runners"] if r["meeting"]==meeting and r["race"]==number) else "AU"
        # Provider snapshot may not contain country. Do not guess NZ/AU identity.
        if not any(r.get("country") in ("AU","NZ") for r in snapshot["runners"] if r["meeting"]==meeting and r["race"]==number):
            country="UNVERIFIED"
        slug=str(len(results)+len(failures)+1).zfill(3)
        try:
            result=execute(snapshot_path,meeting,number,date=args.date,country=country if country!="UNVERIFIED" else "AU",output_dir=out/"races"/slug)
            result["country_provider_verified"]=country!="UNVERIFIED"
            results.append(result)
        except Exception as exc:
            failures.append({"meeting":meeting,"race":number,"error":str(exc)})
    # Provisional classification is per RACE, never one-per-meeting.
    # Require positive uncalibrated model/market edge; never authorise bets.
    picks=[]
    for result in results:
        ordered=result.get("ordered") or []
        if not ordered:
            continue
        top=ordered[0]
        p=float(top["v7_win_probability"])
        odds=float(top["fixed_win_odds"])
        if p >= 0.20 and odds < 4 and p*odds > 1.0:
            picks.append({"meeting":result["meeting"],"race":result["race"],"label":"BB","number":str(top["number"]),"horse":top["horse"],"fixed_win_odds":odds,"model_expected_win_roi":p*odds-1,"betting_authorised":False})
        value=result.get("provisional_value_candidate")
        if isinstance(value,dict):
            vp=float(value["v7_win_probability"])
            vo=float(value["fixed_win_odds"])
            if vo >= 4 and vp >= 0.06 and vp*vo > 1.0:
                picks.append({"meeting":result["meeting"],"race":result["race"],"label":"R","number":str(value["number"]),"horse":value["horse"],"fixed_win_odds":vo,"model_expected_win_roi":vp*vo-1,"betting_authorised":False})
    picks.sort(key=lambda x:(x["meeting"],int(x["race"]),x["label"]))
    diagnostics={"races":len(results),"positive_top_edge":0,"positive_any_edge":0}
    for result in results:
        runners=result.get("ordered") or []
        if not runners:
            continue
        rois=[float(r["v7_win_probability"])*float(r["fixed_win_odds"])-1 for r in runners]
        diagnostics["positive_top_edge"]+=int(rois[0]>0)
        diagnostics["positive_any_edge"]+=int(any(roi>0 for roi in rois))
    # Distinguish bookmaker overround, missing form features, and model adjustments.
    import math
    detailed=[]
    for result in results:
        runners=result.get("ordered") or []
        if not runners:
            continue
        inv=[1/float(r["fixed_win_odds"]) for r in runners]
        overround=sum(inv)
        if not math.isfinite(overround) or overround<=0:
            continue
        comparisons=[]
        for r,raw in zip(runners,inv):
            p=float(r["v7_win_probability"])
            odds=float(r["fixed_win_odds"])
            comparisons.append({"number":r["number"],"horse":r["horse"],
                "odds":odds,"model_p":p,"raw_market_p":raw,
                "normalized_market_p":raw/overround,
                "model_minus_normalized_market_p":p-raw/overround,
                "model_roi":p*odds-1})
        detailed.append({"meeting":result["meeting"],"race":result["race"],
            "market_overround":overround,
            "model_probability_sum":sum(x["model_p"] for x in comparisons),
            "max_model_minus_normalized_market_p":max(x["model_minus_normalized_market_p"] for x in comparisons),
            "max_model_roi":max(x["model_roi"] for x in comparisons),
            "runners":comparisons})
    (out/"market_probability_audit.json").write_text(json.dumps(detailed,indent=2))
    diagnostics["overround_min"]=min((x["market_overround"] for x in detailed),default=None)
    diagnostics["overround_max"]=max((x["market_overround"] for x in detailed),default=None)
    diagnostics["model_p_sum_invalid_races"]=sum(not math.isclose(x["model_probability_sum"],1,abs_tol=1e-5) for x in detailed)
    diagnostics["max_model_minus_normalized_market_p"]=max((x["max_model_minus_normalized_market_p"] for x in detailed),default=None)
    (out/"value_diagnostics.json").write_text(json.dumps(diagnostics,indent=2))

    (out/"selections.json").write_text(json.dumps({"date":args.date,"status":"PROVISIONAL RESEARCH ONLY — NO BET","classification_rules":{"BB":"Top V7-ranked horse in each race; probability >=20%, fixed win odds < $4, uncalibrated model ROI > 0%","R":"Highest model-ROI positive-edge candidate in each race; fixed win odds >= $4, probability >=6%, uncalibrated model ROI > 0%","selection_limit_per_track":None,"betting_authorised":False},"picks":picks,"results":results,"failures":failures},indent=2))
    lines=["# Monty V7 BB/R — "+args.date,"","**PROVISIONAL ONLY — NO BET. Model probabilities are uncalibrated; these are research classifications, not proven betting value.**",""]
    current=None
    for pick in picks:
        if pick["meeting"]!=current:
            current=pick["meeting"]
            lines.extend(["", "## "+current])
        lines.append(f'- R{pick["race"]} — **{pick["label"]} #{pick["number"]} {pick["horse"]}**')
    if not picks:
        lines.append("No qualifying provisional BB/R selections — NO BET.")
    lines.extend(["",f'Scored {len(results)} races; excluded/failed {len(failures)} races. Independent fixture list applied; runner/odds verification incomplete.',""])
    lines.append("Value diagnostic: "+json.dumps(diagnostics,sort_keys=True))
    (out/"selections.md").write_text("\n".join(lines)+"\n")
    print(f"Scored {len(results)} races; failed {len(failures)}")
    if not results:
        raise RuntimeError("No races scored; see provider_audit.json and selections.json")
if __name__=="__main__":
    main()
