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
    args=p.parse_args()
    source=Path(args.input_csv)
    model=Path(args.root)/"results"/"frozen_model.json"
    df=pd.read_csv(source,dtype={"meeting":str,"race":str,"number":str,"horse":str})
    scored=score_operational(df,Path(args.root))
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    record={
        "schema":"monty_provisional_operational_v1",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":STATUS,
        "betting_authorised":False,
        "pre_off_proven":False,
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
