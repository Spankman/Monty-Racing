"""Isolated integration pilot on existing Actions; never production publication."""
import copy,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import monty_operations as ops
from operations.public_sources import capture,sportsbet,rq_facts,rq_declaration
from operations.prospective import freeze


def comparable_name(horse):
    import re
    return ' '.join(re.sub(r'\s*\((?:AUS|NZ|GB|IRE|FR|USA)\)\s*$','',horse,flags=re.I).casefold().split())


def operator_matches(payload,operator,day):
    matches=[(m,r) for m in payload['data'] if m.get('country')=='AU' and str(m.get('date',''))[:10]==day and m.get('venue','').casefold()==operator['meeting'].casefold() for r in m.get('races',[]) if str(r.get('number'))==operator['race']]
    if len(matches)!=1:return False,'provider_race_absent_or_ambiguous',None
    meeting,race=matches[0]
    if race.get('jump_time') is None or ops.timestamp(race['jump_time'])!=ops.timestamp(operator['scheduled_start']) or race.get('distance_m',race.get('distance'))!=operator['distance_m']:
        return False,'provider_operator_distance_or_jump_mismatch',race
    source=[(str(r.get('number')),comparable_name(r.get('name','')),r.get('is_scratched')) for r in race.get('runners',[])]
    direct=[(r['number'],comparable_name(r['horse']),r['scratched']) for r in operator['runners']]
    if any(type(x[2]) is not bool for x in source) or len(source)!=len(set(x[0] for x in source)) or sorted(source)!=sorted(direct):
        return False,'provider_operator_declared_field_or_scratching_mismatch',race
    return True,None,race


def main():
    if os.getenv('GITHUB_REF_NAME')!='integration/verified-operations':raise ValueError('Integration pilot restricted to unmerged branch')
    os.environ['OPERATIONS_RESULTS_BRANCH']='monty-verification-staging-results'
    os.environ['OPERATIONS_ISSUE_COMMENTS']='1'
    from operations import transport,issue_delivery,client
    issue=int(json.loads(Path('.monty/operations-staging.json').read_text())['issue_id']);tag=os.environ['GITHUB_RUN_ID'];workflow=f'https://github.com/{transport.REPO}/actions/runs/{tag}'
    opened=transport.api(f'issues/{issue}')
    if opened['user']['login']!='Spankman' or opened['title']!='Monty verification staging — integrated command and source pilot':raise ValueError('Wrong staging issue')
    started=ops.utcnow();day=started.astimezone(ops.TZ).date().isoformat()
    base=Path('operations_output');private=base/(tag+'-source-private')
    summary=dict(schema='monty.integration.pilot.v1',date=day,commit=os.environ['GITHUB_SHA'],trigger='isolated branch push; not ordinary issue-event acceptance',
        issue_id=issue,issue_created_at=opened['created_at'],started_at=started.isoformat(),workflow_url=workflow,
        production_ready=False,models_frozen=True,expert_weights={'Monty':1.0,'experts':0.0},sources=[],commands=[],timings={})
    issue_delivery.report(issue,'ack',f'**Monty STAGING RUNNING** · [Workflow]({workflow}). No production deployment or wagering.')
    summary['acknowledged_at']=ops.utcnow().isoformat()
    stage=time.monotonic()
    urls=[('tab','https://www.tab.com.au/racing/'+day),
          ('authority_ipswich','https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/ipsw/'+day.replace('-','')+'/race/4'),
          ('authority_wyong','https://racing.racingnsw.com.au/FreeFields/Acceptances.aspx?Key='+day[:4]+'Nov'+day[-2:]+',NSW,Wyong')]
    authority=None;authority_body=None;authority_meta=None
    for key,url in urls:
        meta,body=capture(url,private);summary['sources'].append(dict(meta,role=key))
        if key=='authority_ipswich' and body:
            try:
                authority=rq_facts(body,day,'Ipswich',4);summary['authority_metadata']=authority
                authority_body=body;authority_meta=meta
                from bs4 import BeautifulSoup
                from urllib.parse import urljoin
                links=[a.get('href') for a in BeautifulSoup(body,'html.parser').find_all('a',href=True) if 'Race Fields PDF' in a.get_text(' ',strip=True)]
                if len(links)==1:
                    pdf_meta,pdf=capture(urljoin(url,links[0]),private);summary['sources'].append(dict(pdf_meta,role='authority_field_pdf'))
                    if pdf and pdf.startswith(b'%PDF'):
                        authority=rq_declaration(body,pdf,day,'Ipswich',4);summary['authority_metadata']=authority
            except Exception as exc:summary['authority_parse_error']=type(exc).__name__
    # Second Australian pilot: record the actual NSW source outcome, not a cached
    # search snippet. No attempt to defeat a challenge or repeat a denied request.
    summary['independent_verification_seconds']=round(time.monotonic()-stage,6)
    operator_url='https://www.sportsbet.com.au/horse-racing/australia-nz/ipswich/race-4-11204566'
    packet_path=Path('.monty/verification-operator-packet.json')
    operator=None
    if packet_path.exists():
        packet=json.loads(packet_path.read_text());op_meta=packet['capture'];operator=packet['operator']
        summary['operator_acquisition_mode']='one-off permitted workspace public-page capture; Actions direct access was denied; not unattended production acceptance'
        import hashlib
        if packet.get('operator_sha256')!=hashlib.sha256(json.dumps(operator,sort_keys=True,separators=(',',':')).encode()).hexdigest() or op_meta.get('source_url')!=operator_url or op_meta.get('http_status')!=200:raise ValueError('Operator packet provenance mismatch')
        age=(ops.utcnow()-ops.timestamp(op_meta['observed_at'])).total_seconds()
        if not (0<=age<ops.MAX_AGE_SECONDS) or op_meta.get('status')!='CAPTURED' or operator['date']!=day:
            operator=None;summary['operator_parse_error']='OperatorPacketExpiredOrUnverified'
    else:
        op_meta,body=capture(operator_url,private)
        if body:
            try:operator=sportsbet(body,operator_url,day,'Ipswich',4)
            except Exception as exc:summary['operator_parse_error']=type(exc).__name__
    summary['sources'].append(dict(op_meta,role='operator_ipswich'))
    from krok_adapter import fetch
    stage=time.monotonic();payload=fetch(day,os.environ.get('KROK_API_KEY',''));provider_at=ops.utcnow()
    summary['timings']['provider_acquisition_seconds']=round(time.monotonic()-stage,6)
    summary['raw_provider_snapshot_sha256']=ops.sha_bytes(payload) if hasattr(ops,'sha_bytes') else __import__('hashlib').sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    summary['provider_captured_at']=provider_at.isoformat()
    effective=copy.deepcopy(payload);captured=provider_at
    if operator:
        match,reason,race=operator_matches(effective,operator,day)
        summary['operator_field_matches_provider']=match
        summary['operator_match_blocker']=reason
        summary['operator_observation']=operator
        if match:
            rows={r['number']:r for r in operator['runners']}
            for runner in race['runners']:
                direct=rows[str(runner['number'])]
                if not direct['scratched']:
                    quote=float(direct['fixed_win']);runner.update(odds=[{'bookmaker':'Sportsbet','win':quote}],fixed_win=quote,best_win=quote,fixed_win_bookmaker='Sportsbet',best_win_bookmaker='Sportsbet')
            captured=min(provider_at,ops.timestamp(op_meta['observed_at']))
            summary['price_input_policy']='Explicit direct Sportsbet WIN overlay on matched Ipswich R4 only; Krok field features unchanged'
    verification=dict(race_verified=False,fixed_win_verified=bool(summary.get('operator_field_matches_provider')),emergency_status_verified=False,
        sources=[dict(s,date=day,meeting='Ipswich',race='4') for s in summary['sources'] if s['role'] in ('authority_ipswich','authority_field_pdf','operator_ipswich')],blockers=['independent_authority_complete_field_and_final_emergencies_not_verified'])
    if authority and authority.get('field_verified') and operator and summary.get('operator_field_matches_provider'):
        direct={(r['number'],comparable_name(r['horse']),r['scratched']) for r in operator['runners']}
        official={(r['number'],comparable_name(r['horse']),r['scratched']) for r in authority['runners']}
        facts_match=all(authority.get(k)==operator.get(k) for k in ('distance_m','condition','scheduled_start'))
        verification['race_verified']=direct==official and facts_match and authority.get('surface')=='turf'
        verification['emergency_status_verified']=authority.get('emergency_status_verified',False)
        if verification['race_verified'] and verification['emergency_status_verified']:verification['blockers']=[]
    summary['pilot_verification']=verification
    if verification['race_verified']:
        race['track_condition']=authority['condition']
        summary['authority_input_overlay']='Verified primary authority track condition; original frozen going normalization unchanged'

    commands=['RM6','RM7','RM6PS','RM7PS','RM6 Ipswich 4','RM7 Ipswich 4','RM6PS Ipswich 4','RM7PS Ipswich 4','Ipswich 4']
    first=None
    for i,text in enumerate(commands,1):
        req=ops.command(text,day,'AU');run_id=f'{tag}-integration-{i}';out=base/run_id;stage=time.monotonic()
        forecast=ops.execute(day,out,'v7_engine',run_id=run_id,payload=effective,captured=captured,request=req,timings=True)
        public=out/'public';receipt=json.loads((public/'receipt.json').read_text())
        view=ops.projection(forecast,req)
        # Render only public derived views; raw provider/HTML responses are never uploaded.
        for file in public.glob('v[67]-*.json'):
            file.with_suffix('.txt').write_text(ops.ticket(json.loads(file.read_text()),archived=True))
        from operations.render import render_all
        render_all(public)
        summary['commands'].append(dict(command=text,run_id=run_id,status=forecast['status'],models=forecast['models'],
             elapsed_seconds=round(time.monotonic()-stage,6),capture_age_seconds=(ops.utcnow()-captured).total_seconds(),
             forecast_sha256=receipt['forecast_sha256'],receipt_sha256=ops.sha(public/'receipt.json')))
        if i==1:first=(req,forecast,public)
        if text=='RM6 Ipswich 4' and forecast.get('races'):
            target=forecast['races'][0]
            if all(m['status']=='SCORED' for m in target['models'].values()):
                try:
                    frozen=freeze(forecast,target,verification,base/(tag+'-prospective')/'public'/'record.json')
                    summary['prospective_cohort_admitted']=frozen['cohort_admitted']
                except Exception as exc:summary['prospective_freeze_blocker']=type(exc).__name__
    req,forecast,public=first
    stage=time.monotonic();index=transport.publish(public,forecast['run_id'],day,issue,workflow,request=req)
    summary['timings']['result_publication_seconds']=round(time.monotonic()-stage,6)
    original=transport.api;methods=[]
    def read_only(endpoint,method='GET',body=None,optional=False):
        methods.append(method)
        if method!='GET':raise AssertionError('C attempted a mutation')
        return original(endpoint,method,body,optional)
    transport.api=read_only
    try:
        stage=time.monotonic();status=client.handle('C',request_id=issue)
        summary['read_only_C']=dict(http_methods=methods,request_status=status['request_status'],semantic_outcome=status['semantic_outcome'],freshness=status.get('freshness'),capture_age_seconds=status.get('capture_age_seconds'),receipt_path=status.get('receipt_path'),elapsed_seconds=time.monotonic()-stage)
        if status.get('semantic_outcome') not in ('COMPLETED_ASSESSMENTS','PARTIAL_ASSESSMENTS') or status.get('freshness')!='FRESH' or 'ticket' not in status:raise ValueError('Read-only C did not retrieve a fresh verified forecast')
    finally:transport.api=original
    body=issue_delivery.result_body(req,forecast,json.loads((public/'receipt.json').read_text()),index)
    stage=time.monotonic();issue_delivery.report(issue,'terminal','**ISOLATED STAGING — NOT PRODUCTION ACTIVATION**\n\n'+body)
    summary['timings']['terminal_delivery_seconds']=round(time.monotonic()-stage,6)
    summary['terminal_delivered_at']=ops.utcnow().isoformat()
    summary['finished_at']=ops.utcnow().isoformat();summary['forecast_index']=index
    ops.write(base/(tag+'-summary')/'public'/'verification-acceptance.json',summary)
    print(json.dumps(summary,allow_nan=False))
    if any(c['status'] not in ('COMPLETED_ASSESSMENTS','PARTIAL_ASSESSMENTS') or not c['models'][ops.command(c['command'],day,'AU')['version']]['scored_races'] for c in summary['commands']):raise ValueError('Some requested models did not complete; inspect actual outcomes')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'EXECUTION FAILED','error_type':type(exc).__name__}))
        if os.environ.get('GITHUB_REF_NAME')=='integration/verified-operations':
            from operations import issue_delivery
            issue_id=int(json.loads(Path('.monty/operations-staging.json').read_text()).get('issue_id',214))
            issue_delivery.report(issue_id,'terminal','**STAGING EXECUTION FAILED** · '+type(exc).__name__+' · No production change or qualified bet is claimed.')
        raise SystemExit(1)
