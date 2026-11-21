"""Run frozen V6 on verified canonical historical/current fields only.

Requires exact source identity and scheduled-off quotes in the historical CSV.
Outputs research predictions, never betting-authorised recommendations.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from history_bridge import build
from race_day import ROOT
from monty.scoring import score_features

def run(history,current,day):
    rows,X,names=build(history,current,day)
    if rows.empty:raise ValueError('No current runners')
    market=rows.market_probability.to_numpy(float)
    pred=score_features(X,names,market,rows.WIN_MARKET_ID.to_numpy(),root=ROOT)
    out=rows[['date','WIN_MARKET_ID','SELECTION_ID','SELECTION_NAME','TRACK']].copy()
    out['market_probability']=market
    out['v6_probability']=pred
    out['feature_coverage']=np.isfinite(X).mean(axis=1)
    out['betting_authorised']=False
    out['status']='FROZEN_V6_RESEARCH_ONLY'
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('history');p.add_argument('current');p.add_argument('--date',required=True)
    p.add_argument('--output-dir',default='race_day_output/verified_v6')
    a=p.parse_args()
    h=pd.read_csv(a.history,dtype={'SELECTION_ID':str,'WIN_MARKET_ID':str})
    c=pd.read_csv(a.current,dtype={'SELECTION_ID':str,'WIN_MARKET_ID':str})
    result=run(h,c,a.date)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    result.to_csv(out/'frozen_v6_research.csv',index=False)
    audit={'date':a.date,'runners':len(result),
           'mean_feature_coverage':float(result.feature_coverage.mean()),
           'frozen_v6_scored':True,'source_provenance_independently_verified':False,
           'betting_authorised':False,'current_outcomes_used':False}
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit))

if __name__=='__main__':main()
