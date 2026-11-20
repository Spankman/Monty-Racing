"""Poll authorised GitHub race requests; post an idempotent, fail-closed result.

Designed for scheduled and PR-triggered GitHub Actions, because issue-created events can be
suppressed when an issue is created by an integration token.\n# Single-race poll trigger: Launceston R7, 20 November 2026.
"""
import datetime as dt
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

REPO=os.environ.get("GITHUB_REPOSITORY","Spankman/Monty-Racing")
MARKER="<!-- monty-race-request-v1 -->"
TITLE=re.compile(r"Monty race: ([A-Za-z][A-Za-z .'-]{1,59}) ([1-9]|1[0-9]|20)$")
TZ=ZoneInfo("Australia/Brisbane")
# Every explicitly requested single race is eligible for analysis regardless of
# maiden, two-year-old or hurdle classification. Daily selection filters remain separate.
SINGLE_RACE_CLASS_OVERRIDE=True

def gh(*args):
    p=subprocess.run(["gh",*args],text=True,capture_output=True,check=True)
    return p.stdout

def pending():
    data=json.loads(gh("api",f"repos/{REPO}/issues?state=open&per_page=100"))
    return [x for x in data if "pull_request" not in x and TITLE.fullmatch(x["title"])]

def already_handled(number):
    comments=json.loads(gh("api",f"repos/{REPO}/issues/{number}/comments?per_page=100"))
    return any(MARKER in c.get("body","") for c in comments)

def comment(number,body):
    with tempfile.NamedTemporaryFile("w",encoding="utf8",delete=False) as f:
        f.write(MARKER+"\n"+body+"\n")
        path=f.name
    try:
        gh("issue","comment",str(number),"--repo",REPO,"--body-file",path)
    finally:
        Path(path).unlink(missing_ok=True)

def score(track,race,date):
    from krok_adapter import fetch,normalize
    from research_frozen_linear_replay import run
    from monty_single_race_research import select
    from monty_single_race_ladder import choose
    key=os.environ.get("KROK_API_KEY")
    if not key:raise RuntimeError("KROK_API_KEY is missing")
    snapshot,audit=normalize(fetch(date,key),date,allow_restricted_classes=True)
    # Classification is deliberately not used to reject an explicit race request.
    # Scope completeness validation to the requested race. Unrelated
    # incomplete races must not prevent this race from being evaluated.
    target=[r for r in snapshot["races"] if str(r["meeting"]).strip().casefold()==track.strip().casefold() and str(r["race"])==str(race)]
    if len(target)!=1:
        raise ValueError("Requested race absent or ambiguous")
    runners=[r for r in snapshot["runners"] if str(r["meeting"]).strip().casefold()==track.strip().casefold() and str(r["race"])==str(race)]
    if len(runners)!=int(target[0]["expected_active_runners"]):
        raise ValueError("Requested race field incomplete")
    snapshot={**snapshot,"races":target,"runners":runners}
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        (p/"snapshot.json").write_text(json.dumps(snapshot))
        run(p/"snapshot.json",p/"scores.csv")
        result=select(p/"scores.csv",track,race)
    # Research output cannot authorise any bet without verified odds and
    # approved, calibrated probabilities. Never print the entire leaderboard.
    ladder=choose([{"number":r["number"],"horse":r["horse"],
                    "research_prob":r["research_probability"],"odds":r["odds"]}
                   for r in result["runners"]],approved=False)
    leader=ladder["best"]
    return (f"**{track} R{race} — NO BET (research only)**\n\n"
            f"**Top-ranked: #{leader['number']} {leader['horse']}**\n\n"
            "BB → Q → T → FF: no authorised value bet. "
            "Verified prices and approved probabilities are required.")

def main():
    today=dt.datetime.now(TZ).date()
    # Process newest requests first; old unresolved issues must not starve live requests.
    for issue in sorted(pending(), key=lambda x: x["created_at"], reverse=True)[:100]:
        n=issue["number"]
        if issue["user"]["login"] != REPO.split("/")[0]:
            continue
        if already_handled(n):
            continue
        m=TITLE.fullmatch(issue["title"])
        created=dt.datetime.fromisoformat(issue["created_at"].replace("Z","+00:00")).astimezone(TZ).date()
        if created!=today:
            comment(n,f"**NO BET.** Request was created on {created}; today's date is {today}. Historical requests are not scored as live.")
            continue
        try:
            body=score(m.group(1),int(m.group(2)),today.isoformat())
        except Exception as exc:
            # Do not leak provider payload, tokens, or stack traces into public issues.
            body="**NO BET — scoring failed or race not verified.** See the workflow logs for diagnostic details."
            print(f"Race request #{n} failed: {type(exc).__name__}: {str(exc)[:160]}")
        comment(n,body)
        print(f"Handled issue #{n}")

if __name__=="__main__":main()
