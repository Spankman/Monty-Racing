"""Check provider connectivity and input shape. No model loading or predictions."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
from zoneinfo import ZoneInfo
from krok_adapter import fetch, normalize

def check(date, output):
    try:
        dt.date.fromisoformat(date)
    except ValueError as exc:
        raise ValueError('invalid_date') from exc
    key=os.environ.get('KROK_API_KEY','')
    if not key:raise ValueError('KROK_API_KEY is absent; no live request attempted.')
    try:
        payload=fetch(date,key)
    except ValueError as exc:
        raise ValueError('provider_payload_or_size') from exc
    try:
        _,audit=normalize(payload,date)
    except (ValueError,KeyError,TypeError) as exc:
        raise ValueError('provider_normalization') from exc
    report={'requested_date':date,'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source':'Krok Odds API — https://krokodds.com.au',
            'live_request_succeeded':True,'accepted_races':audit['races_accepted'],
            'accepted_runners':audit['runners_accepted'],'price_sources':audit['price_sources'],
            'tab_verified':False,'complete_au_nz_coverage_verified':False,
            'model_loaded':False,'predictions_generated':False}
    target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')
    return report

def blocked_report(output,date,category):
    report={'requested_date':date,
            'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'status':'BLOCKED','failure_category':category,
            'tab_verified':False,'model_loaded':False,'predictions_generated':False}
    target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--date',default=dt.datetime.now(ZoneInfo('Australia/Brisbane')).date().isoformat())
    p.add_argument('--output',default='connection_report.json');a=p.parse_args()
    try:
        report=check(a.date,a.output)
    except ValueError as exc:
        # Fixed diagnostic; never print provider bodies, request objects or credentials.
        categories={'invalid_date':'Invalid racing date',
                    'provider_payload_or_size':'Provider response JSON or size invalid',
                    'provider_normalization':'Provider response failed racing-field normalization'}
        msg='Missing KROK_API_KEY' if not os.environ.get('KROK_API_KEY') else categories.get(str(exc),'Provider input validation failed')
        blocked_report(a.output,a.date,msg)
        print('BLOCKED: '+msg);return 2
    except urllib.error.HTTPError as exc:
        blocked_report(a.output,a.date,'provider_http_'+str(exc.code))
        print('BLOCKED: provider HTTP status '+str(exc.code));return 2
    except Exception as exc:
        blocked_report(a.output,a.date,'unexpected_'+type(exc).__name__)
        print('BLOCKED: '+type(exc).__name__);return 2
    print(json.dumps(report));return 0

if __name__=='__main__':raise SystemExit(main())
