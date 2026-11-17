"""Build pre-race V6 features from canonical, exact-identity historical fields.

No retraining; current-day outcomes are neither required nor written to history.
This is an offline data bridge, not independent verification of supplied sources.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from race_day import ROOT
from monty.integrity import verify_artifacts
from monty.normalization import normal,clean_person
from history_features import build_features

OPTIONAL=['allocated_weight','claim_kg','age','is_gelding','first_after_gelding',
          'blinkers_first','blinkers_off','tongue_tie_first','winkers_first']
REQUIRED=['date','WIN_MARKET_ID','SELECTION_ID','SELECTION_NAME','TRACK','DISTANCE',
          'market_probability','barrier','jockey','trainer','going','class_text']


def prepare(frame, historical, day):
    frame=frame.copy()
    missing=set(REQUIRED)-set(frame)
    if missing:raise ValueError('Missing canonical columns: '+','.join(sorted(missing)))
    for c in ['WIN_MARKET_ID','SELECTION_ID']:
        if frame[c].isna().any():raise ValueError('Missing exact market/horse identity')
        frame[c]=frame[c].astype(str)
    if frame[REQUIRED[:7]].isna().any().any():raise ValueError('Missing identity/date/distance')
    dates=pd.to_datetime(frame.date,format='%Y-%m-%d',errors='coerce')
    if dates.isna().any():raise ValueError('Invalid date')
    frame['date']=dates.dt.strftime('%Y-%m-%d')
    if historical and frame.date.ge(day).any():raise ValueError('History includes same-day or future records')
    if not historical and not frame.date.eq(day).all():raise ValueError('Current fields date mismatch')
    if frame.duplicated(['WIN_MARKET_ID','SELECTION_ID']).any():raise ValueError('Duplicate market/horse identity')
    frame['name_key']=frame.SELECTION_NAME.map(normal)
    if frame.name_key.eq('').any():raise ValueError('Missing horse name')
    p=pd.to_numeric(frame.market_probability,errors='coerce')
    if not np.isfinite(p).all() or not p.gt(0).all() or not p.lt(1).all():
        raise ValueError('Invalid market probabilities')
    frame['market_probability']=p
    if not np.allclose(frame.groupby('WIN_MARKET_ID').market_probability.sum(),1,atol=1e-8,rtol=0):
        raise ValueError('Incomplete or unnormalized market fields')
    if (frame.groupby('WIN_MARKET_ID').date.nunique()>1).any():raise ValueError('Market spans dates')
    if historical:
        if 'BEST_AVAIL_BACK_AT_SCHEDULED_OFF' not in frame:
            raise ValueError('Historical scheduled-off back quotes required; BSP/SP are not substitutes')
        quotes=pd.to_numeric(frame.BEST_AVAIL_BACK_AT_SCHEDULED_OFF,errors='coerce')
        if not np.isfinite(quotes).all() or not quotes.gt(1).all():
            raise ValueError('Invalid historical scheduled-off quotes')
        inv=1/quotes
        expected=inv/inv.groupby(frame.WIN_MARKET_ID).transform('sum')
        if not np.allclose(expected,p,atol=1e-12,rtol=0):
            raise ValueError('Market probabilities disagree with scheduled-off quotes')
        if 'y' not in frame or not frame.y.isin([0,1]).all():raise ValueError('Historical outcomes required')
        if not frame.groupby('WIN_MARKET_ID').y.sum().eq(1).all():
            raise ValueError('Historical field must have exactly one winner; dead heats unsupported')
    else:
        frame['y']=pd.NA  # Unknown, never a fabricated loss or win.
    for c in OPTIONAL:
        if c not in frame:frame[c]=np.nan
    frame['jockey']=frame.jockey.map(clean_person);frame['trainer']=frame.trainer.map(clean_person)
    frame['enriched_eligible']=not historical
    return frame


def build(history,current,day):
    import datetime as dt
    dt.date.fromisoformat(day)
    h=prepare(history,True,day);c=prepare(current,False,day)
    joined=pd.concat([h,c],ignore_index=True)
    if (joined.groupby('SELECTION_ID').name_key.nunique()>1).any():
        raise ValueError('Horse identity maps to conflicting names; explicit crosswalk required')
    # Equal names with different verified IDs are distinct horses, as in V6.
    # Never fall back to a name-only join across source namespaces.
    # Stable ordering within each local date; same-day histories are updated only after all rows.
    order=['date'] + (['scheduled_seconds'] if 'scheduled_seconds' in joined else []) + ['WIN_MARKET_ID','SELECTION_ID']
    if 'scheduled_seconds' not in h and h.duplicated(['date','SELECTION_ID']).any():
        raise ValueError('Multiple same-day starts need historical scheduled_seconds ordering')
    joined=joined.sort_values(order,kind='stable').reset_index(drop=True)
    selected,X,names=build_features(joined,prediction_date=day)
    if not selected.date.eq(day).all():raise ValueError('Unexpected historical output')
    return selected,X,names


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('history');parser.add_argument('current');parser.add_argument('--date',required=True)
    parser.add_argument('--output-dir',default='race_day_output/history_features')
    args=parser.parse_args();verified=verify_artifacts(ROOT)
    dtype={'SELECTION_ID':str,'WIN_MARKET_ID':str}
    rows,X,names=build(pd.read_csv(args.history,dtype=dtype),pd.read_csv(args.current,dtype=dtype),args.date)
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    features=rows[['date','WIN_MARKET_ID','SELECTION_ID','SELECTION_NAME']].reset_index(drop=True)
    features=pd.concat([features,pd.DataFrame(X,columns=names)],axis=1)
    features.to_csv(out/'features.csv',index=False)
    (out/'audit.json').write_text(json.dumps({'date':args.date,'runners':len(rows),'features':names,
        'artifact_hashes':verified,'current_outcomes_used':False,'predictions_generated':False,
        'source_provenance_independently_verified':False,'betting_ready':False},indent=2)+'\n')
    print('Built pre-race features; source provenance and live betting readiness remain unverified.')

if __name__=='__main__':main()
