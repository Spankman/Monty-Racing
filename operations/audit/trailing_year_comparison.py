"""Diagnostic only: frozen V6 on later retained exchange markets, with limited exact history."""
from collections import defaultdict,deque
from pathlib import Path
import argparse
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'monty_v6'))
from monty.normalization import normal
from monty.scoring import score_features

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('canonical_months', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
p = ROOT / 'monty_v6'
m=json.loads((p/'results/frozen_model.json').read_text())
names=m['input_feature_names']
files=sorted(args.canonical_months.glob('*.canonical.csv.gz'))
frames=[pd.read_csv(f,dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str}) for f in files]
d=pd.concat(frames,ignore_index=True)
if d.duplicated(['WIN_MARKET_ID','SELECTION_ID']).any():
    raise ValueError('Conflicting or duplicated markets across month files')
d=d.sort_values(['date','scheduled_seconds','WIN_MARKET_ID','SELECTION_ID'],kind='stable').reset_index(drop=True)
d['name_key']=d.SELECTION_NAME.map(normal)
stop=d.date.max()
start='2026-05-02'
eval_mask=d.date.ge(start)
eval_rows=d.loc[eval_mask].reset_index(drop=True)
if len(eval_rows)==0:raise ValueError('Missing later test data')
available={f.name[:7].replace('_','-') for f in files}
required={str(x) for x in pd.period_range('2025-05',stop[:7],freq='M')}
if required-available:raise ValueError('Incomplete history: '+str(required-available))
market=eval_rows.market_probability.to_numpy()
race_ids=eval_rows.WIN_MARKET_ID
field_size=eval_rows.groupby('WIN_MARKET_ID').SELECTION_ID.transform('size')
masked=np.full((len(eval_rows),len(names)),np.nan)
for n,x in [('log_market_probability',np.log(market)),('log_field_size',np.log(field_size)),('distance_km',eval_rows.DISTANCE/1000)]:
    masked[:,names.index(n)]=x
rich=masked.copy()
history=defaultdict(deque)
row=0
for date,z in d.groupby('date',sort=False):
    ordinal=pd.Timestamp(date).toordinal()
    if date>=start:
        for x in z.itertuples():
            events=history[(x.SELECTION_ID,x.name_key)]
            while events and ordinal-events[0][0]>365:
                events.popleft()
            n=len(events)
            wins=sum(e[1] for e in events)
            expectation=sum(e[2] for e in events)
            for k,v in [('year_starts_log',np.log1p(n)),('year_win_rate',(wins+.5)/(n+5)),
                        ('year_market_residual',(wins-expectation)/(n+5))]:
                rich[row,names.index(k)]=v
            row+=1
    for x in z.itertuples():
        history[(x.SELECTION_ID,x.name_key)].append((ordinal,x.y,x.market_probability))
assert row==len(eval_rows)
wins=eval_rows.y.to_numpy()==1
full=score_features(rich,names,market,race_ids,root=p)
sparse=score_features(masked,names,market,race_ids,root=p)
days=pd.factorize(eval_rows.loc[wins,'date'],sort=True)[0]
rng=np.random.default_rng(20261125)
ix=rng.integers(days.max()+1,size=(4000,days.max()+1))
counts=np.bincount(days)[ix].sum(axis=1)
def metrics(p,baseline):
    loss=-np.log(p[wins])
    delta=loss+np.log(baseline[wins])
    boot=np.bincount(days,weights=delta)[ix].sum(axis=1)/counts
    top=pd.Series(p).groupby(race_ids,sort=False).idxmax().to_numpy()
    odds=eval_rows.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()[top]
    returns=np.where(wins[top],(odds-1)*.95,-1.)
    equity=np.r_[0,np.cumsum(returns)]
    return {'log_loss':loss.mean(),'brier':np.square(wins-p).sum()/len(top),
            'strike':wins[top].mean(),'proxy_roi':returns.mean(),
            'proxy_drawdown':(np.maximum.accumulate(equity)-equity).max(),
            'delta_log_loss':delta.mean(),'paired_day_ci':np.quantile(boot,[.025,.975]).tolist()}
result=dict(
    testing_dates=[start,stop], races=int(race_ids.nunique()), runners=len(eval_rows),
    months=sorted(available), market=metrics(market,market), sparse=metrics(sparse,market),
    restored_365d=metrics(full,market), restored_vs_sparse=metrics(full,sparse),
    limitation='Retrospective AU exchange quote diagnostic. Three trailing-year inputs only. Metadata unavailable. Prior same-day events excluded; no live mapping, book prices, or untouched sample claimed.'
)
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
