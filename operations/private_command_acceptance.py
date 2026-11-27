"""One-off owner-authorised issue -> existing worker -> private delivery test.

Closed, namespaced staging issues isolate the unmerged candidate from the legacy
production queue. No production parser/state guard is changed. This is not proof
of the post-activation ordinary open-issue/iPhone path.
"""
from datetime import datetime
from pathlib import Path
import hashlib,json,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from monty_operations import TZ,utcnow,timestamp
from operations import client,issue_delivery,transport,worker
from operations.private_delivery import Sink
from operations.private_transport_probe import main as probe

PREFIX='[STAGING ONLY] '

def validated_staging_request(issue,day):
    if (issue.get('user',{}).get('login')!='Spankman' or issue.get('state')!='closed'
        or not str(issue.get('title','')).startswith(PREFIX)):
        raise ValueError('Owned closed staging issue required')
    original=dict(issue,title=issue['title'][len(PREFIX):])
    if not transport.addressed_to_monty(original):raise ValueError('Not an existing Monty command')
    req=transport.validated_request(original)
    if req['date']!=day or req.get('country')!='AU':raise ValueError('Current Australian request required')
    return req

def main():
    if (os.getenv('GITHUB_REF_NAME')!='recovery/puntersedge-operations-20261127'
        or os.getenv('GITHUB_EVENT_NAME')!='push' or os.getenv('GITHUB_RUN_ATTEMPT','1')!='1'):
        raise ValueError('First-attempt isolated staging push required')
    os.environ['PRIVATE_RESULTS_TOKEN']=os.getenv('MONTY_PRIVATE_RESULTS_TOKEN','')
    if probe()['status']!='PRIVATE_WRITE_VERIFIED':raise ValueError('Private write preflight failed; no provider calls')
    control=json.loads(Path('.monty/operations-staging.json').read_text())
    day=utcnow().astimezone(TZ).date().isoformat()
    if control.get('schema')!='monty.private-command-acceptance.v1' or control.get('date')!=day:
        raise ValueError('Current approved acceptance control required')
    entries=control['requests']
    if not 1<=len(entries)<=12 or len({e['issue'] for e in entries})!=len(entries):raise ValueError('Invalid bounded request set')
    run=os.environ['GITHUB_RUN_ID'];workflow='https://github.com/Spankman/Monty-Racing/actions/runs/'+run
    requests=[];created={}
    for entry in entries:
        issue=transport.api('issues/'+str(int(entry['issue'])))
        req=validated_staging_request(issue,day)
        requests.append((entry['issue'],req));created[entry['issue']]=issue['created_at']
    transport.ensure_results_branch()
    queued_at={}
    for number,req in requests:
        old=transport.read(f'requests/{number}.json')
        queued_at[number]=utcnow().isoformat()
        if old is None:
            worker.lifecycle(req,number,run+'-1-'+str(number),workflow,'QUEUED')
            issue_delivery.report(number,'ack','**ISOLATED STAGING — NOT PRODUCTION ACTIVATION**\nCommand `'+req['command']+'` accepted. Models and data gates unchanged. '+workflow)
    methods=[];original_api=transport.api
    def read_only(*args,**kwargs):
        method=kwargs.get('method',args[1] if len(args)>1 else 'GET');methods.append(method)
        if method!='GET':raise AssertionError('C attempted a mutation')
        return original_api(*args,**kwargs)
    transport.api=read_only
    try:pending=client.handle('C',request_id=requests[0][0])
    finally:transport.api=original_api
    # Reuse the existing worker including its genuine subprocess invocation,
    # provider/model routing, same-scope reuse, terminal delivery and receipts.
    worker.work_items=lambda *args:iter(requests)
    original_operate=worker.operate;executions=[]
    def bounded_operate(*args,**kwargs):
        if len(executions)>=control.get('maximum_new_executions',3):raise ValueError('Acceptance provider budget exhausted')
        executions.append(args[1]);return original_operate(*args,**kwargs)
    worker.operate=bounded_operate
    worker.main()
    sink=Sink();rows=[];private_verified={};c_methods=[]
    for number,req in requests:
        transport.api=read_only
        before=len(methods)
        try:result=client.handle('C',request_id=number)
        finally:transport.api=original_api
        c_methods+=methods[before:]
        index=transport.read(f'requests/{number}.json')
        public=transport.read(index['forecast_path'])
        private=public.get('private_delivery')
        verified=False
        if private:
            key=private['receipt_path']
            if key not in private_verified:
                receipt_raw=sink.read(key)
                assert hashlib.sha256(receipt_raw).hexdigest()==private['receipt_sha256']
                receipt=json.loads(receipt_raw)
                for name,digest in receipt['files'].items():
                    raw=sink.read(key.rsplit('/',1)[0]+'/'+name)
                    assert hashlib.sha256(raw).hexdigest()==digest
                private_verified[key]=True
            verified=True
        terminal=issue_delivery.find(number,'terminal')
        rows.append(dict(request_id=number,submitted_command=next(e['command'] for e in entries if e['issue']==number),command=req['command'],
            run_id=index['run_id'],request_status=result['request_status'],semantic_outcome=result['semantic_outcome'],
            delivery_status=result.get('delivery_status'),freshness=result.get('freshness'),fresh_race_assessments=result.get('fresh_race_assessments'),
            forecast_sha256=index['forecast_sha256'],receipt_sha256=index['receipt_sha256'],private_delivery=private,
            private_files_verified=verified,terminal_url=terminal.get('html_url') if terminal else None,
            observed_at=utcnow().isoformat(),request_created_at=created[number],queued_at=queued_at[number],terminal_at=terminal.get('created_at') if terminal else None,
            submission_to_terminal_seconds=(timestamp(terminal['created_at'])-timestamp(created[number])).total_seconds() if terminal else None,
            queued_to_terminal_seconds=(timestamp(terminal['created_at'])-timestamp(queued_at[number])).total_seconds() if terminal else None))
    report=dict(schema='monty.private-command-acceptance.v1',commit=os.environ['GITHUB_SHA'],workflow_url=workflow,date=day,
        staging_namespace=True,issues_deliberately_closed=True,ordinary_open_issue_phone_acceptance=False,
        pending_C=dict(status=pending['request_status'],methods=methods[:len(methods)-len(c_methods)]),
        completed_C_methods=c_methods,C_writes=sum(m!='GET' for m in methods),new_executions=executions,
        maximum_reserved_PE_credits=10*len(executions),requests=rows,production_changed=False)
    out=Path('operations_output/private-command-acceptance');out.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode();(out/'report.json').write_bytes(raw)
    (out/'report.sha256').write_text(hashlib.sha256(raw).hexdigest()+'  report.json\n')
    print(json.dumps(dict(requests=len(rows),executions=len(executions),private_verified=sum(r['private_files_verified'] for r in rows),C_writes=report['C_writes'])))
    if not all(r['request_status']=='COMPLETED' and r['terminal_url'] and r['private_files_verified'] for r in rows):
        raise SystemExit('Some commands failed; inspect semantic outcomes')

if __name__=='__main__':main()
