"""Temporary pre-race expert-tip cache. Standard library only.

Input JSON: {"tips":[{"date":"YYYY-MM-DD","track":"Kilcoy","race":4,
"runner":"Horse","expert":"Name","source_url":"https://...",
"published_at":"2026-11-20T08:00:00+10:00",
"off_at":"2026-11-20T14:00:00+10:00"}]}
All timestamps must be offset-aware. No inference from article leads.
"""
import argparse
import datetime as dt
import json
import pathlib
import tempfile
from urllib.parse import urlparse

def stamp(s):
    x = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if x.tzinfo is None or x.utcoffset() is None:
        raise ValueError("timezone required")
    return x

def validate(t):
    required = ("date", "track", "race", "runner", "expert", "source_url", "published_at", "off_at")
    if any(not t.get(k) for k in required):
        raise ValueError("missing required field")
    dt.date.fromisoformat(t["date"])
    if not isinstance(t["race"], int) or not 1 <= t["race"] <= 20:
        raise ValueError("invalid race")
    if urlparse(t["source_url"]).scheme != "https":
        raise ValueError("HTTPS source required")
    if stamp(t["published_at"]) >= stamp(t["off_at"]):
        raise ValueError("post-off tip rejected")
    if stamp(t["published_at"]).date() > dt.date.fromisoformat(t["date"]):
        raise ValueError("published after race date")
    return {k:t[k] for k in required}

def key(t):
    return tuple(str(t[k]).casefold().strip() for k in ("date","track","race","runner","expert","source_url"))

def save(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf8") as f:
        json.dump({"tips":rows}, f, indent=2)
        temp = pathlib.Path(f.name)
    temp.replace(path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command", choices=("ingest","race","prune"))
    p.add_argument("--cache", default="expert_cache.json")
    p.add_argument("--input")
    p.add_argument("--date")
    p.add_argument("--track")
    p.add_argument("--race", type=int)
    p.add_argument("--now", help="ISO datetime with timezone; default current UTC")
    a=p.parse_args()
    path=pathlib.Path(a.cache)
    existing=json.loads(path.read_text())["tips"] if path.exists() else []
    now=stamp(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if a.command=="ingest":
        if not a.input: p.error("--input required")
        incoming=json.loads(pathlib.Path(a.input).read_text())["tips"]
        clean=[validate(t) for t in incoming]
        merged={key(t):t for t in existing if stamp(t["off_at"])>now}
        for t in clean:
            if stamp(t["off_at"])>now: merged[key(t)]=t
        save(path,list(merged.values()))
        print(json.dumps({"accepted":len(clean),"cached":len(merged)}))
    elif a.command=="prune":
        remaining=[t for t in existing if stamp(t["off_at"])>now]
        save(path,remaining)
        print(json.dumps({"deleted":len(existing)-len(remaining)}))
    else:
        if not a.date or not a.track or not a.race: p.error("--date --track --race required")
        rows=[t for t in existing if t["date"]==a.date and t["track"].casefold()==a.track.casefold() and t["race"]==a.race and stamp(t["published_at"])<=now<stamp(t["off_at"])]
        print(json.dumps({"tips":rows}))
if __name__=="__main__": main()
