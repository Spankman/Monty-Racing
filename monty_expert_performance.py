"""Chronological, provenance-first expert performance and candidate weights.

Only evaluates immutable pre-race tip records joined to verified race results.
No model training or historical selection reconstruction is performed here.
"""
import argparse, json
import pandas as pd
import numpy as np

KEY=['meeting','race','number']
def evaluate(tips_path,results_path,min_bets=30):
    tips=pd.read_csv(tips_path,dtype={k:str for k in KEY})
    results=pd.read_csv(results_path,dtype={k:str for k in KEY})
    needed=set(KEY+['source','captured_at','race_off_at','odds'])
    if not needed.issubset(tips):raise ValueError('Tips missing required fields')
    if not set(KEY+['won']).issubset(results):raise ValueError('Results missing required fields')
    if tips.empty:return {'experts':[],'note':'No expert tips'}
    if tips[list(needed)].isna().any().any() or tips.source.astype(str).str.strip().eq('').any():
        raise ValueError('Missing provenance')
    if tips.duplicated(KEY+['source']).any() or results.duplicated(KEY).any():
        raise ValueError('Duplicate tip or result identity')
    import re
    pattern=re.compile(r'(?:Z|[+-][0-9]{2}:[0-9]{2})$')
    if not tips.captured_at.map(lambda x:bool(pattern.search(str(x)))).all() or not tips.race_off_at.map(lambda x:bool(pattern.search(str(x)))).all():
        raise ValueError('Timestamps must include timezone')
    capture=pd.to_datetime(tips.captured_at,utc=True,errors='coerce')
    off=pd.to_datetime(tips.race_off_at,utc=True,errors='coerce')
    if capture.isna().any() or off.isna().any() or (capture>=off).any():
        raise ValueError('Tip must be recorded before race off')
    if tips.groupby(['meeting','race']).race_off_at.nunique().gt(1).any():
        raise ValueError('Conflicting off times')
    tips['odds']=pd.to_numeric(tips.odds,errors='raise')
    if not np.isfinite(tips.odds).all() or (tips.odds<=1).any():
        raise ValueError('Invalid captured odds')
    results['won']=pd.to_numeric(results.won,errors='raise')
    if not results.won.isin([0,1]).all() or results.groupby(['meeting','race']).won.sum().gt(1).any():
        raise ValueError('Invalid race results')
    joined=tips.merge(results[KEY+['won']],on=KEY,how='left',validate='many_to_one',indicator=True)
    # Do not silently drop missing outcomes or count them as losses.
    if (joined._merge!='both').any():raise ValueError('Results missing for recorded tips')
    # Each source/race is one evaluation unit. Multiple selections in a race
    # are recorded but not treated as independent evidence for a win-only bet.
    rows=[]
    for source,g in joined.groupby('source'):
        unique_races=g.groupby(['meeting','race']).ngroups
        returns=(g.odds*g.won).sum()
        bets=len(g)
        rows.append({'source':source,'tips':bets,'races':int(unique_races),
          'wins':int(g.won.sum()),'strike_rate':round(float(g.won.mean()),5),
          'flat_win_roi':round(float(returns/bets-1),5),
          'eligible_for_weight_research':bool(unique_races>=min_bets),
          'caution':'Descriptive only; not out-of-sample proof of skill'})
    return {'experts':rows,'min_races_for_research':min_bets,
      'note':'Descriptive pre-race records only; no adaptive weights assigned'}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('tips');p.add_argument('results')
    p.add_argument('--output',default='expert_performance.json')
    p.add_argument('--min-races',type=int,default=30)
    a=p.parse_args()
    report=evaluate(a.tips,a.results,a.min_races)
    with open(a.output,'w') as f:json.dump(report,f,indent=2)
    print(json.dumps({'experts':len(report['experts'])}))
