"""Poll authorised GitHub race requests; post an idempotent, fail-closed result.

Designed for scheduled and PR-triggered GitHub Actions, because issue-created events can be
suppressed when an issue is created by an integration token.
# Trigger Launceston R9 win-odds audit rerun.
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
    return any(MARKER in c.get("body","") or "genuine V7 PROVISIONAL" in c.get("body","") or "Monty could not verify and score this race" in c.get("body","") for c in comments)

def comment(number,body):
    with tempfile.NamedTemporaryFile("w",encoding="utf8",delete=False) as f:
        f.write(MARKER+"\n"+body+"\n")
        path=f.name
    try:
        gh("issue","comment",str(number),"--repo",REPO,"--body-file",path)
    finally:
        Path(path).unlink(missing_ok=True)

def score(track,race,date):
    """Run the genuine V7 engine from its pinned development branch checkout."""
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/"result"
        cmd=["python","-m","v7.run_live_single_race","--meeting",track,
             "--race",str(race),"--date",date,"--country","AU",
             "--output-dir",str(out),"--allow-restricted"]
        subprocess.run(cmd,cwd="v7_engine",check=True,capture_output=True,text=True)
        p=out/"v7"/"provisional_selection.json"
        d=json.loads(p.read_text(encoding="utf8"))
    if d.get("status")!="PROVISIONAL_V7_PROVIDER_UNVERIFIED" or d.get("betting_authorised") is not False:
        raise ValueError("Unexpected V7 result status")
    ranked=d.get("ordered",[])
    ladder=d.get("fixed_win_price_progression",{})
    nums=[str(n) for n in ladder.get("numbers",[])]
    if not ranked or not nums:
        raise ValueError("V7 produced no verifiable selection ladder")
    lookup={str(h["number"]):h for h in ranked}
    if any(n not in lookup for n in nums):
        raise ValueError("Progression runner absent from V7 ranking")
    selected=[lookup[n] for n in nums]
    display=" → ".join(
        (f"**#{h['number']} {h['horse']}**" if i==0
         else f"#{h['number']} {h['horse']}")
        for i,h in enumerate(selected))
    prices="; ".join(f"#{h['number']} {h['horse']} ${float(h['fixed_win_odds']):.2f}"
                     for h in selected)
    verdict=d.get("win_value_diagnostic",{}).get("betting_decision","NO BET — unvalidated V7")
    return (f"**{track} R{race} — genuine V7 PROVISIONAL — {ladder.get('type','UNKNOWN')}**\\n\\n"
            f"{display}\\n\\nFixed WIN odds: {prices}\\n\\n"
            f"**{verdict}**\\n\\n"
            "Model probabilities are not prospectively validated; no betting authorisation. "
            "Progression is based on fixed win prices, not exotic payouts.")


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
