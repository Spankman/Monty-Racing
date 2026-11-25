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
        url=BASE+path+('?' + urlencode(params) if params else '')
        for attempt in range(2):
            if self.reserved+COSTS[path]>self.budget:raise ProviderError('Staging request budget reached')
            self.reserved+=COSTS[path]
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
