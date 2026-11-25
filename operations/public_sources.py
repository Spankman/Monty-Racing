"""Bounded read-only public source capture and published-page parsing.

No private endpoints, authenticated sessions, challenge handling or TLS bypass.
Raw pages stay private. Published reports contain provenance and derived facts.
"""
from datetime import datetime,timezone
from decimal import Decimal
import hashlib,json,re,time,urllib.request,urllib.error
from urllib.parse import urlsplit
from pathlib import Path
from bs4 import BeautifulSoup

HOSTS={'www.tab.com.au':'TAB','www.sportsbet.com.au':'Sportsbet',
       'www.racingqueensland.com.au':'Racing Queensland',
       'racing.racingnsw.com.au':'Racing NSW'}


def capture(url,directory):
    parts=urlsplit(url)
    if parts.scheme!='https' or parts.hostname not in HOSTS or parts.username or parts.password or parts.port not in (None,443):
        raise ValueError('Unapproved public source URL')
    started=datetime.now(timezone.utc);t=time.monotonic()
    result=dict(source=HOSTS[parts.hostname],source_url=url,started_at=started.isoformat(),status='UNAVAILABLE')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args):return None
    request=urllib.request.Request(url,headers={'User-Agent':'Monty-public-verification/1.0 (read-only)','Accept':'text/html,application/pdf'})
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=20) as response:
            body=response.read(6_000_001)
            if len(body)>6_000_000:raise ValueError('Public page exceeds limit')
            result.update(http_status=response.status,response_date=response.headers.get('Date'),cache_age=response.headers.get('Age'))
        if any(x in body.lower() for x in [b'verify you are human',b'cf-chl-',b'checking your browser']):
            result['status']='ACCESS_CHALLENGE'
            return result,None
        digest=hashlib.sha256(body).hexdigest();directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        path=directory/(digest+'.source');path.write_bytes(body)
        result.update(status='CAPTURED',sha256=digest,observed_at=datetime.now(timezone.utc).isoformat())
        return result,body
    except urllib.error.HTTPError as exc:
        result.update(http_status=exc.code,status='ACCESS_DENIED' if exc.code in (401,403) else 'HTTP_ERROR')
        return result,None
    except Exception as exc:
        result.update(error_type=type(exc).__name__)
        return result,None
    finally:
        result['elapsed_seconds']=round(time.monotonic()-t,6)


def sportsbet(body,url,day,meeting,race):
    """Parse public SSR state, selecting only the displayed primary WIN market."""
    soup=BeautifulSoup(body,'html.parser')
    scripts=[s.get_text() for s in soup.find_all('script') if 'window.__PRELOADED_STATE__' in s.get_text()]
    if len(scripts)!=1:raise ValueError('Sportsbet published state unavailable or ambiguous')
    text=scripts[0].split('window.__PRELOADED_STATE__',1)[1].split('=',1)[1].lstrip()
    state,_=json.JSONDecoder().raw_decode(text);book=state['entities']['sportsbook']
    match=re.fullmatch(r'https://www\.sportsbet\.com\.au/horse-racing/australia-nz/[^/]+/race-(\d+)-(\d+)',url)
    if not match or int(match[1])!=int(race):raise ValueError('Sportsbet race URL mismatch')
    event=book['events'][match[2]]
    venue=book['competitions'][str(event['competitionId'])]['name']
    jump=datetime.fromtimestamp(event['startTime']['milliseconds']/1000,timezone.utc)
    from zoneinfo import ZoneInfo
    if venue.casefold()!=meeting.casefold() or event['raceNumber']!=int(race) or jump.astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat()!=day:
        raise ValueError('Sportsbet race date/venue/number mismatch')
    primary=book['markets'][str(event['primaryMarketId'])]
    if primary['name']!='Win or Place' or not primary.get('active') or not primary.get('displayed') or event['status']!='ACTIVE' or event.get('stale') or event.get('removed'):
        raise ValueError('Sportsbet primary market not available')
    rows=[]
    for ident in primary['outcomeIds']:
        row=book['outcomes'][str(ident)]
        if row['marketId']!=primary['id'] or type(row.get('active')) is not bool:raise ValueError('Sportsbet field/market mismatch')
        price=None
        if row['active']:
            quote=row['winPrice'];price=Decimal(quote['num'])/Decimal(quote['den'])+1
            if not price.is_finite() or price<=1:raise ValueError('Sportsbet invalid win price')
        rows.append(dict(number=str(row['runnerNumber']),horse=row['name'],scratched=not row['active'],
            fixed_win=str(price) if price else None,bookmaker='Sportsbet',country_of_origin=row.get('runnerCountry'),
            source_runner_id=str(row['id']),barrier=row.get('drawNumber'),jockey=row.get('jockey'),trainer=row.get('trainer')))
    if len(rows)!=len({r['number'] for r in rows}):raise ValueError('Sportsbet duplicate saddlecloth')
    condition=re.sub(r'\((\d+)\)',r'\1',event['trackStatus']).strip()
    return dict(date=day,meeting=meeting,race=str(race),country='AU',status='open',distance_m=int(event['distance']),
                scheduled_start=jump.isoformat(),condition=condition,market='fixed_win',bookmaker='Sportsbet',runners=rows)


def rq_facts(body,day,meeting,race):
    """Read primary authority metadata; absence of a field is never verification."""
    text=BeautifulSoup(body,'html.parser').get_text(' ',strip=True)
    if meeting.casefold() not in text.casefold():raise ValueError('Authority meeting missing')
    from zoneinfo import ZoneInfo
    import calendar
    date=datetime.fromisoformat(day)
    if not re.search(r'\b'+str(date.day)+r'\s+'+calendar.month_name[date.month][:3],text,re.I):raise ValueError('Authority date missing')
    distance=re.search(r'\b(\d{3,4})m\b',text)
    going=re.search(r'\b(Firm [12]|Good [34]|Soft [5-7]|Heavy (?:[89]|10)|Synthetic)\b',text)
    jump=re.search(r'\b(\d{1,2})\.(\d{2})(am|pm)\b',text,re.I)
    fields=dict(date=day,meeting=meeting,race=str(race),country='AU',distance_m=int(distance[1]) if distance else None,
                condition=going[0] if going else None,surface='turf' if re.search(r'\bTurf\b',text) else None,
                field_verified=False,emergency_status_verified=False)
    if jump:
        hour=int(jump[1])%12+(12 if jump[3].lower()=='pm' else 0)
        fields['scheduled_start']=datetime(date.year,date.month,date.day,hour,int(jump[2]),tzinfo=ZoneInfo('Australia/Brisbane')).astimezone(timezone.utc).isoformat()
    return fields
