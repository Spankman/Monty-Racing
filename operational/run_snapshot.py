"""Bridge Krok-normalized snapshot to provisional scorer; research only.

Usage: python operational/run_snapshot.py snapshot.json --output-dir out
Never claims independent field verification or betting readiness.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot")
    parser.add_argument("--output-dir",required=True)
    parser.add_argument("--root",default="monty_v6")
    args=parser.parse_args()
    snapshot=json.loads(Path(args.snapshot).read_text())
    runners=snapshot.get("runners")
    races=snapshot.get("races")
    if not isinstance(runners,list) or not runners:
        raise ValueError("Snapshot requires nonempty runners")
    if not isinstance(races,list) or not races:
        raise ValueError("Snapshot requires race count assertions")
    if not isinstance(snapshot.get("date"),str):
        raise ValueError("Snapshot requires date")
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp)
        csv=temp/"runners.csv"
        manifest=temp/"manifest.json"
        pd.DataFrame(runners).to_csv(csv,index=False)
        manifest.write_text(json.dumps({"date":snapshot["date"],"races":races}))
        command=[sys.executable,str(Path(__file__).with_name("run_operational.py")),
                 str(csv),"--output-dir",args.output_dir,"--root",args.root,
                 "--race-manifest",str(manifest)]
        subprocess.run(command,check=True)
    # Keep the create-only prediction record immutable. Store provenance separately.
    import hashlib
    provenance={
        "source_snapshot_sha256":hashlib.sha256(Path(args.snapshot).read_bytes()).hexdigest(),
        "source_snapshot_date":snapshot["date"],
        "source_adapter":"Krok-normalized snapshot (source unverified)",
        "independent_field_verification_proven":False,
        "betting_authorised":False
    }
    with (Path(args.output_dir)/"snapshot_provenance.json").open("x") as f:
        json.dump(provenance,f,indent=2)
        f.write("\\n")

if __name__=="__main__":
    main()
