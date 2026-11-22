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
PENDING = {'QUEUED', 'RUNNING'}


def api(endpoint, method='GET', body=None, optional=False):
    args=['gh','api','repos/'+REPO+'/'+endpoint,'--method',method]
    if body is not None:args+=['--input','-']
    p=subprocess.run(args,input=json.dumps(body) if body is not None else None,capture_output=True,text=True,timeout=20)
    if p.returncode:
        if optional and 'HTTP 404' in p.stderr:return None
        raise RuntimeError('GitHub transport failed')
    return json.loads(p.stdout) if p.stdout.strip() else None


def read_bytes(path):
    document = api('contents/'+path+'?ref='+BRANCH, optional=True)
    return None if document is None else base64.b64decode(document['content'])


def read(path):
    raw = read_bytes(path)
    return None if raw is None else json.loads(raw)


def enqueue(req):
    params = {key: req[key] for key in ('date', 'country') if req.get(key)}
    issue = api('issues', 'POST', dict(title=PREFIX+req['command'], body=json.dumps(params)))
    return issue['number']


def request_state(index):
    if index is None:
        return 'QUEUED'
    return index.get('request_status') or ('FAILED' if index['status'] == 'FAILED' else 'COMPLETED')


def requests(*, include_processed=False):
    # Explicit pagination; author identity is checked, not body-supplied approval.
    state = 'all' if include_processed else 'open'
    for page in range(1,101):
        rows=api(f'issues?state={state}&sort=created&direction=desc&per_page=100&page={page}')
        for issue in rows:
            if 'pull_request' in issue or issue.get('user',{}).get('login')!='Spankman':continue
            if not issue['title'].startswith(PREFIX):continue
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
                if include_processed or request_state(read(f"requests/{issue['number']}.json")) in PENDING:
                    yield issue['number'],req
            except (ValueError,TypeError):continue
        if len(rows)<100:return
    raise RuntimeError('Request queue pagination exceeded bound')


def ensure_results_branch():
    if api('git/ref/heads/'+BRANCH, optional=True) is None:
        api('git/refs', 'POST', dict(ref='refs/heads/'+BRANCH, sha=os.environ['GITHUB_SHA']))


def write_index(path, index, *, immutable_terminal=False):
    existing = api('contents/'+path+'?ref='+BRANCH, optional=True)
    body = dict(message='Record Monty attempt status [skip ci]', branch=BRANCH,
                content=base64.b64encode((json.dumps(index, indent=2)+'\n').encode()).decode())
    if existing:
        if immutable_terminal:
            saved = json.loads(base64.b64decode(existing['content']))
            if request_state(saved) not in PENDING:
                if saved == index:
                    return
                raise ValueError('Request already settled')
        body['sha'] = existing['sha']
    api('contents/'+path, 'PUT', body)


def record_request(index):
    ensure_results_branch()
    write_index(f"requests/{index['request_id']}.json", index, immutable_terminal=True)


def publish(directory, run_id, day, issue=None, workflow_url=None):
    # The results branch contains sanitized derived views only.
    ensure_results_branch()
    allowed={'forecast.json','receipt.json','v6-official.json','v6-provisional.json',
             'v7-official.json','v7-provisional.json','v6-official.txt','v6-provisional.txt',
             'v7-official.txt','v7-provisional.txt','v6-official.html','v6-provisional.html',
             'v7-official.html','v7-provisional.html', 'v7-shadow.json','v7-shadow.txt','v7-shadow.html'}
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
    if issue is not None:
        state = 'FAILED' if receipt['status'] == 'FAILED' else 'COMPLETED'
        index.update(request_id=issue, request_status=state, workflow_url=workflow_url)
        record_request(index)
    else:
        index['workflow_url'] = workflow_url
        write_index(f'daily/{day}/latest.json', index)
    return index


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['queue','publish']);p.add_argument('--directory');p.add_argument('--run-id');p.add_argument('--date');p.add_argument('--issue',type=int)
    a=p.parse_args()
    if a.action=='queue':
        print(json.dumps([dict(issue=i,request=r) for i,r in requests()]))
    else:print(json.dumps(publish(a.directory,a.run_id,a.date,a.issue)))

if __name__=='__main__':main()
