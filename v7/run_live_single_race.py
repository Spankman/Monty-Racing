"""Fetch today's Krok feed and run a single genuine provisional V7 race.

No independent verification or betting authorisation is implied.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from krok_adapter import fetch,normalize
from .run_provisional_race import execute

def live(meeting,race,*,date,country,output_dir,allow_restricted=False):
    key=os.environ.get("KROK_API_KEY")
    if not key:
        raise ValueError("KROK_API_KEY missing")
    out=Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Refusing to overwrite existing run")
    out.mkdir(parents=True,exist_ok=True)
    raw=fetch(date,key)
    snapshot,audit=normalize(raw,date,include_restricted_flat_research=allow_restricted)
    snapshot_path=out/"provider_snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot,indent=2)+"\n")
    result=execute(snapshot_path,meeting,race,date=date,country=country,
                   output_dir=out/"v7",allow_restricted=allow_restricted)
    result["provider_races_accepted"]=audit["races_accepted"]
    result["provider_runners_accepted"]=audit["runners_accepted"]
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--meeting",required=True)
    p.add_argument("--race",required=True)
    p.add_argument("--date",default=dt.datetime.now(ZoneInfo("Australia/Brisbane")).date().isoformat())
    p.add_argument("--country",choices=("AU","NZ"),default="AU")
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--allow-restricted",action="store_true")
    a=p.parse_args()
    print(json.dumps(live(a.meeting,a.race,date=a.date,country=a.country,
                          output_dir=a.output_dir,allow_restricted=a.allow_restricted),indent=2))
if __name__=="__main__":
    main()
