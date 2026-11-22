"""Run queued commands safely without executing request text as code."""
from datetime import datetime, time
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from operations.transport import requests, publish, read
from monty_operations import command


def daily_due(now, latest):
    return now.time() >= time(8,10) and latest is None


def main():
    now=datetime.now(ZoneInfo('Australia/Brisbane'))
    day=now.date().isoformat()
    mode=os.environ.get('OPERATIONS_MODE','daily')
    items=list(requests()) if mode=='queue' else [(None,command(os.environ.get('OPERATIONS_COMMAND') or 'RM6',os.environ.get('OPERATIONS_DATE') or day))]
    # Issue events filter to their exact issue; queue schedule handles dropped
    # integration-token issue events and requests received while a job is busy.
    issue=os.environ.get('OPERATIONS_ISSUE','')
    if issue:items=[x for x in items if x[0]==int(issue)]
    # Catch up a missed/overwritten 08:10 cron slot on the next queue tick.
    # Never silently retry an already-published FAILED daily attempt.
    if mode=='queue' and not issue and daily_due(now,read('daily/'+day+'/latest.json')):
        items.insert(0,(None,command('RM6',day)))
    items=items[:10]
    for number,req in items:
        if number and read('requests/'+str(number)+'.json'):continue
        run_id=os.environ['GITHUB_RUN_ID']+'-'+os.environ.get('GITHUB_RUN_ATTEMPT','1')+'-'+(str(number) if number else 'daily')
        out=Path('operations_output')/run_id
        args=[sys.executable,'monty_operations.py','--command',req['command'],'--date',req['date'],
              '--output',str(out),'--v7-root','v7_engine','--run-id',run_id]
        if req.get('country'):args+=['--country',req['country']]
        p=subprocess.run(args,capture_output=True,text=True,timeout=1000)
        if not (out/'public/receipt.json').exists():
            # A dependency/interpreter failure must replace the latest-attempt
            # pointer with failure, not leave yesterday's success looking fresh.
            from operations.failure import failed
            failed(out,run_id,req['date'],'runner_startup_failed')
        index=publish(out/'public',run_id,req['date'],number)
        print(json.dumps(index))

if __name__=='__main__':main()
