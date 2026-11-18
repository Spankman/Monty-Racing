"""Execute existing audited V6 snapshot pipeline and emit validated research artifact.

This wrapper never modifies frozen V6. It cannot collect live data by itself.
A missing snapshot results in an explicit NOT_EXECUTED status.
"""
import argparse
import csv
import datetime
import json
import pathlib
import subprocess
import sys

def execute(date, source_snapshot, output_dir="output"):
    datetime.date.fromisoformat(date)
    out=pathlib.Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    status_path=out/"run_status.json"
    status={"racing_date":date,"source_snapshot":source_snapshot or None,
            "model_executed":False,"expert_sites_fetched":False,
            "status":"DISCOVERY_ONLY_NO_RUNNER_SNAPSHOT",
            "reason":"No audited source snapshot supplied"}
    if not source_snapshot:
        status_path.write_text(json.dumps(status,indent=2)+"\n")
        return status
    src=pathlib.Path(source_snapshot)
    if src.is_absolute() or ".." in src.parts or src.suffix.lower()!=".json":
        raise ValueError("Snapshot must be a safe relative JSON path")
    if not src.is_file():
        status["status"]="SNAPSHOT_NOT_FOUND"
        status["reason"]="Requested snapshot path does not exist"
        status_path.write_text(json.dumps(status,indent=2)+"\n")
        return status
    try:
        subprocess.run([sys.executable,"run_day.py",str(src),"--date",date,
                        "--output-dir",str(out/"scored")],check=True,timeout=600)
        audit=json.loads((out/"scored"/"run_audit.json").read_text())
        with (out/"scored"/"monty_selections.csv").open(newline="") as f:
            rows=list(csv.DictReader(f))
        if not rows:
            raise ValueError("Scoring produced no runner rows")
        now=datetime.datetime.now(datetime.timezone.utc).isoformat()
        # This output is deliberately not approved tips; field verification is external.
        races={}
        for row in rows:
            race_id=row["meeting"]+"|"+str(row["race"])
            races.setdefault(race_id,[]).append({
                "runner_number":row["number"],"runner_name":row["horse"],
                "win_probability":float(row["monty_prob"]),
                "odds_decimal":float(row["odds"]),
                "expected_value":float(row["edge"]),
                "feature_coverage":float(row["feature_coverage"]),
                "selection_status":"RESEARCH_ONLY"})
        predictions={"model_version":"v6_frozen_research_snapshot","generated_at":now,
                     "data_cutoff":None,"research_only":True,
                     "source_sha256":audit["source_sha256"],
                     "races":[{"race_id":k,"runners":v} for k,v in sorted(races.items())],
                     "warnings":["Source observation cutoff unavailable; do not infer a pre-race timestamp",
                                 "Snapshot runner counts and odds not independently verified",
                                 "Do not treat as betting advice or validated V7 predictions"]}
        (out/"predictions.json").write_text(json.dumps(predictions,indent=2)+"\n")
        status.update({"model_executed":True,"status":"MODEL_COMPLETED",
                       "model_version":predictions["model_version"],
                       "runner_count":len(rows),"race_count":len(races),
                       "source_sha256":audit["source_sha256"],
                       "reason":"Frozen V6 executed against supplied audited snapshot; research only"})
    except Exception as exc:
        status.update({"model_executed":False,"status":"MODEL_FAILED",
                       "reason":str(exc)[:500]})
    status_path.write_text(json.dumps(status,indent=2)+"\n")
    return status

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    p.add_argument("--source-snapshot",default="")
    p.add_argument("--output-dir",default="output")
    args=p.parse_args()
    result=execute(args.date,args.source_snapshot,args.output_dir)
    print(json.dumps(result,indent=2))
    if result["status"]=="MODEL_FAILED":
        sys.exit(1)

if __name__=="__main__":
    main()
