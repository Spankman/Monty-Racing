"""Owner-private derived forecast delivery using the existing private Git repo.

No raw provider responses, keys or historical inputs. Public Git receives only
receipt pointers. Personal PE licence §§3.4/8.1/8.4; never public-price display.
Git provides tamper evidence, not WORM or guaranteed deletion of past commits.
"""
import base64,hashlib,json,os,re
from pathlib import Path
import subprocess

REPO='Spankman/Monty-Private-Archive'
BRANCH='monty-operational-private-results'
PERMISSION='https://puntersedge.online/terms#section-8'
TERMS_SHA='0933f504bd267d2e4309dc0a6eb36ef1c84614143b66927aebd499ac5618a2c9'

class PrivateDeliveryError(RuntimeError):pass

def encoded(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()

class Sink:
    def __init__(self,token=None):
        self.token=token or os.getenv('MONTY_PRIVATE_RESULTS_TOKEN','')
        if not self.token:raise PrivateDeliveryError('private_writer_credential_absent')
    def api(self,path,method='GET',body=None,optional=False):
        env=dict(os.environ,GH_TOKEN=self.token)
        args=['gh','api','repos/'+REPO+'/'+path,'--method',method]
        if body is not None:args+=['--input','-']
        r=subprocess.run(args,input=json.dumps(body) if body is not None else None,text=True,capture_output=True,timeout=20,env=env)
        if r.returncode:
            if optional and 'HTTP 404' in r.stderr:return None
            raise PrivateDeliveryError('private_github_write_or_access_failed')
        return json.loads(r.stdout)
    def read(self,path):
        item=self.api('contents/'+path+'?ref='+BRANCH,optional=True)
        if item is None:return None
        if not item.get('content'):
            item=self.api('git/blobs/'+item['sha'])
        return base64.b64decode(item['content'])
    def commit(self,files):
        repo=self.api('')
        if repo.get('private') is not True:raise PrivateDeliveryError('private_repository_required')
        head=self.api('git/ref/heads/'+BRANCH)['object']['sha']
        parent=self.api('git/commits/'+head)
        tree=[]
        for name,raw in files.items():
            blob=self.api('git/blobs','POST',dict(content=base64.b64encode(raw).decode(),encoding='base64'))
            tree.append(dict(path=name,mode='100644',type='blob',sha=blob['sha']))
        made_tree=self.api('git/trees','POST',dict(base_tree=parent['tree']['sha'],tree=tree))
        made=self.api('git/commits','POST',dict(message='Private Monty derived forecasts [skip ci]',tree=made_tree['sha'],parents=[head]))
        self.api('git/refs/heads/'+BRANCH,'PATCH',dict(sha=made['sha'],force=False))
        return made['sha']

def derived_forecast(forecast):
    """Exclude original feature matrices/contributions; retain own ranked outputs."""
    allowed={'status','official_classification','prediction_classification','betting_decision','assessment_level',
        'model_version','model_commit','ordered_selections','ranked_runners','progression_bet_type','recommended_bet_type',
        'best_bets','best_chance','roughies','no_bet_reasons','betting_authorised','decision_at','bookmaker',
        'quote_capture_at','quoted_at','market_integrity','ruffies_to_watch','value_selection','most_likely',
        'provisional_classification','feature_evidence','model_inference'}
    value={k:forecast[k] for k in ('schema','date','timezone','run_id','generated_at','receipt','source_mode','status',
        'provider','captured_at','valid_until','provider_snapshot_sha256','models','blockers','coverage') if k in forecast}
    value['races']=[]
    for race in forecast.get('races',[]):
        row={k:v for k,v in race.items() if k in ('meeting','race','country','captured_at','scheduled_start','scratchings',
            'market_integrity','single_race_assessment','independent_verification','scratching_status','data_completeness','shared_model_input_sha256')}
        row['models']={version:{k:v for k,v in model.items() if k in allowed} for version,model in race['models'].items()}
        value['races'].append(row)
    def scrub(value):
        if isinstance(value,dict):return {k:scrub(v) for k,v in value.items() if k not in ('score_trace','original_features','transformed_features','feature_values','raw_provider_response')}
        if isinstance(value,list):return [scrub(v) for v in value]
        return value
    return scrub(value)

def bundle(forecast,now=None):
    from monty_operations import projection,ticket,utcnow
    from operations.render import render
    from operations.combined import combined_ticket
    now=now or utcnow()
    if forecast.get('source_mode')!='LIVE' or forecast.get('provider')!='PuntersEdge':
        raise PrivateDeliveryError('personal_puntersedge_delivery_scope_required')
    run=str(forecast['run_id']);day=forecast['date']
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',run) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):
        raise PrivateDeliveryError('invalid_private_run_identity')
    data=derived_forecast(forecast);files={'forecast.json':encoded(data)}
    for version,mode in [('V6','official'),('V6','provisional'),('V7','shadow'),('V7','provisional')]:
        view=projection(data,dict(version=version,view=mode),now)
        base=version.lower()+'-'+mode
        files[base+'.txt']=ticket(view,now=now).encode();files[base+'.html']=render(view,now=now).encode()
    combined=combined_ticket(data,now)
    text='MONTY — COMBINED PROVISIONAL ASSESSMENTS\nNOT A QUALIFIED DAILY BETTING TICKET\n'+ticket(combined,now=now)
    files['combined-assessments.txt']=text.encode()
    decisions=sorted({r['models']['V6'].get('betting_decision','DATA BLOCKED') for r in data['races']})
    files['combined-qualified.txt']=('MONTY — COMBINED DAILY TICKET\nNo qualified wagers published. Betting status: '+', '.join(decisions)+'\nSee separate provisional/research assessments and missing-evidence reasons.\nIN MONTY WE TRUST.\n').encode()
    receipt=dict(schema='monty.private-delivery-receipt.v1',run_id=run,date=day,provider='PuntersEdge',
        captured_at=data.get('captured_at'),valid_until=data.get('valid_until'),status=data['status'],
        forecast_sha256=sha(files['forecast.json']),provider_snapshot_sha256=data.get('provider_snapshot_sha256'),models=data['models'],
        permission_reference=PERMISSION,reviewed_terms_sha256=TERMS_SHA,personal_owner_only=True,raw_provider_responses_retained=False,feature_matrices_retained=False,contains_attributed_prices=True,
        files={name:sha(raw) for name,raw in files.items()})
    files['receipt.json']=encoded(receipt)
    if sum(map(len,files.values()))>10_000_000:raise PrivateDeliveryError('private_derived_bundle_bound')
    prefix='runs/'+day+'/'+run+'/'
    from monty_operations import timestamp,MAX_AGE_SECONDS
    from datetime import timedelta
    validity=[dict(meeting=r['meeting'],race=str(r['race']),country=r['country'],captured_at=r['captured_at'],valid_until=min(timestamp(r['captured_at'])+timedelta(seconds=MAX_AGE_SECONDS),timestamp(r['scheduled_start'])).isoformat()) for r in data['races'] if any(m.get('status')=='SCORED' for m in r['models'].values())]
    index=dict(race_validity=validity,schema='monty.private-result-index.v1',repository=REPO,ref=BRANCH,run_id=run,date=day,
        status=data['status'],provider='PuntersEdge',captured_at=data.get('captured_at'),valid_until=data.get('valid_until'),
        forecast_path=prefix+'forecast.json',forecast_sha256=receipt['forecast_sha256'],
        receipt_path=prefix+'receipt.json',receipt_sha256=sha(files['receipt.json']),
        tickets={name:prefix+name for name in files if name.endswith('.txt')})
    return {prefix+name:raw for name,raw in files.items()},index

def publish(forecast,*,sink=None,now=None):
    from operations.evidence.store import no_secrets
    no_secrets(forecast)
    files,index=bundle(forecast,now);sink=sink or Sink()
    old=sink.read(index['receipt_path'])
    if old is not None:
        try:saved=json.loads(old)
        except ValueError:raise PrivateDeliveryError('private_forecast_conflict') from None
        if saved.get('forecast_sha256')!=index['forecast_sha256']:raise PrivateDeliveryError('private_forecast_conflict')
        index['receipt_sha256']=sha(old)  # Preserve the original timestamped previews.
        return index
    # Private derived records remain immutable; only the latest pointer advances.
    files['daily/'+forecast['date']+'/latest.json']=encoded(index)
    sink.commit(files)
    return index
