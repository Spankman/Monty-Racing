"""Read GitHub Actions status and artifact metadata for a known run.

No fake run IDs, no predictions inferred from an artifact name, no token logging.
Uses GitHub REST API; private repositories require a token with Actions:read.
"""
import argparse
import json
import os
import urllib.request

API="https://api.github.com"
REPO="Spankman/Monty-Racing"

def _get(path, token=None, opener=None):
    token=token or os.environ.get("GITHUB_TOKEN")
    headers={"Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28",
             "User-Agent":"Monty-Racing-Client"}
    if token:
        headers["Authorization"]="Bearer "+token
    request=urllib.request.Request(API+path,headers=headers)
    opener=opener or urllib.request.urlopen
    with opener(request,timeout=30) as response:
        return json.load(response)

def run_status(run_id, token=None, opener=None):
    if not isinstance(run_id,int) or run_id<=0:
        raise ValueError("run_id must be positive integer")
    data=_get(f"/repos/{REPO}/actions/runs/{run_id}",token,opener)
    status=data.get("status")
    conclusion=data.get("conclusion")
    if status=="completed" and conclusion=="success":
        state="WORKFLOW_SUCCEEDED_ARTIFACT_UNVERIFIED"
    elif status=="completed":
        state="WORKFLOW_FAILED_OR_CANCELLED"
    elif status in ("queued","in_progress","waiting","pending","requested"):
        state="WORKFLOW_PENDING"
    else:
        state="UNKNOWN"
    return {"run_id":run_id,"workflow_status":status,"conclusion":conclusion,
            "state":state,"html_url":data.get("html_url"),
            "head_sha":data.get("head_sha"),
            "warning":"Workflow success does not prove Monty model executed; inspect run_status.json artifact."}

def list_artifacts(run_id,token=None,opener=None):
    if not isinstance(run_id,int) or run_id<=0:
        raise ValueError("run_id must be positive integer")
    data=_get(f"/repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100",token,opener)
    return [{"id":a["id"],"name":a["name"],"expired":a.get("expired",False),
             "size_in_bytes":a.get("size_in_bytes")}
            for a in data.get("artifacts",[])]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True,type=int)
    args=p.parse_args()
    print(json.dumps({"run":run_status(args.run_id),
                      "artifacts":list_artifacts(args.run_id)},indent=2))

if __name__=="__main__":
    main()
