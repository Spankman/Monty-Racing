"""Authenticated GitHub issue queue and append-only derived forecast publication.

No raw snapshots, historical data or secrets are published. Issue bodies are
strict JSON parameters, never instructions or executable shell text.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import sleep
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from monty_operations import command, timestamp
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
    if document is None:return None
    if document.get('encoding') not in ('base64',None) or not document.get('content'):
        # GitHub's Contents endpoint omits inline data above 1 MiB. Git blobs
        # remain read-only and preserve exact bytes for existing integrity checks.
        if not re.fullmatch(r'[0-9a-f]{40}',document.get('sha','')):raise ValueError('Missing file blob SHA')
        document=api('git/blobs/'+document['sha'])
        if document.get('encoding')!='base64':raise ValueError('Unsupported Git blob encoding')
    return base64.b64decode(document['content'])


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


def command_title(title):
    return re.sub(r'^monty command\s*:\s*', '', title.strip(), flags=re.I)


def addressed_to_monty(issue):
    if 'pull_request' in issue or (issue.get('user') or {}).get('login') != 'Spankman':
        return False
    title = (issue.get('title') or '').strip()
    if re.match(r'^(?:monty command\s*:|RM(?:V)?\d|(?:please\s+)?run\s+monty\b)', title, re.I):
        return True
    try:
        return command(title).get('meeting') is not None
    except ValueError:
        return False


def validated_request(issue):
    title = command_title(issue.get('title') or '')
    body = (issue.get('body') or '').strip()
    params = {}
    if body.startswith(('{', '[')):
        try:
            params = json.loads(body)
        except ValueError:
            raise ValueError('Invalid JSON options. Leave the body empty for today in Australia.') from None
        if not isinstance(params, dict) or set(params) - {'date', 'country'}:
            raise ValueError('Only date and country are valid JSON options.')
        if any(not isinstance(v, str) or not v.strip() for v in params.values()):
            raise ValueError('Date and country must be nonempty strings.')
    if 'date' not in params:
        params['date'] = timestamp(issue['created_at']).astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat()
    params['country'] = params.get('country', 'AU').upper()
    req = command(title, **params)
    if req['view'] == 'status':
        raise ValueError('C reads the originating issue. It does not start a run.')
    if body and not body.startswith(('{', '[')):
        try:
            redundant = command(command_title(body), **params)
        except ValueError:
            # The title owns the command. Ordinary body notes are inert.
            return req
        if redundant['command'] != req['command']:
            raise ValueError('Title and body specify different commands. Put the request in the title.')
    return req


def parse_request(issue):
    if not addressed_to_monty(issue):
        return None
    try:
        return validated_request(issue)
    except (ValueError, TypeError, KeyError):
        return None


def request_for_issue(number):
    issue = api(f'issues/{number}', optional=True)
    if issue and issue.get('state') == 'open':
        return parse_request(issue)
    return None


def recent_scope_index(req, issue, now):
    # Both engines are run on the same snapshot. A different view can share a
    # recent result, but the full-day and single-race scopes stay distinct.
    from datetime import timedelta
    from operations.client import scope
    since = (now - timedelta(seconds=90)).isoformat().replace('+00:00', 'Z')
    rows = api(f'issues?state=open&sort=created&direction=desc&per_page=20&since={since}')
    for row in rows:
        if row['number'] == issue:
            continue
        other = parse_request(row)
        if other and scope(other) == scope(req):
            index = read(f"requests/{row['number']}.json")
            if index and reusable(index, req, now):
                return index
    return None


def reusable(index, req, now):
    captured = index.get('captured_at')
    return bool(index.get('request_status') == 'COMPLETED' and index.get('source_mode') == 'LIVE'
                and index.get('provider') == os.getenv('MONTY_PRICE_PROVIDER','PuntersEdge')
                and index.get('forecast_path') and captured
                and 0 <= (now - timestamp(captured)).total_seconds() <= 90
                and index.get('models', {}).get(req['version'], {}).get('scored_races', 0) > 0)


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
    allowed.update({'record.json','record.json.receipt.json','delivery-manifest.json','compact-v6-official.json','compact-v6-provisional.json','compact-v7-official.json','compact-v7-provisional.json','compact-v7-shadow.json'})
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
               status=receipt['status'],source_mode=receipt['source_mode'],provider=receipt.get('provider'),
               receipt_path=prefix+'receipt.json',forecast_path=prefix+'forecast.json',
               forecast_sha256=receipt['forecast_sha256'],generated_at=receipt['generated_at'],
               workflow_url=workflow_url, captured_at=saved_forecast.get('captured_at'),
               valid_until=saved_forecast.get('valid_until'),models=receipt.get('models',{}),
               forecast_integrity_verified=True,
               receipt_sha256=hashlib.sha256((Path(directory)/'receipt.json').read_bytes()).hexdigest())
    if receipt.get('delivery_manifest_sha256'):
        manifest_file=Path(directory)/'delivery-manifest.json'
        if hashlib.sha256(manifest_file.read_bytes()).hexdigest()!=receipt['delivery_manifest_sha256']:raise ValueError('Delivery manifest mismatch')
        delivery=json.loads(manifest_file.read_text())
        if delivery.get('run_id')!=run_id or delivery.get('forecast_sha256')!=receipt['forecast_sha256']:raise ValueError('Delivery references another forecast')
        for preview in delivery.get('previews',[]):
            if preview['path'] not in allowed or not preview['path'].startswith('compact-'):raise ValueError('Unsafe preview path')
            if hashlib.sha256((Path(directory)/preview['path']).read_bytes()).hexdigest()!=preview['sha256']:raise ValueError('Preview integrity mismatch')
        index.update(delivery_manifest_path=prefix+'delivery-manifest.json',delivery_manifest_sha256=receipt['delivery_manifest_sha256'])
    record_file=Path(directory)/'record.json'
    if record_file.exists():
        record_receipt=record_file.with_name('record.json.receipt.json')
        record=json.loads(record_file.read_text());verified=json.loads(record_receipt.read_text())
        if hashlib.sha256(record_file.read_bytes()).hexdigest()!=verified['record_sha256'] or record['provider_snapshot_sha256']!=saved_forecast['provider_snapshot_sha256']:raise ValueError('Prospective record integrity mismatch')
        index.update(prospective_record_path=prefix+'record.json',prospective_record_sha256=verified['record_sha256'],prospective_receipt_path=prefix+'record.json.receipt.json',prospective_receipt_sha256=hashlib.sha256(record_receipt.read_bytes()).hexdigest(),prospective_cohort_admitted=record['cohort_admitted'])
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
