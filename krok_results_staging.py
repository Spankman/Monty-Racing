"""Read-only Krok historical-results staging for V6 source assessment.

This does NOT create V6 training rows: entry_id is not a verified persistent
horse identity, and starting_price/BSP cannot replace scheduled-off quotes.
"""
import argparse
import datetime as dt
import json
import os
from collections import Counter
from pathlib import Path
from krok_client import get

def inspect(payload, date):
    races=payload.get('data')
    if not isinstance(races,list):
        raise ValueError('Expected results race list')
    counts=Counter()
    staged=[]
    for race in races:
        if not isinstance(race,dict):raise ValueError('Invalid race')
        runners=race.get('runners') or []
        if not isinstance(runners,list):raise ValueError('Invalid runners')
        counts['races']+=1
        for runner in runners:
            if not isinstance(runner,dict):raise ValueError('Invalid runner')
            counts['runners']+=1
            if runner.get('is_scratched') is True:
                counts['scratched']+=1
                continue
            for field in ('entry_id','name','jockey','trainer','barrier','finish_position','starting_price','win_bsp','weight'):
                if runner.get(field) is not None:counts['with_'+field]+=1
            staged.append({
                'date':date,
                'provider_entry_id':runner.get('entry_id'),
                'horse_name':runner.get('name'),
                'jockey':runner.get('jockey'),
                'trainer':runner.get('trainer'),
                'barrier':runner.get('barrier'),
                'finish_position':runner.get('finish_position'),
                'starting_price':runner.get('starting_price'),
                'win_bsp':runner.get('win_bsp'),
                'weight':runner.get('weight'),
                'identity_crosswalk_verified':False,
                'scheduled_off_quote_verified':False,
                'v6_history_eligible':False
            })
    return staged,dict(counts)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--date',required=True)
    p.add_argument('--output-dir',default='race_day_output/history_staging')
    a=p.parse_args()
    day=dt.date.fromisoformat(a.date)
    if day>=dt.datetime.now(dt.timezone(dt.timedelta(hours=10))).date():
        raise SystemExit('Historical results date must precede Queensland today')
    payload=get('/api/v1/racing/results/'+a.date,{},os.environ.get('KROK_API_KEY'))
    if (payload.get('meta') or {}).get('truncated') is not False:
        raise SystemExit('Historical results completeness not confirmed')
    staged,counts=inspect(payload,a.date)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'results_staging.json').write_text(json.dumps(staged,indent=2)+'\n')
    audit={'date':a.date,'counts':counts,'source':'Krok results API',
           'identity_crosswalk_verified':False,'scheduled_off_quotes_verified':False,
           'v6_history_eligible':False,'predictions_generated':False}
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit))

if __name__=='__main__':main()
