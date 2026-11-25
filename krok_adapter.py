#!/usr/bin/env python3
"""Krok documented /api/v1/racing/meetings adapter -> Monty v0.4 snapshot.
Requires user-provided API key; no unofficial TAB endpoints or fabricated features.
"""
import argparse, datetime as dt, json, math, os, urllib.parse, urllib.request, urllib.error, time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'monty_v6'))
from monty.normalization import condition

BASE='https://krokodds.com.au/api/v1/racing/meetings'

class IncompleteFields(ValueError):
    pass

def number(value):
    try:
        f=float(value)
        return f if 1<f<float('inf') else None
    except (ValueError,TypeError):return None

def price(r):
    # Prefer a directly attributed TAB quote; otherwise a clearly labelled fixed price.
    for quote in r.get('odds',[]) if isinstance(r.get('odds'),list) else []:
        if isinstance(quote,dict) and str(quote.get('bookmaker','')).strip().lower()=='tab':
            p=number(quote.get('win'))
            if p:return p,'TAB'
    for key in ('fixed_win','best_win'):
        p=number(r.get(key))
        if p:return p,key
    return None,None

# Named fixed-odds operators only; an exchange quote is not a bookmaker price.
FIXED_BOOKMAKERS={name.casefold():name for name in
    ('TAB','TABtouch','Sportsbet','Ladbrokes','Neds','bet365','PointsBet','Unibet',
     'Betr','BetDeluxe','PlayUp','Dabble','BlueBet','Bet Nation','Amused')}


def named_bookmaker(r,selected,origin):
    """Attribute only the exact price already selected; never substitute odds."""
    if origin=='TAB':return 'TAB'
    def known(value):
        return FIXED_BOOKMAKERS.get(str(value or '').strip().casefold())
    # A best-win operator describes best_win, not a differently priced fixed_win.
    name=known(r.get(origin+'_bookmaker'))
    if name and number(r.get(origin))==selected:return name
    for quote in r.get('odds',[]) if isinstance(r.get('odds'),list) else []:
        if not isinstance(quote,dict):continue
        name=known(quote.get('bookmaker'))
        if name and str(quote.get('bookmaker_type','fixed')).lower()=='fixed' and number(quote.get('win'))==selected:
            return name
    return None

def normalize(payload,date,*,allow_restricted_classes=False):
    if not isinstance(payload,dict) or payload.get('success') is not True or not isinstance(payload.get('data'),list):
        raise ValueError('Unexpected API response; expected success=true and data[]')
    meta=payload.get('meta') or {}
    if meta.get('truncated') or meta.get('has_more') or meta.get('next_cursor') or meta.get('next_page') or meta.get('next'):
        raise ValueError('Meeting feed paginated/truncated; refusing to treat it as complete')
    rows=[];races=[];skipped=[];meetings=0
    for meeting in payload['data']:
        if meeting.get('type') not in ('T','R'):continue
        if meeting.get('country') not in (None,'AU','NZ'):continue
        if str(meeting.get('date',''))[:10]!=date:
            skipped.append(f"{meeting.get('venue')}: wrong or missing date");continue
        venue=meeting.get('venue')
        if not venue:continue
        meetings+=1
        for race in meeting.get('races',[]):
            n=race.get('number');status=str(race.get('status','')).lower()
            if n is None or status in ('abandoned','cancelled','canceled','resulted','closed','final'):
                continue
            # Exclude only races positively identified as prohibited; ambiguous classes remain research-only.
            label=' '.join(str(race.get(k) or '') for k in ('name','race_name','class','race_class','description','type')).lower()
            if not allow_restricted_classes and any(x in label for x in ('maiden','2yo','2 year old','two year old','hurdle','steeple','jumping')):
                skipped.append(f'{venue} R{n}: prohibited race type');continue
            rr=race.get('runners')
            if not isinstance(rr,list) or len(rr)<2:
                skipped.append(f'{venue} R{n}: missing runners');continue
            active=[r for r in rr if r.get('is_scratched') is False]
            uncertain=[r for r in rr if r.get('is_scratched') not in (True,False)]
            if uncertain or len(active)<2:
                skipped.append(f'{venue} R{n}: scratching status uncertain');continue
            declared=race.get('runner_count')
            # Counts can include scratchings; do not equate them to active counts.
            if isinstance(declared,int) and declared<len(active):
                skipped.append(f'{venue} R{n}: contradictory runner count');continue
            parsed=[]
            for r in active:
                p,origin=price(r)
                if p is None or r.get('number') is None or not r.get('name'):
                    break
                item={'meeting':venue,'race':str(n),'number':str(r['number']), 'horse':r['name'],'odds':p}
                for source,target in [('barrier','barrier'),('weight','allocated_weight'),('age','age'),('claim_kg','claim_kg')]:
                    v=r.get(source)
                    if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v):
                        item[target]=v
                distance=race.get('distance_m',race.get('distance'))
                if isinstance(distance,(int,float)) and not isinstance(distance,bool) and math.isfinite(distance) and distance>0:
                    item['distance_km']=distance/1000
                raw_going = race.get('track_condition')
                if raw_going is None or not str(raw_going).strip():
                    raw_going = meeting.get('track_hint')
                going = condition(raw_going)
                for g in ('good','soft','heavy','firm','synthetic','unknown'):
                    item['going_'+g] = float(going == g)
                item['_price_source']=origin
                item['_bookmaker']=named_bookmaker(r,p,origin)
                parsed.append(item)
            if len(parsed)!=len(active):
                skipped.append(f'{venue} R{n}: active runner lacks identity/price');continue
            if len({r['number'] for r in parsed})!=len(parsed):
                skipped.append(f'{venue} R{n}: duplicate saddlecloth');continue
            # Derive deterministic race-relative features only when field is complete.
            field_size=len(parsed)
            for item in parsed:
                b=item.get('barrier')
                if isinstance(b,(int,float)) and b>0:
                    item['barrier_fraction']=b/max(field_size,1)
                    item['inside_three']=int(b<=3)
                    item['outside_barrier']=float(b>field_size*.75)
                    if 'distance_km' in item:
                        item['barrier_x_distance']=(b/field_size)*item['distance_km']
                # A missing claim is unknown, not evidence of a zero claim.
                # Never impute a frozen-model input without source evidence.
                if 'allocated_weight' in item and 'claim_kg' in item:
                    item['effective_weight']=item['allocated_weight']-item['claim_kg']
            rows.extend(parsed)
            races.append({'meeting':venue,'race':str(n),'expected_active_runners':len(active)})
    if not rows:raise IncompleteFields('No complete, priced, active thoroughbred fields found')
    return {'date':date,'runners':rows,'races':races}, {'meetings':meetings,'races_accepted':len(races),'runners_accepted':len(rows),'skipped':skipped,'tab_verified':False,'count_basis':'same provider runner list; NOT independently TAB verified','price_sources':sorted(set(r['_price_source'] for r in rows)), 'price_source_counts':{source:sum(r['_price_source']==source for r in rows) for source in sorted(set(r['_price_source'] for r in rows))}}

def _fetch_body(req,deadline,meter=None,command=None):
    """Retry transient acquisition failures only; no alternate source/model."""
    for attempt in range(3):
        attempt_started=time.monotonic()
        remaining=deadline-time.monotonic()
        if remaining<=0:raise ValueError('Krok acquisition deadline exceeded')
        try:
            with urllib.request.urlopen(req,timeout=min(20,remaining)) as response:
                body=response.read(20_000_001)
                if meter is not None:
                    from operations.data_acquisition import record_usage
                    record_usage(meter,req.full_url,getattr(response,'status',200),getattr(response,'headers',{}),command,attempt_started)
            if time.monotonic()>deadline:raise ValueError('Krok acquisition deadline exceeded')
            return body
        except urllib.error.HTTPError as exc:
            if meter is not None:
                from operations.data_acquisition import record_usage
                record_usage(meter,req.full_url,exc.code,exc.headers,command,attempt_started)
            if exc.code not in (429,500,502,503,504) or attempt==2:raise
            from email.utils import parsedate_to_datetime
            retry=exc.headers.get('Retry-After','0')
            try:delay=max(0,int(retry))
            except ValueError:
                try:delay=max(0,(parsedate_to_datetime(retry)-dt.datetime.now(dt.timezone.utc)).total_seconds())
                except (ValueError,TypeError):delay=0
            delay=max(delay,.5*2**attempt)
            if delay>=deadline-time.monotonic():raise ValueError('Krok retry exceeds acquisition deadline') from None
            time.sleep(delay)
        except (urllib.error.URLError,TimeoutError):
            if meter is not None:
                from operations.data_acquisition import record_usage
                record_usage(meter,req.full_url,None,{},command,attempt_started)
            if attempt==2:raise
            time.sleep(min(.5*2**attempt,max(0,deadline-time.monotonic())))


def fetch(date,key,*,meter=None,command=None,country=None,venue=None,dated_card=False,observer=None):
    """Follow explicit pagination markers; never accept an incomplete meeting feed."""
    if not key:raise ValueError('Set KROK_API_KEY; never paste API keys into chat')
    params={'date':date,'race_type':'T','limit':50}
    if country:
        if country not in ('AU','NZ'):raise ValueError('Unsupported racing country')
        params['country']=country
    if venue:params['venue']=venue
    endpoint=BASE+'/'+date if dated_card else BASE
    if dated_card:params.pop('date')
    seen=set()
    meetings=[]
    declared_total=None
    deadline=time.monotonic()+60
    for page_index in range(100):
        url=endpoint+'?'+urllib.parse.urlencode(params)
        if url in seen:raise ValueError('Repeated meeting pagination pointer')
        seen.add(url)
        req=urllib.request.Request(url,headers={'X-API-Key':key,'Accept':'application/json','User-Agent':'Monty-V6/0.5'})
        body=_fetch_body(req,deadline,meter,command) if meter is not None else _fetch_body(req,deadline)
        if len(body)>20_000_000:raise ValueError('Response too large')
        if observer is not None:
            try:observer(body,urllib.parse.urlsplit(endpoint).path)
            except Exception:pass  # Evidence failure must not trigger another provider call.
        payload=json.loads(body)
        if not isinstance(payload,dict) or payload.get('success') is not True or not isinstance(payload.get('data'),list):
            raise ValueError('Invalid meeting feed page')
        meta=payload.get('meta') or {}
        if not isinstance(meta,dict):
            raise ValueError('Meeting feed metadata is '+type(meta).__name__+' (expected object)')
        # A truncated page is acceptable only when an explicit continuation exists.
        # Never accept a truncated final page as a complete feed.
        total=meta.get('total')
        if isinstance(total,bool) or not isinstance(total,int) or total<0:
            raise ValueError('Krok meeting total missing or invalid')
        if declared_total is None:
            declared_total=total
        elif total!=declared_total:
            raise ValueError('Krok meeting total changed between pages')
        if meta.get('truncated') and not (meta.get('next_cursor') or meta.get('next_page') or meta.get('next')):
            if meta.get('has_more') is not False or len(meetings)+len(payload['data'])!=declared_total:
                raise ValueError('Truncated meeting page without continuation and verified total'
                    +'; page_index='+str(page_index+1)
                    +'; received='+str(len(meetings)+len(payload['data']))
                    +'; declared_total='+str(declared_total)
                    +'; has_more='+str(meta.get('has_more')))
        meetings.extend(payload['data'])
        if len(meetings)>5000:raise ValueError('Meeting pagination exceeds safety limit')
        cursor=meta.get('next_cursor')
        next_page=meta.get('next_page')
        next_marker=meta.get('next')
        more=meta.get('has_more')
        pointers=[x for x in (cursor,next_page,next_marker) if x not in (None,'',False)]
        if not pointers and not more:
            if meta.get('has_more') is not False:
                raise ValueError('Final meeting page has no explicit has_more=false')
            if len(meetings)!=declared_total:
                raise ValueError('Meeting count mismatch: received '+str(len(meetings))+
                                 ', declared '+str(declared_total))
            # Provider may mark a final page truncated even after the exact
            # declared total is retrieved; counts and has_more must agree.
            # Only this fully fetched aggregate may reach normalize().
            # Duplicate meetings are unsafe because their race data may differ.
            keys=set()
            for m in meetings:
                if not isinstance(m,dict):raise ValueError('Invalid meeting record')
                identity=(str(m.get('date')),str(m.get('country')),str(m.get('venue')),str(m.get('type')))
                if identity in keys:raise ValueError('Duplicate meeting across pages: '+str(identity))
                keys.add(identity)
            return {'success':True,'data':meetings,'meta':{'has_more':False,'pages_fetched':page_index+1}}
        if cursor not in (None,'',False):
            params.pop('page',None)
            params['cursor']=str(cursor)
        elif next_page not in (None,'',False):
            if isinstance(next_page,bool) or not str(next_page).isdigit():
                raise ValueError('Unrecognized next_page pagination marker')
            params.pop('cursor',None)
            params['page']=str(next_page)
        elif next_marker not in (None,'',False):
            if isinstance(next_marker,bool) or not str(next_marker).isdigit():
                raise ValueError('Unrecognized next pagination marker')
            params.pop('cursor',None)
            params['page']=str(next_marker)
        else:
            raise ValueError('Meeting feed has_more but no usable next-page marker')
    raise ValueError('Meeting pagination exceeded 100 pages')

def main():
    p=argparse.ArgumentParser();p.add_argument('--date',required=True);p.add_argument('--fixture',help='Use a local API JSON fixture instead of live fetch');p.add_argument('--output-dir',default='output_v05');a=p.parse_args()
    dt.date.fromisoformat(a.date)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    raw=json.loads(Path(a.fixture).read_text()) if a.fixture else fetch(a.date,os.environ.get('KROK_API_KEY'))
    snapshot,audit=normalize(raw,a.date)
    (out/'krok_raw.json').write_text(json.dumps(raw,indent=2))
    (out/'krok_snapshot.json').write_text(json.dumps(snapshot,indent=2))
    (out/'krok_adapter_audit.json').write_text(json.dumps(audit,indent=2))
    from run_day import run
    result=run(str(out/'krok_snapshot.json'),a.date,str(out/'scored'))
    print(json.dumps({'adapter':audit,'scoring':result},indent=2))

if __name__=='__main__':main()
