"""Fixed-host, deadline-bounded Krok acquisition. No model or tipster endpoints."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ProviderFailure(Exception):
    def __init__(self, code, retry_after=0):
        super().__init__(code)
        self.code=code
        self.retry_after=retry_after


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args):return None


def retry_seconds(value):
    if not value:return 0
    try:return max(0,int(value))
    except ValueError:
        try:return max(0,int((parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds()))
        except (ValueError,TypeError,OverflowError):return 0


class Provider:
    def __init__(self,key,*,budget=20,opener=None,clock=time.monotonic,sleep=time.sleep):
        self.key=key;self.budget=budget;self.opener=opener or build_opener(NoRedirect())
        self.clock=clock;self.sleep=sleep;self.cooldown_until=0

    def fetch(self,day):
        if not self.key:raise ProviderFailure('PROVIDER_CREDENTIALS_MISSING')
        if self.clock()<self.cooldown_until:
            raise ProviderFailure('PROVIDER_RATE_LIMITED',int(self.cooldown_until-self.clock())+1)
        end=self.clock()+self.budget;params={'date':day,'race_type':'T','limit':50};seen=set();meetings=[];total=None
        for _ in range(20):
            query=urlencode(params)
            if query in seen:raise ProviderFailure('PROVIDER_PAGINATION_LOOP')
            seen.add(query)
            page=None
            for attempt in range(3):
                remaining=end-self.clock()
                if remaining<=0:raise ProviderFailure('PROVIDER_DEADLINE')
                req=Request('https://krokodds.com.au/api/v1/racing/meetings?'+query,
                            headers={'X-API-Key':self.key,'Accept':'application/json'})
                try:
                    with self.opener.open(req,timeout=min(5,remaining)) as response:
                        raw=response.read(20_000_001)
                    if self.clock()>end:raise ProviderFailure('PROVIDER_DEADLINE')
                    if len(raw)>20_000_000:raise ProviderFailure('PROVIDER_RESPONSE_TOO_LARGE')
                    page=json.loads(raw)
                    break
                except HTTPError as exc:
                    delay=retry_seconds(exc.headers.get('Retry-After'))
                    if exc.code==429:
                        # Honour the full server cooldown; do not shorten it to fit our deadline.
                        delay=max(1,delay);self.cooldown_until=self.clock()+delay
                    if exc.code not in (429,500,502,503,504):raise ProviderFailure('PROVIDER_HTTP_'+str(exc.code)) from None
                    if attempt==2 or delay>=end-self.clock():
                        raise ProviderFailure('PROVIDER_RATE_LIMITED' if exc.code==429 else 'PROVIDER_UNAVAILABLE',delay) from None
                    self.sleep(max(delay,.25*2**attempt))
                except (URLError,TimeoutError,OSError):
                    if attempt==2:raise ProviderFailure('PROVIDER_NETWORK_UNAVAILABLE') from None
                    self.sleep(min(.25*2**attempt,max(0,end-self.clock())))
                except (ValueError,UnicodeError):raise ProviderFailure('PROVIDER_INVALID_JSON') from None
            if not isinstance(page,dict) or page.get('success') is not True or not isinstance(page.get('data'),list):
                raise ProviderFailure('PROVIDER_INVALID_ENVELOPE')
            meta=page.get('meta')
            if not isinstance(meta,dict):raise ProviderFailure('PROVIDER_INVALID_METADATA')
            declared=meta.get('total')
            if type(declared) is not int or declared<0:raise ProviderFailure('PROVIDER_TOTAL_UNKNOWN')
            if total is not None and total!=declared:raise ProviderFailure('PROVIDER_TOTAL_CHANGED')
            total=declared;meetings.extend(page['data'])
            if len(meetings)>5000:raise ProviderFailure('PROVIDER_CARD_TOO_LARGE')
            cursor=meta.get('next_cursor');nxt=meta.get('next_page',meta.get('next'))
            if cursor not in (None,'',False):params.pop('page',None);params['cursor']=str(cursor)
            elif nxt not in (None,'',False):
                if type(nxt) is bool or not str(nxt).isdigit():raise ProviderFailure('PROVIDER_UNSAFE_PAGE')
                params.pop('cursor',None);params['page']=str(nxt)
            else:
                if meta.get('has_more') is not False or len(meetings)!=total:
                    raise ProviderFailure('PROVIDER_INCOMPLETE_CARD')
                identities=[(m.get('date'),m.get('country'),m.get('venue'),m.get('type')) for m in meetings if isinstance(m,dict)]
                if len(identities)!=len(meetings) or len(set(identities))!=len(identities):
                    raise ProviderFailure('PROVIDER_AMBIGUOUS_MEETINGS')
                # Redact a provider echo without logging the body or credential.
                def clean(x):
                    if isinstance(x,str):return x.replace(self.key,'[REDACTED]')
                    if isinstance(x,list):return [clean(v) for v in x]
                    if isinstance(x,dict):return {clean(k):clean(v) for k,v in x.items()}
                    return x
                return clean({'success':True,'data':meetings,'meta':{'has_more':False}})
        raise ProviderFailure('PROVIDER_PAGE_LIMIT')
