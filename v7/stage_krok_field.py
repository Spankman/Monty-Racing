"""Stage a Krok snapshot as a V7 single-race verification worksheet.

This tool NEVER attests that a provider field is independently verified and
NEVER scores or authorises a bet. Operator must check active runners,
scratchings, quote source, timestamp and country separately.
"""
import argparse
import json
import math
from pathlib import Path
import pandas as pd

def stage(snapshot_path, meeting, race, output_csv, *, allow_restricted=False):
    snapshot=json.loads(Path(snapshot_path).read_text())
    races=snapshot.get("races")
    if not isinstance(races,list):
        raise ValueError("Snapshot missing accepted race manifest")
    matching=[entry for entry in races if
              str(entry.get("meeting","")).strip().casefold()==meeting.strip().casefold()
              and str(entry.get("race","")).strip()==str(race).strip()]
    if len(matching)!=1:
        raise ValueError("Requested race must occur exactly once in accepted race manifest")
    if matching[0].get("betting_authorised") is not False:
        raise ValueError("Unexpected race betting-authorisation flag")
    rows=snapshot.get("runners")
    if not isinstance(rows,list):
        raise ValueError("Snapshot has no runner list")
    selected=[r for r in rows if str(r.get("meeting","")).strip().casefold()==meeting.strip().casefold()
              and str(r.get("race","")).strip()==str(race).strip()]
    if not selected:
        raise ValueError("Requested race not found in snapshot")
    if matching[0].get("expected_active_runners") != len(selected):
        raise ValueError("Runner count differs from accepted race manifest")
    if len(selected)<3:
        raise ValueError("At least three active runners required for V7")
    if not allow_restricted and any(r.get("research_only_restricted_race") is True for r in selected):
        raise ValueError("Restricted race requires separate explicit override")
    if not allow_restricted and any(r.get("race_classification_unknown") is True for r in selected):
        raise ValueError("Unknown race classification requires separate review")
    if any(r.get("betting_authorised") is not False for r in selected):
        raise ValueError("Unexpected betting-authorisation flag")
    required=("meeting","race","number","horse","odds")
    if any(any(k not in r or r[k] is None for k in required) for r in selected):
        raise ValueError("Incomplete provider field")
    if any(str(r[k]).strip()=="" for r in selected for k in ("meeting","race","number","horse")):
        raise ValueError("Blank runner identity")
    if len({str(r["number"]) for r in selected})!=len(selected):
        raise ValueError("Duplicate saddlecloth")
    try:
        odds=[float(r["odds"]) for r in selected]
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError("Invalid fixed-win odds") from exc
    if any(not math.isfinite(o) or o<=1 for o in odds):
        raise ValueError("Invalid fixed-win odds")
    sources=[r.get("_price_source") for r in selected]
    if any(not isinstance(source,str) or not source.strip() for source in sources):
        raise ValueError("Missing fixed-win price provenance")
    if len(set(sources))!=1:
        raise ValueError("Mixed fixed-win price sources")
    # Never merge a snapshot containing contradictory aliases into a single field.
    # The upstream adapter excludes known aliases, but stage must fail closed too.
    if len({(str(r["meeting"]).casefold(),str(r["race"])) for r in selected})!=1:
        raise ValueError("Conflicting race identities")
    out=Path(output_csv)
    if out.exists():
        raise FileExistsError("Refusing to overwrite an existing field")
    out.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(selected).to_csv(out,index=False)
    return {"status":"UNVERIFIED_PROVIDER_FIELD_REQUIRES_INDEPENDENT_CHECK",
            "runners":len(selected),"output_csv":str(out),
            "betting_authorised":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("snapshot",type=Path)
    p.add_argument("--meeting",required=True)
    p.add_argument("--race",required=True)
    p.add_argument("--output-csv",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(stage(a.snapshot,a.meeting,a.race,a.output_csv),indent=2))

if __name__=="__main__":
    main()
