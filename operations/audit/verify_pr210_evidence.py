"""Verify PR #210 archived bytes from the repository root with the acceptance ZIP at ../acceptance.zip."""
import hashlib,json,subprocess
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import numpy as np

sha=lambda b:hashlib.sha256(b).hexdigest()
e=json.loads(Path('operations/INVESTIGATION_2026-11-25_EVIDENCE.json').read_text())
z=ZipFile('../acceptance.zip')
assert sha(Path('../acceptance.zip').read_bytes()) == e['artifact_sha256']
all_coverage=Counter()
for item in e['commands']:
    p=item['run_id']+'/public/'
    f=z.read(p+'forecast.json');r=z.read(p+'receipt.json')
    assert sha(f)==item['forecast_sha256']==json.loads(r)['forecast_sha256']
    assert sha(r)==item['receipt_sha256']
    f=json.loads(f)
    assert f['provider_snapshot_sha256']==e['provider_snapshot_sha256']
    assert f['status']==item['status']
    assert all(x['country']==item['country'] for x in f['races'])
    for x in f['races']:
        for ver, model in x['models'].items():
            if model['status']!='SCORED':continue
            rows=model['ranked_runners']
            p0=np.array([q['odds']**-1 for q in rows]);p0/=p0.sum()
            c=np.array([q['score_trace']['feature_log_correction'] for q in rows])
            t=np.array([q['score_trace']['temperature'] for q in rows])
            pred=np.exp((np.log(p0)+c)/t);pred/=pred.sum()
            assert np.allclose(pred,[q['probability'] for q in rows],rtol=0,atol=1e-12)
            assert not model['betting_authorised']
            all_coverage.update((ver,q['score_trace']['observed_feature_count']) for q in rows)
    if item['run_id'].endswith('-1'):
        ok=[x for x in f['races'] if all(m['status']=='SCORED' for m in x['models'].values())]
        print('AU races scored by both:',len(ok),'same model top:',sum(len({m['ranked_runners'][0]['number'] for m in x['models'].values()})==1 for x in ok))
        for ver in ('V6','V7'):
            print(ver,'market top agreements:',sum((lambda rows:rows[0]['number']==min(rows,key=lambda q:q['odds'])['number'])(x['models'][ver]['ranked_runners']) for x in ok))
for item in e['original_requests']:
    raw={}
    for k in ['forecast','receipt']:
        raw[k]=subprocess.check_output(['git','show','origin/monty-operations-results:'+item[k+'_path']])
        assert sha(raw[k])==item[k+'_sha256']
    assert json.loads(raw['receipt'])['forecast_sha256']==sha(raw['forecast'])
    f=json.loads(raw['forecast'])
    r=next(r for r in f['races'] if r['meeting']=='Geelong' and str(r['race'])=='8')
    print(item['request_id'], [(v,m['status'],m.get('no_bet_reasons')) for v,m in r['models'].items()] if item['request_id']<208 else [(v,m['status']) for v,m in r['models'].items()])
print('Runner-level feature counts across archived commands:', all_coverage)
