"""Count-only audit of Krok's documented field-form endpoint. Never scores."""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from zoneinfo import ZoneInfo
from krok_adapter import fetch


def probe(date):
    key = os.environ.get('KROK_API_KEY')
    if not key:
        raise ValueError('KROK_API_KEY is absent')
    board = fetch(date, key)
    if board.get('success') is not True:
        raise ValueError('Provider did not return success')
    reports = []
    for meeting in board.get('data', []):
        if meeting.get('country') not in ('AU', 'NZ') or meeting.get('type') not in ('T', 'R'):
            continue
        for race in meeting.get('races', []):
            race_id = race.get('race_key_v2') or race.get('race_key') or race.get('id')
            if not race_id or str(race.get('status')).lower() in ('closed','final','resulted','abandoned'):
                continue
            query = urllib.parse.urlencode({'race_id':race_id, 'form_limit':10})
            request = urllib.request.Request('https://krokodds.com.au/api/v1/racing/field-form?'+query,
                      headers={'X-API-Key':key,'Accept':'application/json'})
            report = {'meeting':meeting.get('venue'), 'race':race.get('number')}
            try:
                with urllib.request.urlopen(request, timeout=35) as response:
                    raw=response.read(20_000_001)
                if len(raw)>20_000_000:
                    raise ValueError('Response exceeds limit')
                payload=json.loads(raw)
                if payload.get('success') is not True:
                    raise ValueError('Provider did not return success')
                runners=payload.get('data',{}).get('runners',[])
                fields=Counter(); form_fields=Counter(); histories=0; quotes=0
                for runner in runners:
                    for name,value in runner.items():
                        if value is not None and value != [] and value != {}:
                            fields[name]+=1
                    for row in runner.get('recent_form') or []:
                        histories+=1
                        for name,value in row.items():
                            if value is not None:
                                form_fields[name]+=1
                    quotes+=sum(bool(q.get('capturedAt')) for q in runner.get('odds') or [])
                report.update(runners=len(runners), runner_field_counts=dict(fields),
                              history_rows=histories, history_field_counts=dict(form_fields),
                              timestamped_quotes=quotes)
            except Exception as exc:
                # Do not log credential-bearing request objects or provider response text.
                report['error_type']=type(exc).__name__
            reports.append(report)
    return {'date':date, 'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'predictions_generated':False, 'races':reports}


if __name__=='__main__':
    date=dt.datetime.now(ZoneInfo('Australia/Brisbane')).date().isoformat()
    print(json.dumps(probe(date),allow_nan=False))
