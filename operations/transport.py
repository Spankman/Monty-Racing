"""Authenticated GitHub issue queue and append-only derived forecast publication.

No raw snapshots, historical data or secrets are published. Issue bodies are
strict JSON parameters, never instructions or executable shell text.
"""
import argparse
import base64
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import sleep
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from monty_operations import command
REPO='Spankman/Monty-Racing'
BRANCH=os.environ.get('OPERATIONS_RESULTS_BRANCH','monty-operations-results')
PREFIX='Monty command: '
PENDING = {'QUEUED', 'RUNNING'}


class GitHubError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'GitHub HTTP {status}' if status else 'GitHub transport unavailable')


def api(endpoint, method='GET', body=None, optional=False):
    args=['gh','api','repos/'+REPO+'/'+endpoint,'--method',method]
    if body is not None:args+=['--input','-']
    p=subprocess.run(args,input=json.dumps(body) if body is not None else None,capture_output=True,text=True,timeout=10)
    if p.returncode:
        match = re.search(r'\bHTTP (\d{3})\b', p.stderr)
        status = int(match.group(1)) if match else None
        if optional and status == 404:
            return None
        raise GitHubError(status)
    return json.loads(p.stdout) if p.stdout.strip() else None


def retry(operation, *, conflicts=False):
    """Retry transient transport errors and atomic ref conflicts only."""
    transient = {None, 408, 429, 500, 502, 503, 504}
    if conflicts:
        transient.update({409, 422})
    for attempt in range(3):
        try:
            return operation()
        except GitHubError as exc:
            if exc.status not in transient or attempt == 2:
                raise
        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise
        sleep(0.5 * (attempt + 1))


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


def parse_request(issue):
    title = issue.get('title') or ''
    if ('pull_request' in issue or (issue.get('user') or {}).get('login') != 'Spankman'
            or not title.startswith(PREFIX)):
        return None
    try:
        params = json.loads(issue.get('body') or '{}')
        if not isinstance(params, dict) or set(params) - {'date', 'country'}:
            return None
        if not params.get('date'):
            # Undated requests are tied to the Brisbane date on the original issue.
            created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
            params['date'] = created.astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat()
        req = command(title[len(PREFIX):], **params)
        return None if req['view'] == 'status' else req
    except (ValueError, TypeError, KeyError):
        return None


def request_for_issue(number):
    issue = api(f'issues/{number}', optional=True)
    if issue and issue.get('state') == 'open':
        return parse_request(issue)
    return None


def requests(*, include_processed=False):
    # Explicit pagination; author identity is checked, not body-supplied approval.
    state = 'all' if include_processed else 'open'
    for page in range(1,101):
        rows=api(f'issues?state={state}&sort=created&direction=desc&per_page=100&page={page}')
        for issue in rows:
            req = parse_request(issue)
            if req is not None and (include_processed or request_state(read(f"requests/{issue['number']}.json")) in PENDING):
                yield issue['number'], req
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


def publish(directory, run_id, day, issue=None, workflow_url=None, *, request=None):
    # Validate the entire allowlist BEFORE touching GitHub. A single tree/commit
    # publishes the complete forecast, receipt, views and terminal index together.
    allowed={'forecast.json','receipt.json','v6-official.json','v6-provisional.json',
             'v7-official.json','v7-provisional.json','v6-official.txt','v6-provisional.txt',
             'v7-official.txt','v7-provisional.txt','v6-official.html','v6-provisional.html',
             'v7-official.html','v7-provisional.html', 'v7-shadow.json','v7-shadow.txt','v7-shadow.html'}
    files=sorted(Path(directory).iterdir())
    if any(not file.is_file() or file.is_symlink() or file.name not in allowed for file in files):
        raise ValueError('Unapproved public file')
    receipt=json.loads((Path(directory)/'receipt.json').read_text())
    import hashlib
    forecast=(Path(directory)/'forecast.json').read_bytes()
    saved_forecast=json.loads(forecast)
    if (receipt['forecast_sha256']!=hashlib.sha256(forecast).hexdigest() or receipt['run_id']!=run_id
        or saved_forecast.get('run_id')!=run_id or saved_forecast.get('status')!=receipt['status']
        or saved_forecast.get('date')!=day or receipt.get('date')!=day):
        raise ValueError('Forecast/receipt integrity mismatch')
    prefix='runs/'+day+'/'+run_id+'/'
    index=dict(schema='monty.operations.index.v1',date=day,run_id=run_id,
               status=receipt['status'],source_mode=receipt['source_mode'],
               receipt_path=prefix+'receipt.json',forecast_path=prefix+'forecast.json',
               forecast_sha256=receipt['forecast_sha256'],generated_at=receipt['generated_at'],
               workflow_url=workflow_url, captured_at=saved_forecast.get('captured_at'),
               valid_until=saved_forecast.get('valid_until'),models=receipt.get('models',{}),
               forecast_integrity_verified=True,
               receipt_sha256=hashlib.sha256((Path(directory)/'receipt.json').read_bytes()).hexdigest())
    if request is not None:index['request']=request
    if issue is not None:
        state = 'FAILED' if receipt['status'] == 'FAILED' else 'COMPLETED'
        index.update(request_id=issue, request_status=state)
        path=f'requests/{issue}.json'
    else:path=f'daily/{day}/latest.json'
    ensure_results_branch()
    # Pin reads and the commit parent to the same branch tip. No force pushes.
    parent=api('git/ref/heads/'+BRANCH)['object']['sha']
    if api('contents/'+prefix.rstrip('/')+'?ref='+parent,optional=True) is not None:
        raise ValueError('Immutable forecast path already exists')
    existing=api('contents/'+path+'?ref='+parent,optional=True)
    if issue is not None and existing:
        saved=json.loads(base64.b64decode(existing['content']))
        if request_state(saved) not in PENDING:raise ValueError('Request already settled')
    tree=api('git/commits/'+parent)['tree']['sha']
    entries=[dict(path=prefix+file.name,mode='100644',type='blob',content=file.read_text()) for file in files]
    entries.append(dict(path=path,mode='100644',type='blob',content=json.dumps(index,indent=2)+'\n'))
    tree=api('git/trees','POST',dict(base_tree=tree,tree=entries))['sha']
    commit=api('git/commits','POST',dict(message='Record immutable Monty forecast and receipt [skip ci]',tree=tree,parents=[parent]))['sha']
    api('git/refs/heads/'+BRANCH,'PATCH',dict(sha=commit,force=False))
    return index


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['queue','publish']);p.add_argument('--directory');p.add_argument('--run-id');p.add_argument('--date');p.add_argument('--issue',type=int)
    a=p.parse_args()
    if a.action=='queue':
        print(json.dumps([dict(issue=i,request=r) for i,r in requests()]))
    else:print(json.dumps(publish(a.directory,a.run_id,a.date,a.issue)))

if __name__=='__main__':main()
