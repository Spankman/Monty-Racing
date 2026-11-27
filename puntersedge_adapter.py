"""Staged read-only PuntersEdge acquisition. Never an automatic model fallback.

Raw responses are personal-use data and must remain private. No provider picks,
account mutation, wager/betslip routes, signup or billing requests are supported.
"""
from datetime import datetime,timezone
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
import hashlib,json,os,time
from operations.data_acquisition import record_usage

BASE='https://api.puntersedge.online'
COSTS={'/v1/usage':0,'/v1/racing/events':1,'/v1/racing/next-to-go':4,
       '/v1/racing/acceptances':2,'/v1/racing/form':3,'/v1/racing/horses/form':3,
       '/v1/racing/horses/runs':3,'/v1/racing/results':2,'/v1/racing/results/coverage':0,
       '/v1/racing/changes':2,'/v1/racing/track-conditions':1,'/v1/racing/markets':2,
       '/v1/racing/price-history':5}


class ProviderError(RuntimeError):pass
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


class Client:
    def __init__(self,key=None,*,budget=40,opener=None,sleeper=time.sleep,observer=None):
        self._key=key or os.getenv('PUNTERSEDGE_API_KEY','')
        if not self._key:raise ProviderError('PuntersEdge credential unavailable')
        self.open=opener or build_opener(NoRedirect()).open
        self.observer=observer;self.observer_errors=[];self.sleep=sleeper;self.budget=budget;self.reserved=0;self.usage=[];self.responses=[]

    def get(self,path,params=None,*,command='STAGING'):
        if command.strip().upper()=='C':raise ProviderError('C cannot acquire data')
        if path not in COSTS:raise ProviderError('Unsupported read-only provider route')
        estimated_cost=COSTS[path]
        if path=='/v1/racing/next-to-go':
            requested=int((params or {}).get('limit',(params or {}).get('num_races',10)))
            if not 1<=requested<=200:raise ProviderError('Unsupported requested race count')
            estimated_cost=2 if requested<=20 else 3 if requested<=60 else 4
        url=BASE+path+('?' + urlencode(params) if params else '')
        for attempt in range(2):
            if self.reserved+estimated_cost>self.budget:raise ProviderError('Staging request budget reached')
            self.reserved+=estimated_cost
            started=time.monotonic();request_at=datetime.now(timezone.utc).isoformat()
            req=Request(url,headers={'X-API-Key':self._key,'Accept':'application/json','User-Agent':'Monty-personal-staging/1.0'})
            try:
                with self.open(req,timeout=20) as response:
                    body=response.read(10_000_001);headers=response.headers;status=response.status
                record_usage(self.usage,url,status,headers,command,started)
                if len(body)>10_000_000:raise ProviderError('Provider response exceeds bound')
                if self.observer is not None:
                    try:self.observer(body,path)
                    except Exception:self.observer_errors.append('raw_observer_failed')
                value=json.loads(body)
                if not isinstance(value,(dict,list)):raise ProviderError('Unexpected provider payload')
                self.responses.append(dict(endpoint=path,request_at=request_at,received_at=datetime.now(timezone.utc).isoformat(),
                    response_date=headers.get('Date'),cache_control=headers.get('Cache-Control'),
                    sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),status=status))
                return value
            except HTTPError as exc:
                record_usage(self.usage,url,exc.code,exc.headers,command,started)
                if attempt==0 and exc.code in (429,500,502,503,504):
                    try:delay=max(.5,float(exc.headers.get('Retry-After','1')))
                    except ValueError:delay=1
                    if delay<=30:self.sleep(delay);continue
                raise ProviderError('PuntersEdge HTTP '+str(exc.code)) from None
            except (URLError,TimeoutError,OSError):
                record_usage(self.usage,url,None,{},command,started)
                if attempt==0:self.sleep(.5);continue
                raise ProviderError('PuntersEdge transport failure') from None
            except (ValueError,TypeError):raise ProviderError('PuntersEdge JSON contract failure') from None


def safe_usage(value):
    """No email, key metadata, billing links or upgrade URLs in reports."""
    keys=('plan','credits_used','credits_limit','credits_remaining','period_start','next_reset_at','reset_at')
    return {k:value[k] for k in keys if k in value and isinstance(value[k],(str,int,float))}


BOOKS={'tab':'TAB','sportsbet':'Sportsbet','ladbrokes_au':'Ladbrokes','neds':'Neds',
       'pointsbetau':'PointsBet','tabtouch':'TABtouch','unibet':'Unibet','betdeluxe':'BetDeluxe','playup':'PlayUp'}


def canonical_race(race,*,day,book='tab',acceptance=None):
    """One explicit full fixed-WIN book -> existing feature builder, no fitting.

    Non-poll time bases remain timestamp-unverified. No best-of-book synthesis,
    name-derived national identity, historical stats, expert or exotic inputs.
    A returned payload supports provisional scoring; it is never betting approval.
    """
    from operations.market_integrity import timestamp
    from zoneinfo import ZoneInfo
    if book not in BOOKS:raise ProviderError('Unsupported named fixed bookmaker')
    if race.get('country')!='AU' or race.get('category')!='horse':raise ProviderError('Confirmed AU thoroughbred race required')
    if (race.get('market_closed_at') or race.get('inplay_at') or race.get('inplay') is True
            or str(race.get('status','')).casefold() in ('closed','final','resulted','abandoned','cancelled','canceled')):
        raise ProviderError('Race explicitly closed or in play')
    jump=timestamp(race['start_time'])
    if jump.astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat()!=day:raise ProviderError('Race date mismatch')
    declarations={};seen=set();runners=[]
    for r in race.get('runners',[]):
        number=str(r.get('number'))
        if not number.isdigit() or int(number)<1 or not isinstance(r.get('name'),str) or not r['name'].strip() or number in seen:
            raise ProviderError('Invalid or duplicate runner identity')
        seen.add(number);declarations[number]=r['name']
        quotes=[q for q in r.get('bookmakers',[]) if q.get('key')==book]
        if len(quotes)!=1:raise ProviderError('Complete single-book field required')
        q=quotes[0];p=q.get('win_price')
        if type(p) not in (int,float) or not 1<p<float('inf'):raise ProviderError('Invalid fixed-win price')
        offer=dict(bookmaker=BOOKS[book],win=p,_collector='PuntersEdge')
        # next-to-go age_basis=poll is the collector's own read; last_update
        # there is not /markets.observed_at (a last price-change clock).
        if q.get('age_basis')=='poll' and q.get('last_update'):
            timestamp(q['last_update'])  # No naive timestamps or invented UTC.
            offer['captured_at']=q['last_update']
        row=dict(number=r['number'],name=r['name'],is_scratched=False,odds=[offer],
            fixed_win=p,fixed_win_bookmaker=BOOKS[book])
        for source,target in [('barrier','barrier'),('weight','weight'),('jockey','jockey'),('trainer','trainer')]:
            if r.get(source) is not None:row[target]=r[source]
        runners.append(row)
    if len(runners)<2:raise ProviderError('At least two active runners required')
    for r in race.get('scratchings',[]) or []:
        number=str(r.get('number'))
        if not number.isdigit() or int(number)<1 or number in seen or not r.get('name'):raise ProviderError('Conflicting scratching identity')
        seen.add(number);declarations[number]=r['name']
        runners.append(dict(number=r['number'],name=r['name'],is_scratched=True))
    if acceptance is not None:
        # Explicit number+name+scratching agreement, never name-only crosswalk.
        expected={str(r['number']):(r['name'],r['scratched']) for r in acceptance}
        actual={str(r['number']):(r['name'],r['is_scratched']) for r in runners}
        if len(expected)!=len(acceptance) or expected!=actual:raise ProviderError('Acceptance field mismatch')
    meeting=dict(venue=race['venue'],country='AU',type='T',date=day,races=[dict(number=race['race_number'],
        jump_time=race['start_time'],status='open',name=race.get('race_name'),race_class=race.get('race_class'),
        distance_m=race.get('distance_m'),track_condition=race.get('track_condition'),runner_count=len(runners),runners=runners)])
    return dict(success=True,data=[meeting],meta=dict(has_more=False,provider='PuntersEdge',
        source_race_id=race.get('race_id'),independent_verification=False,historical_features_joined=False))

def join_acceptances(card, declaration):
    """PR263 same-provider dated field join; never independent verification."""
    if declaration.get('runner_set_status')=='gap_detected':raise ProviderError('PuntersEdge acceptances report a field gap')
    rows=declaration.get('runners')
    if not isinstance(rows,list) or not rows:raise ProviderError('Acceptance runner roster unavailable')
    declared={str(r.get('number')):r for r in rows}
    if len(declared)!=len(rows) or any(not n.isdigit() or int(n)<1 for n in declared):raise ProviderError('Duplicate or invalid acceptance identity')
    offered={str(r['number']):r for r in card['runners'] if not r['is_scratched']}
    if set(offered)-set(declared):raise ProviderError('Priced runner absent from dated acceptance roster')
    for number,row in declared.items():
        if type(row.get('scratched')) is not bool:raise ProviderError('Acceptance scratching state unknown')
        if row['scratched'] and number in offered:raise ProviderError('Active quote conflicts with declared scratching')
        if not row['scratched'] and row.get('emergency') is False and number not in offered:
            raise ProviderError('Declared active runner missing from price board')
        if number in offered:
            name=row.get('runner_name')
            if not isinstance(name,str) or name.strip().casefold()!=offered[number]['name'].strip().casefold():
                raise ProviderError('Price and acceptance identities disagree')
            for source,target in [('age','age'),('claim_kg','claim_kg')]:
                if row.get(source) is not None:offered[number][target]=row[source]
    for source,target in [('race_name','name'),('race_class','race_class'),('distance_m','distance_m')]:
        if declaration.get(source) is not None:card[target]=declaration[source]


def fetch_board(day, key, *, country=None, clock=None, meter=None, command='MONTY_LIVE', observer=None, client=None):
    """One bounded live AU board plus independent discovery inventory.

    Missing/bad races are accounted for individually; no automatic provider or
    best-book fallback. A rolling board never proves national TAB completeness.
    """
    from datetime import timedelta
    from operations.market_integrity import MAX_AGE_SECONDS, timestamp
    from zoneinfo import ZoneInfo
    if country not in (None, 'AU'):raise ProviderError('PuntersEdge route supports Australian racing only')
    if command.strip().upper()=='C':raise ProviderError('C cannot acquire data')
    clock=clock or (lambda:datetime.now(timezone.utc))
    client=client or Client(key,budget=10,observer=observer)
    if meter is not None and client.usage is not meter:
        meter.extend(client.usage);client.usage=meter
    before=len(client.usage)
    account=client.get('/v1/usage',command=command)
    remaining=account.get('credits_remaining')
    if type(remaining) is not int or remaining<500+client.budget:
        raise ProviderError('PuntersEdge allowance unverified or operational reserve insufficient')
    inventory=[];inventory_error=None;declarations={};declaration_ids={};unavailable=[]
    try:
        acceptance=client.get('/v1/racing/acceptances',dict(date=day),command=command)
        if not isinstance(acceptance,dict) or acceptance.get('date')!=day or not isinstance(acceptance.get('meetings'),list):
            raise ProviderError('Unexpected dated acceptance contract')
        for meeting in acceptance['meetings']:
            if not meeting.get('races'):unavailable.append(meeting.get('venue'))
            for race in meeting.get('races',[]):
                key=(str(meeting.get('venue_id') or meeting['venue']).strip().casefold(),str(race['race_number']))
                if key in declarations:raise ProviderError('Duplicate dated acceptance race')
                declarations[key]=race
                if race.get('race_id'):
                    if race['race_id'] in declaration_ids:raise ProviderError('Duplicate dated race ID')
                    declaration_ids[race['race_id']]=key
                inventory.append(dict(race_id=race.get('race_id'),meeting=meeting['venue'],race=race['race_number']))
    except ProviderError:inventory_error='Dated acceptance discovery unavailable';inventory=[];declarations={};declaration_ids={}
    board=client.get('/v1/racing/next-to-go',dict(num_races=200,categories='horse',country='AU',include_unresolved='true'),command=command)
    if not isinstance(board,list):raise ProviderError('Unexpected PuntersEdge board')
    # Do not call a capped board complete; continue safe observed races explicitly.
    capped=len(board)>=200
    now=clock();cutoff=now-timedelta(seconds=MAX_AGE_SECONDS)
    meetings={};race_keys=set();observations=[];omissions=[];seen_ids=set()
    for source in board:
        if not isinstance(source,dict):
            omissions.append(dict(reason='Malformed board race'));continue
        identity=dict(race_id=source.get('race_id'),meeting=source.get('venue'),race=source.get('race_number'))
        if identity['race_id']:seen_ids.add(identity['race_id'])
        try:
            converted=canonical_race(source,day=day)['data'][0];card=converted['races'][0]
            declared_key=declaration_ids.get(source.get('race_id'),(str(source.get('venue_id') or source['venue']).strip().casefold(),str(source['race_number'])))
            if declared_key[1]!=str(source['race_number']):raise ProviderError('Price and acceptance race IDs disagree')
            declared=declarations.get(declared_key)
            if declared is not None:join_acceptances(card,declared)
            clocks=[timestamp(row['odds'][0].get('captured_at')) for row in card['runners'] if not row['is_scratched']]
            if max(clocks)>now:raise ProviderError('TAB poll observation future-dated')
            if min(clocks)<=cutoff:raise ProviderError('TAB poll observation older than five minutes')
            if timestamp(card['jump_time'])<=now:raise ProviderError('Scheduled jump reached')
        except (ProviderError,AttributeError,KeyError,TypeError,ValueError) as exc:
            omissions.append(dict(identity,reason=str(exc) if isinstance(exc,ProviderError) else 'Incomplete race or observation contract'))
            continue
        card['quote_observed_at']=min(clocks).isoformat()
        venue=converted['venue'];identity_key=(venue.casefold(),str(card['number']))
        if identity_key in race_keys:raise ProviderError('Duplicate race identity on PuntersEdge board')
        race_keys.add(identity_key)
        if venue not in meetings:meetings[venue]=dict(converted,races=[])
        meetings[venue]['races'].append(card);observations.extend(clocks)
    absent=[dict(r,reason='Discovered race absent from priced rolling board') for r in inventory if r['race_id'] not in seen_ids]
    payload=dict(success=True,data=list(meetings.values()),meta=dict(has_more=False,provider='PuntersEdge',
        board_scope='AU rolling board; discovery horizon24h; independent TAB national completeness unverified',
        board_races=len(board),eligible_races=len(race_keys),board_at_limit=capped,discovered_races=inventory,
        discovery_error=inventory_error,discovery_scope='Dated provider acceptances; not independent TAB schedule',acceptance_meetings_without_races=unavailable,omissions=omissions+absent,complete_national_coverage_verified=False,
        usage_summary=__import__('operations.data_acquisition',fromlist=['usage_summary']).usage_summary(client.usage[before:])))
    # Empty priced cards retain diagnostics; normalisation reports DATA BLOCKED.
    # Acquisition time is distinct from each race's original per-offer poll time.
    return payload,now
