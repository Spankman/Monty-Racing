"""Opt-in GitHub Actions dispatch bridge for Monty clients.

Requires GITHUB_TOKEN in the environment with Actions:write on repository.
Never stores credentials, never claims a dispatched job completed.
Stdlib only. Dispatch is explicit via --dispatch; otherwise dry-run.
"""
import argparse
import datetime
import json
import os
import re
import urllib.error
import urllib.request

REPO = "Spankman/Monty-Racing"
WORKFLOW = "monty-v7-research.yml"
REF = "experiment/expert-consensus-v7"
API = "https://api.github.com"

def payload(date, source_snapshot=""):
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("date must be YYYY-MM-DD")
    datetime.date.fromisoformat(date)
    if source_snapshot:
        from pathlib import PurePosixPath
        p = PurePosixPath(source_snapshot)
        if p.is_absolute() or ".." in p.parts or p.suffix != ".json":
            raise ValueError("source_snapshot must be a relative JSON path")
    return {"ref": REF, "inputs": {"racing_date": date, "source_snapshot": source_snapshot}}

def dispatch(date, source_snapshot="", token=None, opener=None):
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN required for dispatch; no run was started")
    request = urllib.request.Request(
        f"{API}/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches",
        data=json.dumps(payload(date, source_snapshot)).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"},
        method="POST")
    opener = opener or urllib.request.urlopen
    with opener(request, timeout=30) as response:
        if response.status != 204:
            raise RuntimeError(f"Unexpected GitHub dispatch status: {response.status}")
    return {"status": "DISPATCH_ACCEPTED_NOT_COMPLETED", "repository": REPO,
            "workflow": WORKFLOW, "branch": REF, "date": date,
            "warning": "GitHub returns HTTP 204 without a run ID. Query Actions runs separately; never assume completion."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    p.add_argument("--source-snapshot", default="")
    p.add_argument("--dispatch", action="store_true",
                   help="Explicitly trigger GitHub Actions (requires GITHUB_TOKEN)")
    args = p.parse_args()
    if args.dispatch:
        result = dispatch(args.date, args.source_snapshot)
    else:
        result = {"status": "DRY_RUN_NO_DISPATCH", "repository": REPO,
                  "workflow": WORKFLOW, "payload": payload(args.date, args.source_snapshot)}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
