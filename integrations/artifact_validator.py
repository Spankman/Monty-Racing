"""Validate Monty GitHub Actions artifact contents before exposing to any AI.

A green Actions check is NOT proof that the model ran. This validator requires
run_status.json and, for completed predictions, an explicit, nonempty prediction
file with matching model/version/run metadata. No network access required.
"""
import argparse
import io
import json
import zipfile

MAX_ZIP_BYTES = 30_000_000
MAX_MEMBER_BYTES = 10_000_000

def _read_json(z, name):
    names = z.namelist()
    matches = [n for n in names if n == name or n.endswith('/' + name)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {name}, found {len(matches)}")
    info = z.getinfo(matches[0])
    if info.file_size > MAX_MEMBER_BYTES:
        raise ValueError(f"Artifact member too large: {name}")
    return json.loads(z.read(matches[0]))

def validate_artifact_bytes(data):
    if len(data) > MAX_ZIP_BYTES:
        raise ValueError("Artifact ZIP too large")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.infolist()) > 1000:
            raise ValueError("Too many artifact members")
        if any(i.file_size > MAX_MEMBER_BYTES for i in z.infolist()):
            raise ValueError("Oversized member")
        status = _read_json(z, "run_status.json")
        if not isinstance(status, dict):
            raise ValueError("Invalid run_status.json")
        if status.get("model_executed") is not True:
            return {"state": "NOT_EXECUTED", "run_status": status,
                    "predictions": None,
                    "reason": "Discovery or partial pipeline only"}
        if status.get("status") != "MODEL_COMPLETED":
            raise ValueError("model_executed true requires MODEL_COMPLETED")
        predictions = _read_json(z, "predictions.json")
        if not isinstance(predictions, dict):
            raise ValueError("Invalid predictions.json")
        for key in ("model_version", "generated_at", "data_cutoff", "races"):
            if not predictions.get(key):
                raise ValueError("Completed predictions missing " + key)
        if not isinstance(predictions["races"], list) or not predictions["races"]:
            raise ValueError("Completed predictions must have nonempty races")
        if predictions["model_version"] != status.get("model_version"):
            raise ValueError("Model version mismatch")
        if str(predictions["model_version"]).startswith("v7") and not predictions.get("research_only"):
            raise ValueError("V7 predictions must be research-only until approved")
        return {"state": "VALIDATED_MODEL_OUTPUT", "run_status": status,
                "predictions": predictions}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("artifact_zip")
    args=p.parse_args()
    with open(args.artifact_zip, "rb") as f:
        result=validate_artifact_bytes(f.read())
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
