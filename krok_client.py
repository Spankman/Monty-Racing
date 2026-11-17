"""Bounded Krok JSON client with useful, credential-free HTTP diagnostics."""
import json
import urllib.error
import urllib.parse
import urllib.request

class ProviderError(ValueError):
    def __init__(self, status, retry_after=None):
        self.status=status;self.retry_after=retry_after
        super().__init__('Krok HTTP '+str(status))

def get(path, params, key):
    if not key:raise ValueError('KROK_API_KEY is absent')
    if not path.startswith('/api/v1/racing/') or '?' in path:
        raise ValueError('Unsupported provider route')
    url='https://krokodds.com.au'+path+'?'+urllib.parse.urlencode(params)
    request=urllib.request.Request(url,headers={'X-API-Key':key,'Accept':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=35) as response:
            raw=response.read(20_000_001)
    except urllib.error.HTTPError as exc:
        # No automatic retries: respect rate limits and paid-tier gates.
        retry=exc.headers.get('Retry-After')
        raise ProviderError(exc.code, retry if retry and retry.isdigit() else None) from None
    if len(raw)>20_000_000:raise ValueError('Response too large')
    payload=json.loads(raw)
    if not isinstance(payload,dict) or payload.get('success') is not True:
        raise ValueError('Unexpected provider response')
    return payload
