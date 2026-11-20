#!/usr/bin/env python3
"""Krok documented /api/v1/racing/meetings adapter -> Monty v0.4 snapshot.
Requires user-provided API key; no unofficial TAB endpoints or fabricated features.
"""
import argparse, datetime as dt, json, os, re, urllib.parse, urllib.request, urllib.error, time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'monty_v6'))
from monty.normalization import condition

BASE='https://krokodds.com.au/api/v1/racing/meetings'

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

def normalize(payload,date,include_restricted_flat_research=False):
    if not isinstance(payload,dict) or payload.get('success') is not True or not isinstance(payload.get('data'),list):
        raise ValueError('Unexpected API response; expected success=true and data[]')
    meta=payload.get('meta') or {}
    if not isinstance(meta,dict):
        raise ValueError('Unexpected provider pagination metadata type')
    if any(not isinstance(m,dict) for m in payload['data']):
        raise ValueError('Unexpected provider meeting record type')
    if meta.get('truncated') or meta.get('has_more') or meta.get('next_cursor') or meta.get('next_page') or meta.get('next'):
        raise ValueError('Meeting feed paginated/truncated; refusing to treat it as complete')
    # Fetch requests limit=50 meetings. A full page without a trustworthy
    # pagination terminator cannot prove complete AU/NZ coverage.
    if len(payload['data']) >= 50 and not (meta.get('has_more') is False or meta.get('is_last_page') is True or meta.get('total_pages') == 1):
        raise ValueError('Provider returned the 50-meeting page limit without an explicit end-of-feed signal')
    rows=[];races=[];skipped=[];meetings=0;incomplete_race_diagnostics=[]
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
            # Only known pre-off states are eligible for research scoring.
            # Unknown, running and resulted races must never be treated as pre-race.
            if n is None or status not in ('open','scheduled','upcoming','pre-race','prerace'):
                skipped.append(f'{venue} R{n}: not confirmed pre-race status');continue
            # Jumps remain excluded. Maiden and juvenile flat races may be
            # scored for research ONLY when explicitly enabled.
            label=' '.join(str(race.get(k) or '') for k in ('name','race_name','class','race_class','description','type')).lower()
            jumps=bool(re.search(r'\b(?:hurdle|steeple|jumping|jumps|chase)\b',label))
            maiden=bool(re.search(r'\b(?:maiden|mdn|maid)\b',label))
            juvenile=bool(re.search(r'\b(?:2yo|2\s*[- ]?\s*y\s*[- ]?\s*o|2\s*year\s*old|two\s*year\s*old|juvenile)\b',label))
            if isinstance(race.get('runners'),list):
                ages=[r.get('age') for r in race['runners'] if r.get('is_scratched') is False]
                juvenile=juvenile or (bool(ages) and all(isinstance(age,(int,float)) and not isinstance(age,bool) and age==2 for age in ages))
            # Unknown class is permitted for scoring, but not represented as
            # positively verified to be an unrestricted race.
            classification_unknown=not bool(label.strip())
            restricted=jumps or maiden or juvenile
            if jumps or (restricted and not include_restricted_flat_research):
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
                item={'meeting':venue,'race':str(n),'number':str(r['number']), 'horse':r['name'],'odds':p, 'research_only_restricted_race':bool(maiden or juvenile), 'race_classification_unknown':classification_unknown, 'betting_authorised':False}
                for source,target in [('barrier','barrier'),('weight','allocated_weight'),('age','age'),('claim_kg','claim_kg')]:
                    v=r.get(source)
                    if isinstance(v,(int,float)) and not isinstance(v,bool):item[target]=v
                distance=race.get('distance_m',race.get('distance'))
                if isinstance(distance,(int,float)) and distance>0:item['distance_km']=distance/1000
                raw_going = race.get('track_condition')
                if raw_going is None or not str(raw_going).strip():
                    raw_going = meeting.get('track_hint')
                going = condition(raw_going)
                for g in ('good','soft','heavy','firm','synthetic','unknown'):
                    item['going_'+g] = float(going == g)
                item['_price_source']=origin
                parsed.append(item)
            if len(parsed)!=len(active):
                # Record only public race identifiers and aggregate missing-field counts.
                # Never silently drop a runner to make a field scoreable.
                incomplete_race_diagnostics.append({
                    'meeting': str(venue), 'race': str(n),
                    'missing_price': sum(price(r)[0] is None for r in active),
                    'missing_number': sum(r.get('number') is None for r in active),
                    'missing_name': sum(not r.get('name') for r in active),
                    'class_label_present': bool(label.strip()),
                    'price_status': ('no_fixed_win_prices' if all(price(r)[0] is None for r in active) else 'partial_fixed_win_prices') if any(price(r)[0] is None for r in active) else 'prices_present_identity_incomplete',
                    'retry_candidate_when_prices_update': all(r.get('number') is not None and bool(r.get('name')) for r in active) and any(price(r)[0] is None for r in active),
                    'retry_reason': 'await_complete_fixed_win_prices' if all(r.get('number') is not None and bool(r.get('name')) for r in active) and any(price(r)[0] is None for r in active) else 'identity_or_other_data_incomplete',
                })
                skipped.append(f'{venue} R{n}: active runner lacks identity/price');continue
            if len({r['number'] for r in parsed})!=len(parsed):
                skipped.append(f'{venue} R{n}: duplicate saddlecloth');continue
            # A race must use one quoted price basis; mixed bookmakers distort
            # normalized market probabilities and apparent edge.
            if len({item['_price_source'] for item in parsed})!=1:
                skipped.append(f'{venue} R{n}: mixed price sources');continue
            # Derive deterministic race-relative features only when field is complete.
            field_size=len(parsed)
            for item in parsed:
                b=item.get('barrier')
                if isinstance(b,(int,float)) and b>0:
                    item['barrier_fraction']=b/max(field_size,1)
                    item['inside_three']=int(b<=3)
                    item['outside_barrier']=float(b>field_size*.75)
                    if 'distance_km' in item:item['barrier_x_distance']=b/field_size*distance/1000
                if 'allocated_weight' in item:
                    item['effective_weight']=item['allocated_weight']-item.get('claim_kg',0)
            rows.extend(parsed)
            races.append({'meeting':venue,'race':str(n),'expected_active_runners':len(active),'research_only_restricted_race':bool(maiden or juvenile),'race_classification_unknown':classification_unknown,'betting_authorised':False})
    # Explain recoverable provider-data gaps without fabricating missing odds.
    incomplete_summary={
        'races':len(incomplete_race_diagnostics),
        'races_missing_price':sum(d['missing_price']>0 for d in incomplete_race_diagnostics),
        'races_missing_number':sum(d['missing_number']>0 for d in incomplete_race_diagnostics),
        'races_missing_name':sum(d['missing_name']>0 for d in incomplete_race_diagnostics),
        'missing_price_runner_slots':sum(d['missing_price'] for d in incomplete_race_diagnostics),
        'missing_number_runner_slots':sum(d['missing_number'] for d in incomplete_race_diagnostics),
        'missing_name_runner_slots':sum(d['missing_name'] for d in incomplete_race_diagnostics),
        'races_no_fixed_win_prices':sum(d['price_status']=='no_fixed_win_prices' for d in incomplete_race_diagnostics),
        'races_partial_fixed_win_prices':sum(d['price_status']=='partial_fixed_win_prices' for d in incomplete_race_diagnostics),
        'races_prices_present_identity_incomplete':sum(d['price_status']=='prices_present_identity_incomplete' for d in incomplete_race_diagnostics),
        'races_retry_candidate_when_prices_update':sum(d['retry_candidate_when_prices_update'] for d in incomplete_race_diagnostics),
    }
    # A venue/race key must identify exactly one field. Duplicate provider records
    # would otherwise silently merge separate fields in downstream scoring.
    keys=[(str(r['meeting']).strip().casefold(),str(r['race']).strip()) for r in races]
    if len(keys)!=len(set(keys)):
        raise ValueError('Duplicate meeting/race identity in provider feed')
    if not rows:raise ValueError('No complete, priced, active thoroughbred fields found')
    return {'date':date,'runners':rows,'races':races}, {'meetings':meetings,'races_accepted':len(races),'runners_accepted':len(rows),'restricted_flat_research_races':sum(r['research_only_restricted_race'] for r in races),'skipped':skipped,'incomplete_race_diagnostics':incomplete_race_diagnostics,'incomplete_race_summary':incomplete_summary,'tab_verified':False,'count_basis':'same provider runner list; NOT independently TAB verified','price_sources':sorted(set(r['_price_source'] for r in rows))}

def fetch(date,key):
    """Read complete dated full cards using documented cursor pagination."""
    if not key:
        raise ValueError('Set KROK_API_KEY; never paste API keys into chat')
    records=[]
    seen_cursors=set()
    seen_meetings=set()
    cursor=None
    for attempt in range(100):
        # Krok's dated summary board is NOT the complete runner feed.
        # Dated full=1 supports cursor pages (max 25 meetings).
        params={'full':'1','limit':25,'race_type':'T'}
        if cursor is not None:
            params['cursor']=cursor
        url=BASE+'/'+date+'?'+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={
            'X-API-Key':key,'Accept':'application/json',
            'User-Agent':'Monty-V6/0.5'})
        with urllib.request.urlopen(req,timeout=35) as resp:
            body=resp.read(20_000_001)
        if len(body)>20_000_000:
            raise ValueError('Response too large')
        payload=json.loads(body)
        if (not isinstance(payload,dict) or payload.get('success') is not True
                or not isinstance(payload.get('data'),list)):
            raise ValueError('Invalid provider page response')
        meta=payload.get('meta') or {}
        if not isinstance(meta,dict):
            raise ValueError('Invalid pagination metadata')
        batch=payload['data']
        if not batch and (meta.get('has_more') or meta.get('truncated')):
            raise ValueError('Provider returned empty nonterminal page')
        for meeting in batch:
            if not isinstance(meeting,dict):
                raise ValueError('Invalid meeting record')
            identity=str(meeting.get('id') or meeting.get('meeting_key') or
                         (meeting.get('date'),meeting.get('venue'),meeting.get('type')))
            if identity in seen_meetings:
                raise ValueError('Duplicate meeting across cursor pages')
            seen_meetings.add(identity)
        records.extend(batch)
        more=meta.get('has_more')
        nxt=meta.get('next_cursor')
        if more is True or nxt:
            if not nxt or not isinstance(nxt,str) or nxt in seen_cursors:
                raise ValueError('Incomplete full-card feed: missing/repeated next_cursor')
            seen_cursors.add(nxt)
            cursor=nxt
            continue
        if more is False and not meta.get('truncated') and not nxt:
            return {'success':True,'data':records,
                    'meta':{'has_more':False,'is_last_page':True,
                            'pages_fetched':attempt+1}}
        raise ValueError('Provider did not confirm end of full-card feed')
    raise ValueError('Provider pagination exceeded 100 pages')

def main():
    p=argparse.ArgumentParser();p.add_argument('--date',required=True);p.add_argument('--fixture',help='Use a local API JSON fixture instead of live fetch');p.add_argument('--output-dir',default='output_v05');p.add_argument('--provisional-operational',action='store_true',help='Use provisional V6 scorer; research only, not betting-authorised');a=p.parse_args()
    dt.date.fromisoformat(a.date)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    raw=json.loads(Path(a.fixture).read_text()) if a.fixture else fetch(a.date,os.environ.get('KROK_API_KEY'))
    snapshot,audit=normalize(raw,a.date)
    (out/'krok_raw.json').write_text(json.dumps(raw,indent=2))
    (out/'krok_snapshot.json').write_text(json.dumps(snapshot,indent=2))
    (out/'krok_adapter_audit.json').write_text(json.dumps(audit,indent=2))
    if a.provisional_operational:
        import subprocess
        subprocess.run([sys.executable,str(Path(__file__).resolve().parent/'operational'/'run_snapshot.py'),str(out/'krok_snapshot.json'),'--output-dir',str(out/'provisional_scored')],check=True)
        result={'status':'PROVISIONAL_RESEARCH_ONLY','output_dir':str(out/'provisional_scored'),'betting_authorised':False}
    else:
        from run_day import run
        result=run(str(out/'krok_snapshot.json'),a.date,str(out/'scored'))
    print(json.dumps({'adapter':audit,'scoring':result},indent=2))

if __name__=='__main__':main()
