"""Staged read-only PuntersEdge acquisition. Never an automatic model fallback.

Raw responses are personal-use data and must remain private. No provider picks,
account mutation, wager/betslip routes, signup or billing requests are supported.
"""
from datetime import datetime,timezone
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode, urlsplit
import hashlib,json,os,time
def record_usage(rows, url, status, headers, command, started):
    safe = {}
    for key in ('X-Credits-Cost', 'X-Credits-Remaining', 'X-Credits-Limit',
                'X-RateLimit-Limit', 'X-RateLimit-Remaining'):
        value = headers.get(key)
        if isinstance(value, str) and value.isascii() and value.isdigit():
            safe[key.lower()] = int(value)
    rows.append(dict(endpoint=urlsplit(url).path, status=status, command=command,
                     attempted_at=datetime.now(timezone.utc).isoformat(),
                     elapsed_seconds=round(time.monotonic() - started, 6),
                     **safe, credit_cost_known='x-credits-cost' in safe))

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
    from monty_operations import timestamp
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


def venue_key(row):
    return (row.get('venue_id') or row['venue']).strip().casefold()


def join_acceptances(card, declaration):
    """Use same-source declaration facts after exact race and runner matches."""
    if declaration.get('runner_set_status') == 'gap_detected':
        raise ProviderError('PuntersEdge acceptances report a field gap')
    runners = {str(row['number']): row for row in declaration.get('runners', [])}
    offered = {str(row['number']): row for row in card['runners'] if not row['is_scratched']}
    for number, declared in runners.items():
        name = declared.get('runner_name')
        if declared.get('scratched') is True and number in offered:
            raise ProviderError('Active TAB quote conflicts with declared scratching')
        if (declared.get('scratched') is False and declared.get('emergency') is False
                and number not in offered):
            raise ProviderError('Declared active runner missing from TAB price board')
        if number not in offered:
            continue
        row = offered[number]
        if not isinstance(name, str) or name.casefold().strip() != row['name'].casefold().strip():
            raise ProviderError('Price and acceptance runner identities disagree')
        for source, target in (('age', 'age'), ('claim_kg', 'claim_kg')):
            if declared.get(source) is not None:
                row[target] = declared[source]
    for key in ('race_name', 'race_class', 'distance_m'):
        if declaration.get(key) is not None:
            card['name' if key == 'race_name' else key] = declaration[key]


def fetch_board(day, key, *, country=None, meeting=None, race_number=None, clock=None):
    """Reconcile a dated discovery window with the rolling TAB price board."""
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    from monty_operations import MAX_AGE_SECONDS, timestamp

    if country not in (None, 'AU'):
        raise ProviderError('This PuntersEdge route is configured for Australia only')
    clock = clock or (lambda: datetime.now(timezone.utc))
    client = Client(key, budget=12)
    params = dict(categories='horse', country='AU', include_unresolved='true')
    discovery = 'ACCEPTANCES'
    try:
        card_params = dict(date=day)
        if meeting:
            card_params['venue'] = meeting
        acceptances = client.get('/v1/racing/acceptances', card_params, command='MONTY_LIVE')
        if (not isinstance(acceptances, dict) or acceptances.get('date') != day
                or not isinstance(acceptances.get('meetings'), list)):
            raise ProviderError('Unexpected PuntersEdge acceptances response')
    except ProviderError:
        acceptances, discovery = {}, 'UNAVAILABLE'
    # The board's venue parameter requires an exact market spelling. A
    # bounded AU board avoids venue filtering mistakes for single-race aliases.
    board_params = dict(params, num_races=200)
    board = client.get('/v1/racing/next-to-go', board_params, command='MONTY_LIVE')
    if not isinstance(board, list):
        raise ProviderError('Unexpected PuntersEdge price board')
    now = clock()
    cutoff = now - timedelta(seconds=MAX_AGE_SECONDS)
    zone = ZoneInfo('Australia/Brisbane')
    discovered, priced, excluded = {}, {}, {}

    def identity(row):
        try:
            if (row.get('country') != 'AU' or row.get('category') != 'horse'
                    or timestamp(row['start_time']).astimezone(zone).date().isoformat() != day):
                return None
            return venue_key(row), str(row['race_number'])
        except (AttributeError, KeyError, TypeError, ValueError):
            return None

    declarations = {}
    unavailable_meetings = []
    ids = {}
    for venue in acceptances.get('meetings', []):
        name = venue['venue']
        races = venue.get('races', [])
        if not races:
            unavailable_meetings.append(name)
        for race in races:
            key = venue_key(venue), str(race['race_number'])
            if meeting and key[1] != str(race_number):
                continue
            discovered[key] = name
            declarations[key] = race
            if race.get('race_id'):
                ids[race['race_id']] = key

    target_keys = set(discovered)
    if meeting:
        target_keys.add((meeting.casefold(), str(race_number)))

    for race in board:
        key = identity(race)
        if key:
            key = ids.get(race.get('race_id'), key)
        if not key or meeting and key not in target_keys and (
                race.get('venue', '').casefold() != meeting.casefold() or key[1] != str(race_number)):
            continue
        if key in priced or key in excluded:
            priced.pop(key, None)
            excluded[key] = 'duplicate race on price board'
            continue
        try:
            if timestamp(race['start_time']) <= now + timedelta(minutes=1):
                excluded[key] = 'race inside pre-jump freeze or already due'
                continue
            converted = canonical_race(race, day=day)['data'][0]
            card = converted['races'][0]
            if key in declarations:
                join_acceptances(card, declarations[key])
                if meeting:
                    # Keep the exact requested spelling for the shared scope check.
                    converted['venue'] = meeting
            elif meeting:
                converted['venue'] = meeting
            clocks = [timestamp(row['odds'][0].get('captured_at'))
                      for row in card['runners'] if not row['is_scratched']]
            if not all(cutoff < observed <= now for observed in clocks):
                excluded[key] = 'TAB poll observation stale or future dated'
                continue
        except ProviderError as exc:
            excluded[key] = str(exc)  # Messages are fixed in canonical_race.
            continue
        except (AttributeError, KeyError, TypeError, ValueError):
            excluded[key] = 'invalid race data or missing TAB poll timestamp'
            continue
        priced[key] = converted, card, min(clocks)

    meetings = {}
    for converted, card, observed in priced.values():
        venue = converted['venue']
        card['quote_observed_at'] = observed.isoformat()
        meetings.setdefault(venue, dict(converted, races=[]))['races'].append(card)
    for key in discovered.keys() - priced.keys() - excluded.keys():
        excluded[key] = 'discovered but absent from rolling price board'
    if meeting and not priced and not excluded:
        excluded[(meeting.casefold(), str(race_number))] = 'requested race absent from discovery and price board'
    from collections import Counter

    cost = [row.get('x-credits-cost') for row in client.usage]
    meta = dict(has_more=False, provider='PuntersEdge', board_scope='AU rolling board',
                discovery_status=discovery, discovered_races=len(discovered),
                discovered_meetings=len({key[0] for key in discovered}),
                board_races=len(board), board_at_limit=len(board) >= board_params['num_races'],
                eligible_races=len(priced),
                provider_reported_meetings=acceptances.get('meeting_count'),
                provider_reported_races=acceptances.get('race_count'),
                unresolved_board_races=sum(isinstance(race, dict) and race.get('country') is None for race in board),
                acceptance_meetings_without_races=len(unavailable_meetings),
                acquisition_reason_counts=dict(Counter(excluded.values())),
                observed_credits_used=sum(cost) if cost and all(value is not None for value in cost) else None,
                acquisition_skips=[f'{discovered.get(key, key[0])} R{key[1]}: {reason}'
                                   for key, reason in sorted(excluded.items())] +
                                  [f'{name}: acceptance races unavailable' for name in unavailable_meetings])
    return dict(success=True, data=list(meetings.values()), meta=meta), now
