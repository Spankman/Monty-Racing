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
    def __init__(self,key=None,*,budget=40,opener=None,sleeper=time.sleep):
        self._key=key or os.getenv('PUNTERSEDGE_API_KEY','')
        if not self._key:raise ProviderError('PuntersEdge credential unavailable')
        self.open=opener or build_opener(NoRedirect()).open
        self.sleep=sleeper;self.budget=budget;self.reserved=0;self.usage=[];self.responses=[]

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


def fetch_board(day, key, *, country=None, clock=None):
    """Build one TAB fixed-win snapshot from the bounded AU rolling board."""
    from datetime import timedelta
    from operations.market_integrity import MAX_AGE_SECONDS, timestamp

    if country not in (None, 'AU'):
        raise ProviderError('PuntersEdge route supports Australian racing only')
    clock = clock or (lambda: datetime.now(timezone.utc))
    client = Client(key, budget=8)
    board = client.get('/v1/racing/next-to-go', {
        'num_races': 200, 'categories': 'horse', 'country': 'AU',
    }, command='MONTY_LIVE')
    if not isinstance(board, list) or len(board) >= 200:
        raise ProviderError('Unexpected or potentially truncated PuntersEdge board')
    now = clock()
    cutoff = now - timedelta(seconds=MAX_AGE_SECONDS)
    meetings = {}
    race_keys = set()
    observations = []
    for race in board:
        try:
            converted = canonical_race(race, day=day)['data'][0]
            card = converted['races'][0]
            clocks = [timestamp(row['odds'][0].get('captured_at'))
                      for row in card['runners'] if not row['is_scratched']]
            if not all(cutoff < observed <= now for observed in clocks):
                continue
            if timestamp(card['jump_time']) <= now + timedelta(minutes=1):
                continue
        except (ProviderError, AttributeError, KeyError, TypeError, ValueError):
            continue
        venue = converted['venue']
        identity = (venue.casefold(), str(card['number']))
        if identity in race_keys:
            raise ProviderError('Duplicate race identity on PuntersEdge board')
        race_keys.add(identity)
        if venue not in meetings:
            meetings[venue] = dict(converted, races=[])
        meetings[venue]['races'].append(card)
        observations.extend(clocks)
    if not observations:
        raise ProviderError('No complete PuntersEdge TAB fields with fresh observations')
    payload = dict(success=True, data=list(meetings.values()), meta=dict(
        has_more=False, provider='PuntersEdge', board_scope='AU rolling board',
        board_races=len(board), eligible_races=len(race_keys),
    ))
    return payload, min(observations)
