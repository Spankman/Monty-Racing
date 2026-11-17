"""Three-request bounded diagnostic; logs schema counts, never runner records."""
import datetime as dt
import json
import os
from collections import Counter
from zoneinfo import ZoneInfo
from krok_client import get,ProviderError


def main():
    key=os.environ.get('KROK_API_KEY')
    today=dt.datetime.now(ZoneInfo('Australia/Brisbane')).date()
    routes=[('/api/v1/racing/field-form',{'race_id':str(today)+'_scone_T_7','form_limit':10}),
            ('/api/v1/racing/results/'+str(today-dt.timedelta(days=1)),{}),
            ('/api/v1/racing/results/'+str(today-dt.timedelta(days=365)),{})]
    reports=[]
    for path,params in routes:
        item={'path':path}
        try:
            payload=get(path,params,key);data=payload.get('data')
            races=data if isinstance(data,list) else [data] if isinstance(data,dict) else []
            runners=[r for race in races for r in race.get('runners',[])]
            fields=Counter(k for r in runners for k,v in r.items() if v is not None)
            item.update(http_status=200,races=len(races),runners=len(runners),fields=dict(fields),
                        meta={k:payload.get('meta',{}).get(k) for k in ('tier','limit','count','truncated','date','rate_limit')})
        except ProviderError as exc:
            item.update(http_status=exc.status,retry_after=exc.retry_after)
            reports.append(item)
            if exc.status in (401,402,403,429):break
            continue
        except Exception as exc:
            item['error_type']=type(exc).__name__
        reports.append(item)
    print(json.dumps({'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'requests':reports,'predictions_generated':False}))

if __name__=='__main__':main()
