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
    dt.date.fromisoformat(date)
    key=os.environ.get('KROK_API_KEY','')
    if not key:raise ValueError('KROK_API_KEY is absent; no live request attempted.')
    payload=fetch(date,key)
    _,audit=normalize(payload,date)
    report={'requested_date':date,'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source':'Krok Odds API — https://krokodds.com.au',
            'live_request_succeeded':True,'accepted_races':audit['races_accepted'],
            'accepted_runners':audit['runners_accepted'],'price_sources':audit['price_sources'],
            'tab_verified':False,'complete_au_nz_coverage_verified':False,
            'model_loaded':False,'predictions_generated':False}
    target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--date',default=dt.datetime.now(ZoneInfo('Australia/Brisbane')).date().isoformat())
    p.add_argument('--output',default='connection_report.json');a=p.parse_args()
    try:
        report=check(a.date,a.output)
    except ValueError as exc:
        # Fixed diagnostic; never print provider bodies, request objects or credentials.
        msg='Missing KROK_API_KEY' if not os.environ.get('KROK_API_KEY') else 'Date or provider input did not pass validation'
        print('BLOCKED: '+msg);return 2
    except urllib.error.HTTPError as exc:
        print('BLOCKED: provider HTTP status '+str(exc.code));return 2
    except Exception as exc:
        print('BLOCKED: '+type(exc).__name__);return 2
    print(json.dumps(report));return 0

if __name__=='__main__':raise SystemExit(main())
