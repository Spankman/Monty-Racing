"""Create-only provenance records for daily and ad-hoc single-race picks.

Research metadata only. Never asserts pre-off proof or authorises bets.
"""
import hashlib
import json
from pathlib import Path

MODES=('FULL_DAY','SINGLE_RACE')

def record_prediction(path, *, mode, meeting, race, selections, source,
                      recorded_at_utc, parent_daily_id=None):
    if mode not in MODES:raise ValueError('Invalid prediction mode')
    if mode=='SINGLE_RACE' and not parent_daily_id:
        # Standalone ad-hoc requests are allowed; original daily entries untouched.
        parent_daily_id=None
    if not meeting or not str(race).strip() or not source:
        raise ValueError('Meeting, race and source required')
    if not isinstance(selections,(list,tuple)) or not selections:
        raise ValueError('Selections required; use separate NO_BET event')
    for p in selections:
        if not isinstance(p,dict) or not str(p.get('number','')).strip() or not str(p.get('horse','')).strip():
            raise ValueError('Each selection needs number and horse')
    if not recorded_at_utc.endswith('Z'):
        raise ValueError('UTC timestamp ending Z required')
    entry=dict(schema='monty_prediction_mode_v1',mode=mode,meeting=str(meeting),
               race=str(race),selections=list(selections),source=source,
               recorded_at_utc=recorded_at_utc,parent_daily_id=parent_daily_id,
               pre_off_proven=False,betting_authorised=False,
               model_execution_independently_verified=False)
    canonical=json.dumps(entry,sort_keys=True,separators=(',',':')).encode()
    entry['record_sha256']=hashlib.sha256(canonical).hexdigest()
    dest=Path(path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x',encoding='utf-8') as f:
        json.dump(entry,f,indent=2,sort_keys=True)
        f.write(chr(10))
    return entry
