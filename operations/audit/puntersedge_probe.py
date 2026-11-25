"""Bounded authenticated AU comparison: aggregate evidence only, no raw exports."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
from pathlib import Path
import json,os,sys,time,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from puntersedge_adapter import Client,ProviderError,safe_usage
from operations.data_acquisition import usage_summary
from operations.audit.provider_entitlement_probe import request
from operations.public_sources import capture,sportsbet
from operations.market_integrity import timestamp


def now():return datetime.now(timezone.utc)
def rows(value):return value if isinstance(value,list) else []
def norm(value):return ' '.join(str(value).casefold().split())


def observe(race,collector):
    result={};quote_keys=set();rkeys=set()
    for runner in race.get('runners',[]):
        if collector=='Krok' and runner.get('is_scratched') is not False:continue
        rkeys.update(runner);number=str(runner.get('number'));name=norm(runner.get('name'))
        if not number.isdigit() or not name:continue
        for q in runner.get('bookmakers' if collector=='PuntersEdge' else 'odds',[]):
            quote_keys.update(q)
            book=str(q.get('key' if collector=='PuntersEdge' else 'bookmaker','')).casefold()
            book={'pointsbetau':'pointsbet','sportsbet':'sportsbet','tab':'tab','tabtouch':'tabtouch','ladbrokes_au':'ladbrokes','ladbrokes':'ladbrokes'}.get(book,book)
            price=q.get('win_price' if collector=='PuntersEdge' else 'win')
            if type(price) not in (int,float) or not 1<price<float('inf'):continue
            clocks={k:q[k] for k in ('last_update','last_seen_at','observed_at','captured_at','updated_at','age_seconds','stale') if k in q}
            if collector=='PuntersEdge' and q.get('age_basis')=='poll':clocks['observation_at']=q.get('last_update')
            elif collector=='Krok':clocks['observation_at']=q.get('captured_at') or q.get('observed_at')
            key=(number,name,book)
            if key in result:raise ValueError('Ambiguous same-runner/book quotes')
            result[key]=dict(price=price,clocks=clocks,source_url=q.get('source_url') or q.get('bet_link'))
    return result,sorted(rkeys),sorted(quote_keys)


def summarize(values,at):
    clocks={};perbook={}
    for (_,_,book),value in values.items():
        perbook[book]=perbook.get(book,0)+1
        for k,v in value['clocks'].items():
            if k=='stale':continue
            try:age=float(v) if k=='age_seconds' else (at-timestamp(v)).total_seconds()
            except (TypeError,ValueError,AttributeError):continue
            clocks.setdefault(k,[]).append(age)
    return dict(offers=len(values),bookmakers=perbook,clocks={k:dict(count=len(v),min_age_seconds=min(v),max_age_seconds=max(v),
        under_300_seconds=sum(0<=a<300 for a in v)) for k,v in clocks.items()})


def result_inventory(value):
    return dict(sample_races=len(value) if isinstance(value,list) else None,
        statuses=dict(__import__('collections').Counter(r.get('status','UNKNOWN') for r in rows(value))),
        full_runner_rows=sum(len(rows(r.get('runners'))) for r in rows(value)),
        unavailable_runner_lists=sum(not isinstance(r.get('runners'),list) for r in rows(value)),
        independent_official_settlement=False)


def compare(a,b,at):
    common=set(a)&set(b)
    def observed(value):
        try:return timestamp(value['clocks'].get('observation_at') or value['clocks'].get('captured_at'))
        except (TypeError,ValueError,AttributeError):return None
    return dict(exact_runner_name_number_book_matches=len(common),same_price=sum(a[k]['price']==b[k]['price'] for k in common),
        first_only=len(set(a)-set(b)),second_only=len(set(b)-set(a)),
        exact_observation_time_matches=sum(observed(a[k]) is not None and observed(a[k])==observed(b[k]) for k in common),
        first=summarize({k:a[k] for k in common},at),second=summarize({k:b[k] for k in common},at),
        independence_established=False,limitation='Same-request window is not identical upstream observation time; matching prices never prove collector independence')


def main():
    if (os.getenv('GITHUB_HEAD_REF') or os.getenv('GITHUB_REF_NAME'))!='integration/puntersedge-staging':raise ValueError('Staging branch required')
    out=dict(started_at=now().isoformat(),commit=os.getenv('GITHUB_SHA'),
        workflow_url=f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        credential_configured=bool(os.getenv('PUNTERSEDGE_API_KEY')),model_inference=False,production_changed=False)
    root=Path('operations_output/puntersedge-probe');public=root/'public';public.mkdir(parents=True,exist_ok=True)
    client=None
    try:
        client=Client(budget=40);before=client.get('/v1/usage');out['usage_before']=safe_usage(before)
        out['authentication_verified']=True
        # Entire priced AU board, plus unresolved-country records kept explicit.
        params=dict(num_races=200,categories='horse',country='AU',include_unresolved='true')
        pe=client.get('/v1/racing/next-to-go',params)
        if not isinstance(pe,list):raise ValueError('Unexpected next-to-go shape')
        out['board']=dict(races=len(pe),confirmed_au=sum(r.get('country')=='AU' for r in pe),
            country_unresolved=sum(r.get('country') is None for r in pe),venues=sorted({r.get('venue','') for r in pe}))
        day=now().astimezone(__import__('zoneinfo').ZoneInfo('Australia/Brisbane')).date().isoformat()
        events=client.get('/v1/racing/events',dict(hours_ahead=24,categories='horse',country='AU',include_unresolved='true'))
        out['events']=dict(count=len(events) if isinstance(events,list) else None)
        confirmed=[r for r in pe if r.get('country')=='AU' and r.get('category')=='horse' and timestamp(r['start_time'])>now()]
        preferred=[r for r in confirmed if norm(r.get('venue'))=='launceston' and r.get('race_number')==6]
        target=(preferred or sorted(confirmed,key=lambda r:r['start_time']))[0] if confirmed else None
        # Do not guess AU from an unresolved country or horse-reference name.
        if target:
            race_id=target['race_id'];venue=target['venue'];number=target['race_number']
            out['target']={k:target.get(k) for k in ('race_id','venue','race_number','category','country','start_time','distance_m','track_condition')}
            accept=client.get('/v1/racing/acceptances',dict(date=day,venue=venue))
            out['acceptances']={k:accept.get(k) for k in ('date','meeting_count','race_count','runner_count','scratched_count','emergency_count','as_of','completeness')}
            form=client.get('/v1/racing/form',dict(race_id=race_id,runs=10))
            out['form']={k:form.get(k) for k in ('card_source','form_as_at','runners_total','runners_with_runs','runs_per_runner','source')}
            out['form']['runner_keys']=sorted({k for r in form.get('runners',[]) for k in r})
            out['form']['past_runs']=sum(len(r.get('runs',[])) for r in form.get('runners',[]))
            markets=client.get('/v1/racing/markets',dict(race_id=race_id,markets='win')) if before.get('plan')!='free' else {}
            out['market_view_entitlement']='Free test previously returned 200 despite published Plus restriction; not relied on or re-requested'
            out['market_book_summary']=[dict(key=b.get('key'),runners=b.get('runners_quoted'),book_percentage=b.get('overround_pct'),
                reported_book_time=b.get('observed_at'),time_semantics='schema: newest price change, not all-runner observation time')
                for m in markets.get('markets',[]) if m.get('market')=='win' for b in m.get('bookmakers',[])]
            out['epochs']=[]
            prior=None
            for epoch in range(2):
                if epoch:
                    time.sleep(35)
                    time.sleep(35)  # Cross documented 65s Free cache; no >60s wait.
                start=now()
                with ThreadPoolExecutor(max_workers=2) as pool:
                    p=pool.submit(client.get,'/v1/racing/next-to-go',dict(params,venue=venue,num_races=20),command='PAIRED_SINGLE_RACE')
                    k=pool.submit(request,'https://krokodds.com.au','/api/v1/racing/meetings',os.getenv('KROK_API_KEY',''),dict(date=day,country='AU',race_type='T',venue=venue,limit=50))
                    newer=p.result();ks,krok=k.result()
                matches=[r for r in newer if r.get('race_id')==race_id]
                km=[r for m in (krok or {}).get('data',[]) if norm(m.get('venue'))==norm(venue) and m.get('country')=='AU' and m.get('type')=='T' and str(m.get('date',''))[:10]==day
                    for r in m.get('races',[]) if r.get('number')==number and timestamp(r.get('jump_time'))==timestamp(target['start_time'])]
                at=now();entry=dict(request_window_start=start.isoformat(),request_window_end=at.isoformat(),krok_status=ks)
                if len(matches)==len(km)==1:
                    a,rkeys,qkeys=observe(matches[0],'PuntersEdge');b,_,_=observe(km[0],'Krok')
                    entry.update(comparison=compare(a,b,at),pe_runner_keys=rkeys,pe_quote_keys=qkeys,
                        pe_scratchings=len(matches[0].get('scratchings',[])),krok_scratchings=sum(x.get('is_scratched') is True for x in km[0].get('runners',[])))
                    entry['age_basis_counts']=dict(__import__('collections').Counter(q.get('age_basis','UNKNOWN') for r in matches[0]['runners'] for q in r.get('bookmakers',[])))
                    declarations=[r for m in accept.get('meetings',[]) for r in m.get('races',[]) if r.get('race_number')==number]
                    if len(declarations)==1:
                        expected={str(r['number']):(norm(r['runner_name']),r.get('scratched')) for r in declarations[0]['runners']}
                        actual={str(r['number']):(norm(r['name']),False) for r in matches[0]['runners']}
                        actual.update({str(r['number']):(norm(r['name']),True) for r in matches[0].get('scratchings',[])})
                        entry['acceptance_reconciliation']=dict(exact_declared_field_and_scratchings=expected==actual,
                            acceptance_runners=len(expected),live_declared_runners=len(actual),
                            missing_from_live=len(set(expected)-set(actual)),emergencies=sum(r.get('emergency') is True for r in declarations[0]['runners']),
                            independently_verified=False)
                    # Market integrity is computed from the exact single-book
                    # adapter, never the displayed aggregate overround alone.
                    from puntersedge_adapter import canonical_race
                    from operations.market_integrity import analyze,quote_evidence
                    entry['single_book_checks']={}
                    for book in ('tab','sportsbet'):
                        try:
                            canonical=canonical_race(matches[0],day=day,book=book)
                            active=[r for r in canonical['data'][0]['races'][0]['runners'] if not r['is_scratched']]
                            quotes=[quote_evidence(r) for r in active]
                            for r in quotes:r['odds']=r.get('odds')
                            entry['single_book_checks'][book]=analyze(quotes,expected_active=len(active),captured_at=at.isoformat(),now=at,
                                context=dict(active_identities=[[r['number'],r['horse']] for r in quotes]))
                            # Do not export real prices/baseline runner rows.
                            entry['single_book_checks'][book].pop('market_only_baseline',None)
                        except Exception as exc:entry['single_book_checks'][book]={'blocker':str(exc) if isinstance(exc,ProviderError) else type(exc).__name__}
                    if not epoch and os.getenv('PE_RUN_FROZEN')=='1':
                        try:
                            import monty_operations as ops
                            canonical=canonical_race(matches[0],day=day,book='tab')
                            forecast=ops.execute(day,root/'private-inference',Path('v7_engine'),run_id=os.environ['GITHUB_RUN_ID']+'-PE',
                                payload=canonical,captured=at,request=ops.command(f'RM6 {venue} {number}',day,'AU'))
                            out['model_inference']=True
                            out['staged_engine_test']=dict(status=forecast['status'],models=forecast['models'],
                                forecast_sha256=ops.sha(root/'private-inference/public/forecast.json'),receipt_sha256=ops.sha(root/'private-inference/public/receipt.json'),
                                outcomes=[dict(model=v,status=z['status'],classification=z.get('prediction_classification'),betting=z.get('betting_decision')) for r in forecast['races'] for v,z in r['models'].items()])
                        except Exception as exc:out['staged_engine_test']={'blocker':type(exc).__name__}
                    if prior:entry['pe_since_prior']=compare(prior,a,at)
                    if prior:
                        common=set(prior)&set(a)
                        entry['changed_poll_time_unchanged_price']=sum(prior[k]['price']==a[k]['price'] and
                            prior[k]['clocks'].get('last_update')!=a[k]['clocks'].get('last_update') for k in common)
                    differences=[]
                    for value in a.values():
                        q=value['clocks']
                        try:differences.append(abs((at-timestamp(q['last_update'])).total_seconds()-q['age_seconds']))
                        except (TypeError,KeyError,ValueError,AttributeError):pass
                    entry['age_clock_max_difference_seconds']=max(differences) if differences else None
                    prior=a
                    if not epoch:
                        # TAB first; follow only public race pages returned by API,
                        # never betslip links. No challenge/redirect/TLS bypass.
                        links=list(dict.fromkeys(v['source_url'] for key,v in a.items() if key[2] in ('tab','sportsbet') and v.get('source_url')))
                        direct=[]
                        from urllib.parse import urlsplit
                        for url in sorted(links,key=lambda u:0 if 'www.tab.com.au/' in u else 1)[:2]:
                            if urlsplit(url).query or urlsplit(url).fragment:continue
                            meta,body=capture(url,root/'private-direct');meta['race_parse_verified']=False
                            if body and url.startswith('https://www.sportsbet.com.au/'):
                                try:
                                    direct_race=sportsbet(body,url,day,venue,number)
                                    vector={(r['number'],norm(r['horse']),'sportsbet'):dict(price=float(r['fixed_win']),clocks={}) for r in direct_race['runners'] if not r['scratched']}
                                    meta.update(race_parse_verified=True,pe_comparison=compare(a,vector,now()),krok_comparison=compare(b,vector,now()))
                                except Exception as exc:meta['parse_blocker']=type(exc).__name__
                            direct.append(meta)
                        out['direct_bookmaker_evidence']=direct
                else:entry['blocker']='Exact same-race pair unavailable; no inferred race match'
                out['epochs'].append(entry)
            conditions=client.get('/v1/racing/track-conditions',dict(date=day,venue=venue))
            out['track_conditions']=dict(meetings=len(conditions.get('meetings',[])),keys=sorted(conditions))
            delta=client.get('/v1/racing/changes',dict(since=(now()-timedelta(minutes=2)).isoformat(),categories='horse',country='AU',include_unresolved='true'))
            out['changes']=dict(server_time=delta.get('server_time'),races=len(delta.get('races',[])))
        results=client.get('/v1/racing/results',dict(date=day,categories='horse',country='AU',limit=50))
        out['results']=result_inventory(results)
        after=client.get('/v1/usage');out['usage_after']=safe_usage(after)
        out['usage_period_delta']=after.get('credits_used',0)-before.get('credits_used',0)
    except Exception as exc:
        # Only our fixed messages, never raw response bodies, requests or keys.
        out['blocker']=str(exc) if isinstance(exc,ProviderError) else type(exc).__name__
    if client:out.update(request_usage=client.usage,response_evidence=client.responses,usage_summary=usage_summary(client.usage))
    out['finished_at']=now().isoformat();(public/'puntersedge-probe.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out.get(k) for k in ('workflow_url','authentication_verified','usage_summary','blocker')}))
    if out.get('blocker'):raise SystemExit(1)


if __name__=='__main__':main()
