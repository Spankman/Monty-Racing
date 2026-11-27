"""One owner-authorised private transport probe; no provider calls or secrets output."""
import base64,hashlib,json,os
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError

REPO='Spankman/Monty-Private-Archive'
BRANCH='monty-operational-private-results'

def main():
    report=dict(schema='monty.private-transport-capability.v1',repository=REPO,branch=BRANCH,
                credential_value_published=False,permissions_changed=False,provider_calls=0,
                runtime_commit=os.environ['GITHUB_SHA'],workflow_url='https://github.com/Spankman/Monty-Racing/actions/runs/'+os.environ['GITHUB_RUN_ID'])
    token=os.getenv('PRIVATE_RESULTS_TOKEN','')
    report['credential_configured']=bool(token)
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self,*args):return None
    def api(path,method='GET',body=None):
        endpoint='https://api.github.com/repos/'+REPO
        request=Request(endpoint+('/'+path if path else ''),method=method,
            headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Monty-private-capability/1.0'},
            data=json.dumps(body).encode() if body is not None else None)
        with build_opener(NoRedirect()).open(request,timeout=15) as response:return json.load(response)
    stage='credential'
    try:
        if not token:raise ValueError('Existing archive credential absent')
        stage='repository_metadata'
        repo=api('');report['repository_private']=repo.get('private') is True
        if not report['repository_private']:raise ValueError('Private sink required')
        report['reported_push_permission']=repo.get('permissions',{}).get('push')
        # Probe only the already-created dedicated branch; do not change access.
        stage='private_branch'
        ref=api('git/ref/heads/'+BRANCH)
        report['branch_present']=bool(ref.get('object',{}).get('sha'))
        raw=(json.dumps(dict(schema='monty.hosted-private-probe.v1',run_id=os.environ['GITHUB_RUN_ID'],provider_data=False),sort_keys=True)+'\n').encode()
        path='operational-probes/hosted-'+os.environ['GITHUB_RUN_ID']+'.json'
        stage='private_write'
        created=api('contents/'+path,'PUT',dict(branch=BRANCH,message='Verify owner-only hosted result transport',content=base64.b64encode(raw).decode()))
        stage='private_readback'
        saved=api('contents/'+path+'?ref='+created['commit']['sha'])
        if base64.b64decode(saved['content'])!=raw:raise ValueError('private_readback_mismatch')
        report.update(status='PRIVATE_WRITE_VERIFIED',readback_verified=True,path=path,sha256=hashlib.sha256(raw).hexdigest(),commit=created['commit']['sha'])
    except HTTPError as exc:report.update(status='PRIVATE_TRANSPORT_BLOCKED',http_status=exc.code)
    except ValueError:report.update(status='PRIVATE_TRANSPORT_BLOCKED',blocker='private_writer_credential_absent' if not token else 'private_destination_not_confirmed')
    except Exception as exc:report.update(status='PRIVATE_TRANSPORT_BLOCKED',error=type(exc).__name__)
    report['stage']=stage
    out=Path('operations_output/private-transport-probe');out.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(report,sort_keys=True,indent=2).encode();(out/'report.json').write_bytes(raw)
    (out/'report.sha256').write_text(hashlib.sha256(raw).hexdigest()+'  report.json\n')
    print(json.dumps(report))
    return report
if __name__=='__main__':
    result=main()
    if result['status']!='PRIVATE_WRITE_VERIFIED':raise SystemExit(2)
