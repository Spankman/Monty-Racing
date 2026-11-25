"""Bounded real-provider staging measurement; publish counts/receipts only."""
import hashlib,json,os,sys,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import krok_adapter
import monty_operations as ops
from operations.data_acquisition import CaptureBatch,usage_summary
from operations.market_integrity import quote_evidence,timestamp
from operations.audit.provider_entitlement_probe import call_formfav,request
from operations.rq_verification import capture_races


def inventory(payload,now):
    races=[];ages=[];bad=0;selected=0;times=0;books=Counter();raw=Counter()
    for meeting in payload['data']:
        for race in meeting.get('races',[]):
            active=[r for r in race.get('runners',[]) if r.get('is_scratched') is False]
            races.append((meeting['venue'],str(race['number']),len(active)))
            for r in active:
                for q in r.get('odds',[]):
                    for field in ('captured_at','capturedAt','quoted_at','updated_at'):
                        raw[field]+=q.get(field) is not None
                selected+=1;q=quote_evidence(r);books[q['bookmaker'] or 'UNKNOWN']+=1
                if q['quote_timestamps']:
                    times+=1
                    try:ages.extend((now-timestamp(t)).total_seconds() for t in q['quote_timestamps'])
                    except (ValueError,TypeError,AttributeError):bad+=1
    return dict(meetings=len(payload['data']),races=len(races),active_runners=selected,race_keys=races,
        selected_offer_timestamp_count=times,invalid_selected_timestamp_count=bad,
        selected_age_min_seconds=min(ages) if ages else None,selected_age_max_seconds=max(ages) if ages else None,
        selected_stale_count=sum(a>=300 for a in ages),selected_future_count=sum(a<0 for a in ages),
        nested_timestamp_fields=dict(raw),selected_bookmakers=dict(books),pages=payload['meta']['pages_fetched'])


def main():
    if os.getenv('GITHUB_HEAD_REF')!='integration/data-cost-controls':raise ValueError('Staging branch required')
    root=Path('operations_output/data-cost');public=root/'public';public.mkdir(parents=True,exist_ok=True)
    now=ops.utcnow();day=now.astimezone(ops.TZ).date().isoformat();key=os.getenv('KROK_API_KEY','')
    out=dict(date=day,started_at=now.isoformat(),commit=os.getenv('GITHUB_SHA'),
        workflow_url=f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        new_live_inference=False,production_changed=False,credential_configured=bool(key))
    usage=[]
    try:
        if not key:raise ValueError('Configured Krok credential unavailable')
        payload=krok_adapter.fetch(day,key,meter=usage,command='RM6 acquisition pilot',country='AU');captured=ops.utcnow()
        out['meetings']=inventory(payload,captured)
        card=krok_adapter.fetch(day,key,meter=usage,command='DATED_CARD comparison',country='AU',dated_card=True)
        out['dated_card']=inventory(card,ops.utcnow())
        a=set(map(tuple,out['meetings']['race_keys']));b=set(map(tuple,out['dated_card']['race_keys']))
        out['comparison']=dict(same_race_keys_and_active_counts=a==b,meetings_only=len(a-b),dated_only=len(b-a),
            limitation='Sequential calls; moving prices and field changes may differ. Dated route is documented alias, not another independent source.')
        upcoming=[]
        for m in payload['data']:
            for r in m.get('races',[]):
                try:
                    if timestamp(r['jump_time'])>ops.utcnow():upcoming.append((timestamp(r['jump_time']),m,r))
                except (KeyError,TypeError,ValueError):continue
        upcoming.sort(key=lambda x:x[0])
        network=0
        def bounded(*args,**kwargs):
            nonlocal network
            if network>=2:raise ValueError('Bounded trial network budget reached; request not executed')
            network+=1
            return krok_adapter.fetch(*args,**kwargs)
        batch=CaptureBatch(bounded,key);batch.usage=usage
        # The initial acquisition is real and already metered. Sharing it does
        # not reset its timestamp or claim a second provider request.
        batch._entries[(day,'AU')]=dict(payload=payload,captured_at=captured,
            acquisition_id=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest())
        trials=[]
        commands=['RM6','RM7','RM6PS','RM7PS']
        if upcoming:
            _,m,r=upcoming[0];commands += [f"RM6 {m['venue']} {r['number']}"]*3
        for cmd in commands:
            try:
                _,at=batch.get(day,'AU',cmd);trials.append(dict(command=cmd,acquisition_status='RETURNED',captured_at=at.isoformat()))
            except Exception as exc:trials.append(dict(command=cmd,acquisition_status='BLOCKED',reason=type(exc).__name__))
        out['command_acquisition_trials']=trials;out['batch_receipts']=batch.receipts
        out['C']=dict(provider_calls=0,mode='not submitted to acquisition; existing read-only status path unchanged')
        # Fresh primary Queensland evidence, once per field PDF. It is already
        # after Ipswich's last jump; do not turn a post-jump check into a pilot.
        out['rq_primary']=capture_races(day,[7],root/'rq-private')
        out['rq_cohort_prejump_available']=any(timestamp(r['jump_time'])>ops.utcnow() for m in payload['data'] if m.get('state')=='QLD' for r in m.get('races',[]) if r.get('jump_time'))
        # Genuine inference attempt on an upcoming AU race, one shared capture.
        # Admission remains blocked absent an independently verified operator,
        # primary state authority and compatible historical evidence.
        if upcoming:
            _,m,r=upcoming[0];req=ops.command(f"RM6 {m['venue']} {r['number']}",day,'AU')
            f=ops.execute(day,root/'live-race',Path('v7_engine'),run_id=os.environ['GITHUB_RUN_ID']+'-data-pilot',
                payload=payload,captured=captured,request=req,timings=True)
            out['new_live_inference']=True
            out['live_pilot']=dict(meeting=m['venue'],race=r['number'],jump=r['jump_time'],status=f['status'],
                captured_at=f.get('captured_at'),models=f['models'],races=[dict(meeting=x['meeting'],race=x['race'],
                market_integrity=x.get('market_integrity'),outcomes={v:dict(status=z['status'],classification=z.get('prediction_classification'),
                reasons=z.get('no_bet_reasons')) for v,z in x['models'].items()}) for x in f['races']],
                forecast_sha256=ops.sha(root/'live-race/public/forecast.json'),receipt_sha256=ops.sha(root/'live-race/public/receipt.json'),
                independently_verified=False,admission='NOT ADMITTED — authority/operator/history verification incomplete')
        else:out['live_pilot']={'status':'NO_UPCOMING_AU_RACE_IN_CAPTURE'}
    except Exception as exc:out['blocker']=type(exc).__name__
    out['usage']=usage;out['usage_summary']=usage_summary(usage)
    out['free_trial']=dict(separate_free_credential_configured=bool(os.getenv('KROK_FREE_API_KEY')),
        verified_free_plan=False,blocker='Existing credential tier is not proof of a Free account; no plan/billing changes made')
    if os.getenv('KROK_FREE_API_KEY'):
        free_usage=[]
        try:
            free=krok_adapter.fetch(day,os.environ['KROK_FREE_API_KEY'],meter=free_usage,command='FREE bounded acquisition trial',country='AU')
            verified=bool(free_usage) and all(x.get('x-credits-limit')==50 and x.get('x-ratelimit-limit')==5 for x in free_usage)
            out['free_trial'].update(usage=free_usage,coverage=inventory(free,ops.utcnow()),verified_free_plan=verified,
                blocker=None if verified else 'Free plan limits not verified from response headers')
        except Exception as exc:out['free_trial'].update(usage=free_usage,blocker=type(exc).__name__)
    # Optional credentials are never requested in chat or echoed.
    out['formfav']=call_formfav(day,os.getenv('FORMFAV_API_KEY'))
    pe=os.getenv('PUNTERSEDGE_API_KEY')
    out['puntersedge']={'credential_configured':bool(pe),'live_independence_verified':False}
    if pe:
        status,data=request('https://api.puntersedge.online','/v1/racing/next-to-go',pe,{'limit':1})
        out['puntersedge']['next_to_go']=dict(status,returned_object=data is not None)
    out['finished_at']=ops.utcnow().isoformat()
    ops.write(public/'data-cost-pilot.json',out)
    print(json.dumps(dict(workflow_url=out['workflow_url'],usage=out['usage_summary'],live_pilot_status=out.get('live_pilot',{}).get('status'),blocker=out.get('blocker'))))


if __name__=='__main__':main()
