"""Create-only provisional prediction outputs; never imply pre-off verification."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from v6_operational_scorer import score_operational,STATUS

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input_csv")
    p.add_argument("--output-dir",default="operational_output")
    p.add_argument("--root",default="monty_v6")
    p.add_argument("--race-manifest",help="Race count assertions JSON; does not independently verify completeness")
    args=p.parse_args()
    source=Path(args.input_csv)
    model=Path(args.root)/"results"/"frozen_model.json"
    df=pd.read_csv(source,dtype={"meeting":str,"race":str,"number":str,"horse":str})
    scored=score_operational(df,Path(args.root))
    if args.race_manifest:
        manifest=json.loads(Path(args.race_manifest).read_text())
        races=manifest.get("races")
        if manifest.get("date") and not isinstance(manifest["date"],str):
            raise ValueError("Invalid race manifest date")
        if not isinstance(races,list) or not races:
            raise ValueError("Race manifest needs races[]")
        expected={}
        for race in races:
            key=str(race.get("meeting","")).strip().upper()+"|"+str(race.get("race","")).strip()
            count=race.get("expected_active_runners")
            if not str(race.get("meeting","")).strip() or not str(race.get("race","")).strip() or type(count) is not int or count<1 or key in expected:
                raise ValueError("Invalid or duplicate race count")
            expected[key]=count
        # If the manifest declares research restrictions, enforce them against
        # the scored runner-level flags. Missing declarations remain unverified.
        for race in races:
            if "research_only_restricted_race" not in race:
                continue
            restricted=race["research_only_restricted_race"]
            if type(restricted) is not bool:
                raise ValueError("Invalid manifest research restriction flag")
            key=str(race["meeting"]).strip().upper()+"|"+str(race["race"]).strip()
            actual=scored.loc[scored["race_id"]==key,"research_only_restricted_race"]
            if actual.empty or not actual.eq(restricted).all():
                raise ValueError("Manifest and scored research restrictions disagree")
        observed=scored.groupby("race_id").size().to_dict()
        if observed!=expected:
            raise ValueError("Incomplete or unexpected race fields: "+str({"observed":observed,"expected":expected}))
        # Counts match the supplied manifest; its independent origin is not proven.

    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    record={
        "schema":"monty_provisional_operational_v1",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":STATUS,
        "betting_authorised":False,
        "pre_off_proven":False,
        "race_counts_match_supplied_manifest":bool(args.race_manifest),
        "manifest_counts_are_source_assertions":bool(args.race_manifest),
        "independent_field_verification_proven":False,
        "artifact_integrity_verified":False,
        "input_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "frozen_model_sha256":hashlib.sha256(model.read_bytes()).hexdigest(),
        "runner_count":len(scored),
        "race_count":scored["race_id"].nunique(),
        "note":"Provisional research scoring; input field and odds timestamps unverified."
    }
    if (out/"operational_predictions.csv").exists() or (out/"prediction_record.json").exists():
        raise FileExistsError("Output directory already contains prediction records")
    # Create-only outputs prevent silent overwrites of prior predictions.
    with (out/"operational_predictions.csv").open("x",encoding="utf-8",newline="") as f:
        scored.to_csv(f,index=False)
    with (out/"prediction_record.json").open("x",encoding="utf-8") as f:
        json.dump(record,f,indent=2)
        f.write("\n")
    print(json.dumps(record,indent=2))

if __name__=="__main__":
    main()
