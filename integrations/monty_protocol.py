"""Portable Monty request/result validators. No server or execution bridge."""
import datetime
import json
import re

def validate_request(p):
    if not isinstance(p, dict) or set(p) != {"date","model","meetings","idempotency_key"}:
        raise ValueError("Missing or unexpected request keys")
    date=p["date"]
    if not isinstance(date,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date):
        raise ValueError("Invalid date format")
    datetime.date.fromisoformat(date)
    if p["model"] not in ("latest_approved","v6","v7_research"):
        raise ValueError("Invalid model")
    if p["meetings"] != "all_au_nz":
        raise ValueError("Invalid meetings")
    key=p["idempotency_key"]
    if not isinstance(key,str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,128}",key):
        raise ValueError("Invalid idempotency key")
    return dict(p)

def validate_run_result(p):
    if not isinstance(p,dict) or p.get("status") not in ("queued","running","completed","failed","blocked"):
        raise ValueError("Invalid run status")
    if not isinstance(p.get("run_id"),str) or not p["run_id"]:
        raise ValueError("Missing run id")
    if p["status"] == "completed":
        if any(not p.get(k) for k in ("model_version","generated_at","data_cutoff","races")):
            raise ValueError("Missing completed-run metadata")
        if not isinstance(p["races"],list):
            raise ValueError("Invalid races")
        if str(p["model_version"]).startswith("v7") and not p.get("research_only",False):
            raise ValueError("V7 requires research_only")
    return p

def dumps(p):
    return json.dumps(p,sort_keys=True,separators=(",",":"))
