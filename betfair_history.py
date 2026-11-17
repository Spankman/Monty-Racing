"""Import official Betfair ANZ CSVs using V6's retained-race rules.

Public historical data only. No odds API key, model training or live selections.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from race_day import ROOT
from monty.normalization import full_clock_seconds

COLUMNS=['LOCAL_MEETING_DATE','SCHEDULED_RACE_TIME','ACTUAL_OFF_TIME','TRACK','STATE_CODE',
         'RACE_NO','WIN_MARKET_ID','RACING_TYPE','DISTANCE','RACE_TYPE','SELECTION_ID',
         'TAB_NUMBER','SELECTION_NAME','WIN_RESULT','WIN_BSP','BEST_AVAIL_BACK_AT_SCHEDULED_OFF']
STATES={'QLD','NSW','VIC','SA','WA','TAS','NT','ACT'}


def convert(raw):
    missing=set(COLUMNS)-set(raw)
    if missing:raise ValueError('Missing Betfair source columns: '+','.join(sorted(missing)))
    raw_count=len(raw)
    d=raw.loc[raw.STATE_CODE.isin(STATES)&raw.RACING_TYPE.eq('Thoroughbred'),COLUMNS].copy()
    dates=pd.to_datetime(d.LOCAL_MEETING_DATE,format='mixed',dayfirst=True,errors='coerce')
    # ISO dates need explicit handling: dayfirst is ambiguous for YYYY-MM-DD.
    iso=d.LOCAL_MEETING_DATE.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')
    dates.loc[iso]=pd.to_datetime(d.loc[iso,'LOCAL_MEETING_DATE'],format='%Y-%m-%d',errors='coerce')
    if dates.isna().any():raise ValueError('Invalid historical meeting date')
    d['date']=dates.dt.strftime('%Y-%m-%d');d=d.drop(columns='LOCAL_MEETING_DATE').drop_duplicates()
    for c in ['WIN_MARKET_ID','SELECTION_ID']:d[c]=d[c].astype(str)
    conflicts=set(d.loc[d.duplicated(['WIN_MARKET_ID','SELECTION_ID'],keep=False),'WIN_MARKET_ID'])
    d=d[~d.WIN_MARKET_ID.isin(conflicts)].copy()
    for c in ['DISTANCE','TAB_NUMBER','WIN_BSP','BEST_AVAIL_BACK_AT_SCHEDULED_OFF']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    d['scheduled_seconds']=d.SCHEDULED_RACE_TIME.map(full_clock_seconds)
    d['delay_seconds']=d.ACTUAL_OFF_TIME.map(full_clock_seconds)-d.scheduled_seconds
    d['_quote_ok']=np.isfinite(d.BEST_AVAIL_BACK_AT_SCHEDULED_OFF)&d.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.gt(1)
    d['_delay_ok']=d.delay_seconds.between(1,1200)
    d['_label_ok']=d.WIN_RESULT.isin(['WINNER','LOSER']);d['_winner']=d.WIN_RESULT.eq('WINNER')
    g=d.groupby('WIN_MARKET_ID',sort=False);sizes=g.size();reason=pd.Series('',index=sizes.index)
    metadata=g[['date','TRACK','STATE_CODE','RACE_NO','DISTANCE','scheduled_seconds','delay_seconds']].nunique(dropna=False)
    checks=[(sizes.lt(4),'fewer_than_four_runners'),(metadata.ne(1).any(axis=1),'inconsistent_race_metadata'),
            (~g._quote_ok.all(),'invalid_any_runner_quote'),(~g._delay_ok.all(),'quote_not_clearly_before_actual_off'),
            (~g._label_ok.all(),'unknown_outcome'),(g._winner.sum().ne(1),'not_single_winner')]
    for mask,label in checks:reason.loc[mask&reason.eq('')]=label
    d=d[d.WIN_MARKET_ID.isin(reason.index[reason.eq('')])].copy()
    d=d.sort_values(['date','scheduled_seconds','WIN_MARKET_ID','SELECTION_ID'],kind='stable').reset_index(drop=True)
    inv=1/d.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy(float)
    groups=pd.factorize(d.WIN_MARKET_ID)[0]
    denominator=np.bincount(groups,weights=inv)
    d['market_probability']=inv/denominator[groups]
    d['y']=d.WIN_RESULT.eq('WINNER').astype(int)
    d['class_text']=d.RACE_TYPE;d['barrier']=np.nan;d['jockey']='';d['trainer']='';d['going']='unknown'
    d=d.drop(columns=['_quote_ok','_delay_ok','_label_ok','_winner'])
    d=d.sort_values(['date','scheduled_seconds','WIN_MARKET_ID','SELECTION_ID'],kind='stable').reset_index(drop=True)
    return d,dict(raw_rows=raw_count,retained_runners=len(d),retained_races=d.WIN_MARKET_ID.nunique(),
        date_min=None if d.empty else d.date.min(),date_max=None if d.empty else d.date.max(),
        conflicting_races=len(conflicts),exclusions=reason[reason.ne('')].value_counts().to_dict(),
        missing_metadata=['barrier','jockey','trainer','going'],nz_supported_by_frozen_baseline=False,
        source='Official Betfair ANZ historical CSV',predictions_generated=False,betting_ready=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('csv');p.add_argument('--output-dir',default='history_data/imported')
    a=p.parse_args();source=Path(a.csv)
    d,audit=convert(pd.read_csv(source,dtype=str,keep_default_na=False))
    audit['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    d.to_csv(out/'canonical_history.csv.gz',index=False)
    (out/'import_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit))

if __name__=='__main__':main()
