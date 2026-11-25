"""Idempotent staging-only Git commits using existing gh authentication.

No workflow dispatch, merge, production write, billing or credential output.
An atomic commit contains both immutable launch ID and push-trigger marker.
"""
import argparse,base64,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from operations.trial.program import validate_plan,protocol
class Missing(RuntimeError):pass
BRANCH='trial/puntersedge-acceptance-20261126'
REPO='Spankman/Monty-Racing'
def api(path,method='GET',body=None):
    command=['gh','api',f'repos/{REPO}/'+path,'--method',method]
    data=None
    if body is not None:command+=['--input','-'];data=json.dumps(body)
    result=subprocess.run(command,input=data,text=True,capture_output=True)
    if result.returncode:
        if 'HTTP 404' in result.stderr:raise Missing('GitHub object absent')
        raise RuntimeError('GitHub request failed (no response body logged)')
    return json.loads(result.stdout)
def current(path):
    try:
        v=api('contents/'+path+'?ref='+BRANCH)
        return json.loads(base64.b64decode(v['content']))
    except Missing:return None

def atomic(files,message):
    head=api('git/ref/heads/'+BRANCH)['object']['sha'];commit=api('git/commits/'+head)
    tree=[]
    for path,value in files.items():
        blob=api('git/blobs','POST',dict(content=json.dumps(value,indent=2)+'\n',encoding='utf-8'))
        tree.append(dict(path=path,mode='100644',type='blob',sha=blob['sha']))
    tree=api('git/trees','POST',dict(base_tree=commit['tree']['sha'],tree=tree))
    made=api('git/commits','POST',dict(message=message,tree=tree['sha'],parents=[head]))
    api('git/refs/heads/'+BRANCH,'PATCH',dict(sha=made['sha'],force=False))
    return made['sha']
def launch(day,mode):
    if day not in protocol()['dates'] or mode not in ('plan','capture','results'):raise ValueError('Outside approved trial')
    path=f'operations/trial/launches/{day}-{mode}.json'
    old=current(path)
    if old:return dict(status='ALREADY_LAUNCHED',request=old)
    if mode!='plan':
        p=current(f'operations/trial/plans/{day}.json')
        if p is None:raise ValueError('No immutable preregistration; run plan first')
        validate_plan(p)
    control=dict(date=day,mode=mode,request_id=f'PE-AU-20261126-6D-{day}-{mode}',requested_at=datetime.now(timezone.utc).isoformat())
    commit=atomic({path:control,'operations/trial/control.json':control},f"trial: {day} {mode} (idempotent staged acquisition)")
    return dict(status='LAUNCHED',commit=commit,request=control)
def register(path):
    plan=validate_plan(json.loads(Path(path).read_text()));target=f"operations/trial/plans/{plan['date']}.json"
    old=current(target)
    if old:
        if old!=plan:raise ValueError('Immutable plan already differs')
        return dict(status='ALREADY_REGISTERED',plan_sha256=plan['plan_sha256'])
    commit=atomic({target:plan},'trial: freeze prospective preregistration '+plan['date'])
    return dict(status='REGISTERED',commit=commit,plan_sha256=plan['plan_sha256'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--date');p.add_argument('--mode',choices=['plan','capture','results']);p.add_argument('--register')
    a=p.parse_args();print(json.dumps(register(a.register) if a.register else launch(a.date,a.mode)))
if __name__=='__main__':main()
