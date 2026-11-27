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

def race_key(venue, race_number):
    name = venue.get('venue_id') or venue.get('venue')
    if not isinstance(name, str) or not name.strip() or not str(race_number).isdigit():
        raise ValueError('Invalid venue or race number')
    return name.strip().casefold(), str(int(race_number))


def dated_acceptances(client, day, command):
    """Capture a same-provider declaration inventory without claiming verification."""
    payload = client.get('/v1/racing/acceptances', {'date': day}, command=command)
    if (not isinstance(payload, dict) or payload.get('date') != day
            or not isinstance(payload.get('meetings'), list)):
        raise ProviderError('Unexpected dated acceptances contract')
    by_key, by_id = {}, {}
    for meeting in payload['meetings']:
        for race in meeting.get('races', []):
            key = race_key(meeting, race['race_number'])
            race_id = race.get('race_id')
            if key in by_key or (race_id and race_id in by_id):
                raise ProviderError('Ambiguous dated acceptance race identity')
            by_key[key] = (meeting['venue'], race)
            if race_id:
                by_id[race_id] = key
    return by_key, by_id


def reconcile_field(card, declaration):
    if declaration.get('runner_set_status') == 'gap_detected':
        raise ProviderError('Dated acceptance reports a runner gap')
    declared = {}
    for row in declaration.get('runners', []):
        number = str(row['number'])
        if number in declared:
            raise ProviderError('Duplicate saddlecloth in dated acceptance')
        declared[number] = row
    observed = {str(row['number']): row for row in card['runners']}
    for number, row in observed.items():
        prior = declared.get(number)
        if prior and (' '.join(str(prior.get('runner_name') or '').casefold().split())
                      != ' '.join(row['name'].casefold().split())):
            raise ProviderError('Price board and acceptance runner identities disagree')
        if prior and prior.get('scratched') is True and not row['is_scratched']:
            raise ProviderError('Live TAB quote conflicts with an acceptance scratching')
    for number, row in declared.items():
        offered = observed.get(number)
        if (row.get('emergency') is False and row.get('scratched') is False
                and not offered):
            raise ProviderError('Declared runner absent from TAB field')
    if not card.get('race_class') and declaration.get('race_class'):
        card['race_class'] = declaration['race_class']


def board_quote_clocks(source, card, now, cutoff, clock_counts):
    from operations.market_integrity import timestamp

    clocks = [timestamp(row['odds'][0]['captured_at'])
              for row in card['runners'] if not row['is_scratched']
              and row['odds'][0].get('captured_at')]
    if len(clocks) != sum(not row['is_scratched'] for row in card['runners']):
        raise ProviderError('TAB poll observation unavailable')
    tab = [quote for row in source['runners'] for quote in row.get('bookmakers', [])
           if quote.get('key') == 'tab']
    tiers = {quote.get('refresh_tier') for quote in tab}
    tier = next(iter(tiers)) if len(tiers) == 1 else None
    tier = tier if tier in ('card', 'live') else 'mixed-or-unreported'
    cache = 'cached' if source.get('cached') is True else 'cache-unreported-or-fresh'
    if max(clocks) > now:
        state = 'future'
    elif min(clocks) <= cutoff:
        state = 'expired'
    else:
        state = 'fresh'
    clock_counts[f'{tier}/{cache}/{state}'] += 1
    if state != 'fresh':
        raise ProviderError(f'TAB poll observation {state}')
    return clocks



def fetch_board(day, key, *, country=None, clock=None, meter=None, command='MONTY_LIVE', observer=None, client=None):
    """One bounded live AU board plus independent discovery inventory.

    Missing/bad races are accounted for individually; no automatic provider or
    best-book fallback. A rolling board never proves national TAB completeness.
    """
    from collections import Counter
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
    inventory=[];inventory_error=None
    try:
        events=client.get('/v1/racing/events',dict(hours_ahead=24,categories='horse',country='AU',include_unresolved='true'),command=command)
        if not isinstance(events,list):raise ProviderError('Unexpected discovery contract')
        for event in events:
            try:
                if (event.get('country')=='AU' and event.get('category')=='horse'
                    and timestamp(event['start_time']).astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat()==day):
                    inventory.append(dict(race_id=event.get('race_id'),meeting=event.get('venue'),race=event.get('race_number')))
            except (ValueError,TypeError,KeyError,AttributeError):inventory_error='Incomplete discovery identities'
    except ProviderError:inventory_error='Independent provider discovery unavailable'
    acceptance_error = None
    try:
        declarations, acceptance_ids = dated_acceptances(client, day, command)
    except (ProviderError, ValueError, TypeError, KeyError, AttributeError):
        declarations, acceptance_ids = {}, {}
        acceptance_error = 'Dated acceptance inventory unavailable'
    board=client.get('/v1/racing/next-to-go',dict(num_races=200,categories='horse',country='AU',include_unresolved='true'),command=command)
    if not isinstance(board,list):raise ProviderError('Unexpected PuntersEdge board')
    # Do not call a capped board complete; continue safe observed races explicitly.
    capped=len(board)>=200
    now=clock();cutoff=now-timedelta(seconds=MAX_AGE_SECONDS)
    meetings, priced, duplicates, omissions = {}, {}, set(), []
    seen_ids, seen_keys = set(), set()
    clock_counts = Counter()
    for source in board:
        if not isinstance(source, dict):
            omissions.append(dict(reason='Malformed board race'))
            continue
        identity = dict(race_id=source.get('race_id'), meeting=source.get('venue'),
                        race=source.get('race_number'))
        try:
            if (source.get('country') != 'AU' or source.get('category') != 'horse'
                    or timestamp(source['start_time']).astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat() != day):
                raise ProviderError('Outside the current AU thoroughbred card')
            key = acceptance_ids.get(identity['race_id']) or race_key(source, source['race_number'])
            if identity['race_id']:
                seen_ids.add(identity['race_id'])
            repeated = key in seen_keys
            seen_keys.add(key)
            if repeated:
                priced.pop(key, None)
                duplicates.add(key)
                raise ProviderError('Duplicate race identity on price board')
            converted = canonical_race(source, day=day)['data'][0]
            card = converted['races'][0]
            if key in declarations:
                reconcile_field(card, declarations[key][1])
            clocks = board_quote_clocks(source, card, now, cutoff, clock_counts)
            if timestamp(card['jump_time']) <= now + timedelta(minutes=1):
                raise ProviderError('Race inside pre-jump freeze')
            card['price_observed_at'] = min(clocks).isoformat()
            priced[key] = converted, card
        except (ProviderError, AttributeError, KeyError, TypeError, ValueError) as exc:
            if identity['race_id'] and source.get('country') == 'AU':
                seen_ids.add(identity['race_id'])
            omissions.append(dict(identity, reason=str(exc) if isinstance(exc, ProviderError)
                                  else 'Incomplete race or observation contract'))
    for key, (converted, card) in priced.items():
        venue = converted['venue']
        meetings.setdefault(venue, dict(converted, races=[]))['races'].append(card)

    omitted_ids = set()
    for key, (meeting, race) in declarations.items():
        race_id = race.get('race_id')
        if key not in seen_keys and race_id not in seen_ids:
            omissions.append(dict(race_id=race_id, meeting=meeting, race=race['race_number'],
                                  reason='Dated acceptance absent from priced rolling board'))
            if race_id:
                omitted_ids.add(race_id)
    absent = [dict(race, reason='Discovered event absent from priced rolling board')
              for race in inventory if race['race_id'] and race['race_id'] not in seen_ids | omitted_ids]
    payload=dict(success=True,data=list(meetings.values()),meta=dict(has_more=False,provider='PuntersEdge',
        board_scope='AU rolling board; discovery horizon24h; independent TAB national completeness unverified',
        board_races=len(board),eligible_races=len(priced),board_at_limit=capped,discovered_races=inventory,
        dated_meeting_count=len({key[0] for key in declarations}), dated_race_count=len(declarations),
        dated_priced_count=len(priced.keys() & declarations.keys()), dated_acceptances_error=acceptance_error,
        tab_clock_counts=dict(clock_counts), duplicate_board_races=len(duplicates),
        discovery_error=inventory_error,omissions=omissions+absent,complete_national_coverage_verified=False,
        usage_summary=__import__('operations.data_acquisition',fromlist=['usage_summary']).usage_summary(client.usage[before:])))
    # Empty priced cards retain diagnostics; normalisation reports DATA BLOCKED.
    return payload,now
