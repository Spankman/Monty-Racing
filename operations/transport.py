"""Authenticated GitHub issue queue and append-only derived forecast publication.

No raw snapshots, historical data or secrets are published. Issue bodies are
strict JSON parameters, never instructions or executable shell text.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from monty_operations import command
REPO='Spankman/Monty-Racing'
BRANCH='monty-operations-results'
PREFIX='Monty command: '


def api(endpoint, method='GET', body=None, optional=False):
    args=['gh','api','repos/'+REPO+'/'+endpoint,'--method',method]
    if body is not None:args+=['--input','-']
    p=subprocess.run(args,input=json.dumps(body) if body is not None else None,capture_output=True,text=True)
    if p.returncode:
        if optional and 'HTTP 404' in p.stderr:return None
        raise RuntimeError('GitHub transport failed')
    return json.loads(p.stdout) if p.stdout.strip() else None


def read(path):
    d=api('contents/'+path+'?ref='+BRANCH,optional=True)
    if d is None:return None
    return json.loads(base64.b64decode(d['content']))


def requests():
    # Explicit pagination; author identity is checked, not body-supplied approval.
    for page in range(1,101):
        rows=api(f'issues?state=open&per_page=100&page={page}')
        for issue in rows:
            if 'pull_request' in issue or issue.get('user',{}).get('login')!='Spankman':continue
            if not issue['title'].startswith(PREFIX):continue
            if read('requests/'+str(issue['number'])+'.json'):continue
            try:
                params=json.loads(issue.get('body') or '{}')
                if not isinstance(params,dict) or set(params)-{'date','country'}:continue
                req=command(issue['title'][len(PREFIX):],**params)
                if req['view']=='status':continue
                # Undated requests are tied to the creation date, never replayed
                # days later against a different card.
                from zoneinfo import ZoneInfo
                from datetime import datetime
                created=datetime.fromisoformat(issue['created_at'].replace('Z','+00:00')).astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat()
                if not params.get('date'):req['date']=created
                yield issue['number'],req
            except (ValueError,TypeError):continue
        if len(rows)<100:return
    raise RuntimeError('Request queue pagination exceeded bound')


def publish(directory, run_id, day, issue=None):
    # Result branch contains code already public in this repository plus only
    # sanitized derived forecast views. No archive or private worktree is staged.
    ref=api('git/ref/heads/'+BRANCH,optional=True)
    if ref is None:
        api('git/refs','POST',dict(ref='refs/heads/'+BRANCH,sha=os.environ['GITHUB_SHA']))
    allowed={'forecast.json','receipt.json','v6-official.json','v6-provisional.json',
             'v7-official.json','v7-provisional.json','v6-official.txt','v6-provisional.txt',
             'v7-official.txt','v7-provisional.txt','v6-official.html','v6-provisional.html',
             'v7-official.html','v7-provisional.html'}
    prefix='runs/'+day+'/'+run_id+'/'
    for file in sorted(Path(directory).iterdir()):
        if file.name not in allowed:raise ValueError('Unapproved public file')
        path=prefix+file.name
        if api('contents/'+path+'?ref='+BRANCH,optional=True) is not None:
            raise ValueError('Immutable forecast path already exists')
        api('contents/'+path,'PUT',dict(message='Record immutable Monty derived forecast [skip ci]',
             branch=BRANCH,content=base64.b64encode(file.read_bytes()).decode()))
    receipt=json.loads((Path(directory)/'receipt.json').read_text())
    index=dict(schema='monty.operations.index.v1',date=day,run_id=run_id,
               status=receipt['status'],source_mode=receipt['source_mode'],
               receipt_path=prefix+'receipt.json',forecast_path=prefix+'forecast.json',
               forecast_sha256=receipt['forecast_sha256'],generated_at=receipt['generated_at'])
    if issue:
        path='requests/'+str(issue)+'.json'
        if read(path) is not None:raise ValueError('Request already settled')
        api('contents/'+path,'PUT',dict(message='Complete Monty request [skip ci]',branch=BRANCH,
             content=base64.b64encode((json.dumps(index,indent=2)+'\n').encode()).decode()))
    else:
        path='daily/'+day+'/latest.json'
        existing=api('contents/'+path+'?ref='+BRANCH,optional=True)
        body=dict(message='Update latest Monty attempt pointer [skip ci]',branch=BRANCH,
                  content=base64.b64encode((json.dumps(index,indent=2)+'\n').encode()).decode())
        if existing:body['sha']=existing['sha']
        api('contents/'+path,'PUT',body)
    return index


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['queue','publish']);p.add_argument('--directory');p.add_argument('--run-id');p.add_argument('--date');p.add_argument('--issue',type=int)
    a=p.parse_args()
    if a.action=='queue':
        print(json.dumps([dict(issue=i,request=r) for i,r in requests()]))
    else:print(json.dumps(publish(a.directory,a.run_id,a.date,a.issue)))

if __name__=='__main__':main()
