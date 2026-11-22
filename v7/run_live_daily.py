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
    args=p.parse_args()
    dt.date.fromisoformat(args.date)
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
    (out/"selections.json").write_text(json.dumps({"date":args.date,"status":"PROVISIONAL RESEARCH ONLY — NO BET","results":results,"failures":failures},indent=2))
    lines=["# Monty V7 — "+args.date,"","**EXPERIMENTAL — NO BET. Country attribution not verified where provider snapshot lacks country.**",""]
    for result in sorted(results,key=lambda x:(x["meeting"],int(x["race"]) if x["race"].isdigit() else 999)):
        top=result["ordered"][0]
        lines.append(f'## {result["meeting"]} R{result["race"]}')
        lines.append(f'**#{top["number"]} {top["horse"]}** — ${top["fixed_win_odds"]:.2f}, V7 {top["v7_win_probability"]:.1%}')
        value=result.get("provisional_value_candidate")
        if isinstance(value,dict):
            lines.append(f'Value candidate: #{value.get("number","?")} {value.get("horse","?")} (uncalibrated)')
        lines.append("NO BET — experimental model")
        lines.append("")
    lines.append(f'Scored {len(results)} races; failed {len(failures)} races. Provider country verification incomplete.')
    (out/"selections.md").write_text("\n".join(lines)+"\n")
    print(f"Scored {len(results)} races; failed {len(failures)}")
    if not results:
        raise RuntimeError("No races scored; see provider_audit.json and selections.json")
if __name__=="__main__":
    main()
