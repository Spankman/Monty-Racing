"""Finite, budgeted hosted trial. Output is aggregates + encrypted private evidence.

Each capture is a separate workflow step followed immediately by artifact upload.
No production integration, auto-migration, retraining, approval or settlement
attestation is performed here. Existing prospective gates remain authoritative.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import argparse,hashlib,json,os,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from operations.trial.program import protocol,preregister,validate_plan,windows,stamp,digest,seal,TZ
from puntersedge_adapter import Client,ProviderError,safe_usage,canonical_race
from operations.audit.puntersedge_probe import observe,compare,summarize,norm,result_inventory
from operations.audit.provider_entitlement_probe import request as krok_request
from operations.public_sources import capture,rq_declaration,sportsbet
from operations.data_acquisition import usage_summary

ROOT=Path('operations_output/pe-trial')
def now():return datetime.now(timezone.utc)
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as file:json.dump(value,file,indent=2,allow_nan=False);file.write('\n')
def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def safe_error(exc):return str(exc) if isinstance(exc,ProviderError) else type(exc).__name__
def guard():
    if os.getenv('GITHUB_REPOSITORY')!='Spankman/Monty-Racing':raise ValueError('Owner repository required')
    if os.getenv('GITHUB_REF_NAME')!='trial/puntersedge-acceptance-20261126':raise ValueError('Trial staging branch required')
    if os.getenv('GITHUB_EVENT_NAME')!='push':raise ValueError('Only staged marker pushes permitted')
def reserve(client,phase):
    account=client.get('/v1/usage',command='PE_TRIAL_'+phase.upper())
    remaining=account.get('credits_remaining')
    if type(remaining) is not int or remaining<protocol()['puntersedge_operational_reserve']+client.budget:
        raise ProviderError('Unverified/insufficient PE allowance; operational reserve preserved')
    return safe_usage(account)
def lineage(day,phase):
    return dict(schema='monty.pe-trial.v1',trial_id=protocol()['trial_id'],date=day,phase=phase,
        commit=os.getenv('GITHUB_SHA'),started_at=now().isoformat(),
        workflow_url=f"https://github.com/Spankman/Monty-Racing/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        betting_authorised=False,production_changed=False)
def finish(public,private,entry,client):
    if client:
        try:entry['usage_after']=safe_usage(client.get('/v1/usage',command='PE_TRIAL_USAGE'))
        except Exception as exc:entry['usage_after_error']=safe_error(exc)
        entry.update(request_usage=client.usage,response_evidence=client.responses,usage=usage_summary(client.usage),
                     reserved_credits=client.reserved)
        a=entry.get('usage_before',{}).get('credits_used');b=entry.get('usage_after',{}).get('credits_used')
        entry['account_counter_delta']=b-a if type(a) is type(b) is int and b>=a else None
        entry['account_delta_attribution']='Account-wide; concurrent production calls may contribute; endpoint headers separately recorded'
    entry['finished_at']=now().isoformat()
    if private.exists():entry['encrypted_evidence_sha256']=seal(private,public/'private-evidence.cms')
    save(public/'receipt.json',entry)
    (public/'receipt.sha256').write_text(sha(public/'receipt.json')+'  receipt.json\n')
    print(json.dumps({k:entry.get(k) for k in ('phase','status','workflow_url','blocker','reserved_credits')}))

def market_summaries(values,expected,at,collector):
    from operations.market_integrity import analyze
    result={}
    for book in sorted({k[2] for k in values}):
        rows=[dict(number=n,horse=name,odds=v['price'],bookmaker=book,
            quote_timestamps=[v['clocks']['observation_at']] if v['clocks'].get('observation_at') else [],
            quote_time_basis=collector+'_PROVIDER_OBSERVATION_NOT_BOOKMAKER_UPDATE')
            for (n,name,b),v in values.items() if b==book]
        audit=analyze(rows,expected_active=len(expected),captured_at=at.isoformat(),now=at,
                      context=dict(active_identities=expected))
        audit.pop('market_only_baseline',None)  # Runner prices/distribution private.
        result[book]=audit
    return result

def history_inventory(form,received):
    rows=[r for horse in form.get('runners',[]) for r in horse.get('runs',[])]
    valid=[];rejected=0
    for row in rows:
        try:
            # Exclude same-day outcomes even when an exact race clock is present.
            date=str(row['date'])[:10]
            if date>=received.astimezone(TZ).date().isoformat():raise ValueError('same-day/future')
            if row.get('start_time') and stamp(row['start_time'])>=received:raise ValueError('future clock')
            datetime.strptime(date,'%Y-%m-%d');valid.append(row)
        except (ValueError,KeyError,TypeError):rejected+=1
    try:future_asof=stamp(form['form_as_at'])>received
    except (ValueError,TypeError,KeyError):future_asof=None
    return dict(candidate_strictly_prior_day_rows=len(valid),excluded_same_day_future_or_invalid_rows=rejected,
                declared_form_as_at_after_capture=future_asof,verified_lifetime_identity=False,
                feature_activation=False,limitation='Provider form_as_at may denote scheduled race cutoff; not treated as observation time or historical availability proof')

def plan(day):
    public=ROOT/'public/plan';private=ROOT/'private/plan';public.mkdir(parents=True);private.mkdir(parents=True)
    entry=lineage(day,'plan');client=None
    try:
        client=Client(budget=protocol()['daily_plan_credit_cap']);entry['usage_before']=reserve(client,'plan')
        card=client.get('/v1/racing/next-to-go',dict(num_races=200,categories='horse',country='AU',include_unresolved='true'))
        if not isinstance(card,list):raise ProviderError('Priced card schema mismatch')
        save(private/'card.json',card)
        registered=preregister(card,day,now());save(public/'plan.json',registered)
        entry.update(status=registered['status'],plan_sha256=registered['plan_sha256'],registered_races=len(registered['races']),
                     card_races=len(card),country_unresolved=sum(r.get('country') is None for r in card))
        for venue in dict.fromkeys(r['venue'] for r in registered['races']):
            response=client.get('/v1/racing/acceptances',dict(date=day,venue=venue))
            save(private/('acceptances-'+hashlib.sha256(venue.encode()).hexdigest()[:12]+'.json'),response)
        entry['historical_form']=[]
        for i,race in enumerate(registered['races']):
            form=client.get('/v1/racing/form',dict(race_id=race['race_id'],runs=10))
            save(private/f'form-{i}.json',form)
            entry['historical_form'].append(dict(race_id=race['race_id'],source_sha256=digest(form),
                runners=form.get('runners_total'),runners_with_runs=form.get('runners_with_runs'),
                past_runs=sum(len(r.get('runs') or []) for r in form.get('runners',[])),
                temporal_inventory=history_inventory(form,now()),
                form_as_at=form.get('form_as_at'),activated_features=False,
                limitation='Candidate history only; no national identity crosswalk or original residual reconstruction attested'))
    except Exception as exc:entry.update(status='FAILED',blocker=safe_error(exc))
    finish(public,private,entry,client)
    return entry

def authority(race,folder):
    if not race.get('rq_code'):return dict(verified=False,blocker='No validated primary-authority adapter for this venue; no inferred verification',sources=[])
    from bs4 import BeautifulSoup
    url=f"https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/{race['rq_code']}/{race['date'].replace('-','')}/race/{race['race_number']}"
    meta,body=capture(url,folder);result=dict(primary_authority='Racing Queensland',verified=False,sources=[meta])
    if body:
        try:
            links=[urljoin(url,a['href']) for a in BeautifulSoup(body,'html.parser').find_all('a',href=True) if 'Race Fields PDF' in a.get_text(' ',strip=True)]
            if len(links)!=1:raise ValueError('Authority PDF link unavailable/ambiguous')
            pm,pdf=capture(links[0],folder);result['sources'].append(pm)
            if not pdf:raise ValueError('Authority PDF unavailable')
            facts=rq_declaration(body,pdf,race['date'],race['venue'],race['race_number'])
            result.update(facts=facts,verified=facts['field_verified'] and facts['emergency_status_verified'])
        except Exception as exc:result['blocker']=str(exc) if isinstance(exc,ValueError) else safe_error(exc)
    return result

def reconcile_authority(evidence,target):
    if not evidence.get('verified'):return False
    def name(s):
        import re
        return norm(re.sub(r'\s*\((?:NZ|AUS|GB|IRE|FR|USA)\)\s*$','',s,flags=re.I))
    facts=evidence['facts']
    expected={str(r['number']):(name(r['horse']),r['scratched']) for r in facts['runners']}
    actual={str(r['number']):(name(r['name']),False) for r in target['runners']}
    actual.update({str(r['number']):(name(r['name']),True) for r in target.get('scratchings',[])})
    return expected==actual and len(expected)==len(facts['runners']) and facts['distance_m']==target.get('distance_m')

def direct(target,folder,denied,minutes):
    values,_,_=observe(target,'PuntersEdge');result=[]
    links=list(dict.fromkeys(v['source_url'] for key,v in values.items() if key[2] in ('tab','sportsbet') and v.get('source_url')))
    for url in sorted(links,key=lambda s:0 if urlsplit(s).hostname=='www.tab.com.au' else 1)[:2]:
        parts=urlsplit(url)
        if parts.query or parts.fragment or parts.hostname in denied:continue
        # Do not repeat a failed public acquisition four times. 500 gets one
        # bounded later retry at T-2; 401/403/challenges stop that host all day.
        if minutes not in (60,2):continue
        meta,body=capture(url,folder);meta['race_parse_verified']=False
        if body and parts.hostname=='www.tab.com.au':
            meta['parse_blocker']='TAB public HTML is not attested to contain an executable full-field fixed-win vector; HTTP200 alone is insufficient'
        if meta.get('http_status') in (401,403) or meta.get('status')=='ACCESS_CHALLENGE':denied.add(parts.hostname)
        if body and parts.hostname=='www.sportsbet.com.au':
            try:
                facts=sportsbet(body,url,stamp(target['start_time']).astimezone(TZ).date().isoformat(),target['venue'],target['race_number'])
                meta['race_parse_verified']=True;save(folder/'parsed-sportsbet.json',facts)
            except Exception as exc:meta['parse_blocker']=safe_error(exc)
        result.append(meta)
    return result

def acceptance_inventory(value,target,at):
    candidates=[r for m in value.get('meetings',[]) if norm(m.get('venue'))==norm(target['venue'])
        for r in m.get('races',[]) if r.get('race_id')==target['race_id'] and r.get('race_number')==target['race_number']]
    if value.get('date')!=stamp(target['start_time']).astimezone(TZ).date().isoformat() or len(candidates)!=1:
        return dict(reconciled=False,blocker='Exact acceptance date/venue/race ID unavailable',independent=False)
    declared=candidates[0];rows=declared.get('runners') or []
    expected={str(r['number']):(norm(r['runner_name']),r.get('scratched')) for r in rows}
    actual={str(r['number']):(norm(r['name']),False) for r in target['runners']}
    actual.update({str(r['number']):(norm(r['name']),True) for r in target.get('scratchings',[])})
    try:age=(at-stamp(value['as_of'])).total_seconds()
    except (ValueError,TypeError,KeyError):age=None
    return dict(reconciled=bool(expected) and len(expected)==len(rows) and expected==actual,
        independent=False,acceptance_as_of=value.get('as_of'),acceptance_age_seconds=age,
        declared_runners=len(rows),live_declared_runners=len(actual),
        missing_live_declarations=len(set(expected)-set(actual)),extra_live_declarations=len(set(actual)-set(expected)),
        contradictory_identity_or_scratching_count=sum(expected[n]!=actual[n] for n in set(expected)&set(actual)),
        unresolved_emergencies=sum(r.get('emergency') is True and r.get('scratched') is not True for r in rows),
        provider_runner_set_status=declared.get('runner_set_status'),provider_missing_rows=len(declared.get('missing_runners') or []),
        limitation='Baseline declaration cache; current live quotes/SCR inspected each point; not independent final field/emergency approval')

def exact_target(card,race):
    targets=[r for r in card if r.get('race_id')==race['race_id'] and r.get('country')=='AU' and r.get('category')=='horse'
             and norm(r.get('venue'))==norm(race['venue']) and r.get('race_number')==race['race_number']
             and stamp(r['start_time'])==stamp(race['start_time'])]
    if len(targets)!=1:raise ProviderError('Registered race missing/ambiguous/rescheduled; no replacement')
    return targets[0]

def point(day,index,plan_path):
    registered=validate_plan(load(plan_path));schedule=windows(registered)
    public=ROOT/f'public/window-{index:02}';private=ROOT/f'private/window-{index:02}';public.mkdir(parents=True);private.mkdir(parents=True)
    entry=lineage(day,'capture');entry['window_index']=index;client=None
    state_path=ROOT/'private/state.json';state=load(state_path) if state_path.exists() else dict(reserved=0,krok_requests=0,denied_hosts=[])
    try:
        if registered['date']!=day:raise ValueError('Plan/control date mismatch')
        if index>=len(schedule):entry['status']='UNREGISTERED_SLOT';return entry
        scheduled,race,minutes=schedule[index]
        entry.update(race=race,plan_sha256=registered['plan_sha256'],minutes_before_jump=minutes,scheduled_capture_at=scheduled.isoformat())
        while now()<scheduled:time.sleep(min(30,max(0,(scheduled-now()).total_seconds())))
        late=(now()-scheduled).total_seconds();entry['capture_start_delay_seconds']=late
        if late>protocol()['capture_start_lateness_seconds']:entry['status']='MISSED_WINDOW';return entry
        client=Client(budget=protocol()['daily_capture_credit_cap']-state['reserved'])
        entry['usage_before']=reserve(client,'capture');entry['acquisition_started_at']=now().isoformat()
        entry['pair_request_start_delay_seconds']=(now()-scheduled).total_seconds()
        if entry['pair_request_start_delay_seconds']>protocol()['capture_start_lateness_seconds']:
            entry['status']='MISSED_WINDOW';return entry
        if state['krok_requests']>=protocol()['krok_daily_request_cap']:raise ProviderError('Krok daily request cap reached')
        def krok():
            if not os.getenv('KROK_API_KEY'):return dict(error='Krok credential unavailable',attempted=False),None
            if state['krok_requests'] and 'krok_remaining' not in state:return dict(error='Krok remaining allowance unverified; stop after single probe',attempted=False),None
            if state.get('krok_remaining',1000000)<protocol()['krok_operational_reserve']+10:return dict(error='Krok reserve stop',attempted=False),None
            begin=time.monotonic();meta,payload=krok_request('https://krokodds.com.au','/api/v1/racing/meetings',os.environ['KROK_API_KEY'],
                dict(date=day,country='AU',race_type='T',venue=race['venue'],limit=50))
            meta.update(elapsed_seconds=time.monotonic()-begin,attempted=True);return meta,payload
        with ThreadPoolExecutor(max_workers=3) as pool:
            pe_future=pool.submit(client.get,'/v1/racing/next-to-go',dict(num_races=20,categories='horse',country='AU',venue=race['venue'],include_unresolved='true'),command='PE_TRIAL_PAIR')
            k_future=pool.submit(krok);a_future=pool.submit(authority,race,private/'authority')
            card=pe_future.result();pe_received=now();km,kpayload=k_future.result();a=a_future.result()
        state['krok_requests']+=int(km.get('attempted',False))
        if km.get('x-credits-remaining') is not None:state['krok_remaining']=km['x-credits-remaining']
        entry.update(acquisition_finished_at=now().isoformat(),pe_received_at=pe_received.isoformat(),krok=km)
        target=exact_target(card,race)
        cached=state.setdefault('acceptances',{})
        if race['venue'] not in cached:
            cached[race['venue']]=client.get('/v1/racing/acceptances',dict(date=day,venue=race['venue']),command='PE_TRIAL_FIELD_BASELINE')
        save(private/'acceptance-baseline.json',cached[race['venue']])
        entry['acceptance_reconciliation']=acceptance_inventory(cached[race['venue']],target,pe_received)
        save(private/'puntersedge.json',card);save(private/'krok.json',kpayload);save(private/'authority.json',a)
        entry['authority']=dict(verified=a.get('verified',False),race_field_reconciled=reconcile_authority(a,target),
                               blocker=a.get('blocker'),sources=a['sources'])
        pv,_,_=observe(target,'PuntersEdge');entry['puntersedge_prices']=summarize(pv,pe_received)
        expected=[[str(r['number']),norm(r['name'])] for r in target['runners']]
        entry['puntersedge_markets']=market_summaries(pv,expected,pe_received,'PUNTERSEDGE')
        matches=[r for m in (kpayload or {}).get('data',[]) if norm(m.get('venue'))==norm(race['venue']) and m.get('country')=='AU' and m.get('type')=='T' and str(m.get('date',''))[:10]==day
            for r in m.get('races',[]) if r.get('number')==race['race_number'] and stamp(r['jump_time'])==stamp(race['start_time'])]
        entry['krok_pagination_complete']=(kpayload or {}).get('meta',{}).get('has_more') is False
        if len(matches)==1:
            kv,_,_=observe(matches[0],'Krok');entry['comparison']=compare(pv,kv,pe_received)
            entry['krok_markets']=market_summaries(kv,expected,pe_received,'KROK')
        else:entry['comparison_blocker']='Exact Krok same-race unavailable; no name-only/race substitution'
        denied=set(state['denied_hosts']);entry['direct_bookmakers']=direct(target,private/'direct',denied,minutes);state['denied_hosts']=sorted(denied)
        import monty_operations as ops
        payload=canonical_race(target,day=day,book=protocol()['bookmaker'])
        forecast=ops.execute(day,private/'inference',Path('v7_engine'),run_id=os.environ['GITHUB_RUN_ID']+f'-{index}',payload=payload,captured=pe_received,
            request=ops.command(f"RM6 {race['venue']} {race['race_number']}",day,'AU'),timings=True)
        entry.update(status=forecast['status'],models=forecast['models'],
            forecast_sha256=sha(private/'inference/public/forecast.json'),receipt_sha256=sha(private/'inference/public/receipt.json'),
            outcomes=[dict(model=v,status=m['status'],classification=m.get('prediction_classification'),betting=m.get('betting_decision')) for r in forecast['races'] for v,m in r['models'].items()])
        entry['prospective_records']=[]
        from operations.prospective import freeze
        for i,scored in enumerate(forecast['races']):
            try:
                # No attestation from metadata alone. The unreconstructed historical
                # crosswalk and absent operator reconciliation remain fail-closed.
                verification=dict(race_verified=entry['authority']['race_field_reconciled'],fixed_win_verified=False,
                    emergency_status_verified=a.get('facts',{}).get('emergency_status_verified',False),sources=[],
                    compatible_history={},blockers=['independent_operator_reconciliation_unverified','original_asof_history_crosswalk_unverified'])
                frozen=freeze(forecast,scored,verification,private/f'prospective-{i}.json')
                entry['prospective_records'].append(dict(record_sha256=sha(private/f'prospective-{i}.json'),
                    cohort_admitted=frozen['cohort_admitted'],blockers=frozen['admission_blockers'],
                    frozen_at=frozen['frozen_at'],shared_model_input_sha256=frozen['shared_model_input_sha256']))
            except Exception as exc:entry['prospective_records'].append(dict(blocker=safe_error(exc)))
        entry['pre_jump_finished']=now()<stamp(race['start_time'])
        entry['collector_independence_established']=False
    except Exception as exc:entry.update(status='DATA_BLOCKED' if isinstance(exc,ProviderError) else 'EXECUTION_FAILED',blocker=safe_error(exc))
    finally:
        if client:state['reserved']+=max(client.reserved,sum(x.get('x-credits-cost',0) for x in client.usage))
        state_path.parent.mkdir(parents=True,exist_ok=True);state_path.write_text(json.dumps(state))
        finish(public,private,entry,client)
    return entry

def results(day,plan_path):
    validate_plan(load(plan_path));public=ROOT/'public/results';private=ROOT/'private/results';public.mkdir(parents=True);private.mkdir(parents=True)
    entry=lineage(day,'results');client=None
    try:
        client=Client(budget=protocol()['daily_results_credit_cap']);entry['usage_before']=reserve(client,'results')
        value=client.get('/v1/racing/results',dict(date=day,categories='horse',country='AU',limit=200))
        save(private/'provider-results.json',value)
        entry.update(status='CAPTURED_NOT_INDEPENDENTLY_SETTLED',inventory=result_inventory(value),
            official_settlements=0,limitation='Provider results do not satisfy independent final official settlement or cohort admission; no performance claim')
        for race in load(plan_path)['races']:
            save(private/('authority-'+digest(race)[:12]+'.json'),authority(race,private/'authority'))
    except Exception as exc:entry.update(status='FAILED',blocker=safe_error(exc))
    finish(public,private,entry,client);return entry

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['plan','capture','results']);parser.add_argument('--index',type=int,default=0)
    args=parser.parse_args();guard();control=load('operations/trial/control.json');day=control['date']
    if day not in protocol()['dates'] or control['mode']!=args.mode:raise ValueError('Invalid finite control')
    if day!=now().astimezone(TZ).date().isoformat():raise ValueError('Hosted acquisition date must be current Brisbane date')
    plan_path=Path('operations/trial/plans')/(day+'.json')
    if args.mode=='plan':result=plan(day)
    elif args.mode=='capture':result=point(day,args.index,plan_path)
    else:result=results(day,plan_path)
    if result['status'] in ('FAILED','EXECUTION_FAILED'):raise SystemExit(1)
if __name__=='__main__':main()
