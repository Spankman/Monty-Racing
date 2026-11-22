"""Candidate 2 evidence audit. No fitting, retuning, or edits to frozen picks."""
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def interval(w,n):
    if not n:return (None,None)
    z=norm.ppf(.975);p=w/n;den=1+z*z/n
    centre=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return float(centre-half),float(centre+half)


def summary(d):
    n=len(d);wins=int(d.y.sum());expected=float(d.v7_probability.sum())
    low,high=interval(wins,n)
    return dict(bets=n,wins=wins,expected_wins=expected,mean_predicted_probability=float(d.v7_probability.mean()) if n else None,
        strike_rate=float(wins/n) if n else None,win_rate_wilson_95_low=low,win_rate_wilson_95_high=high,
        mean_odds=float(d.odds.mean()) if n else None,expected_profit_units=float(d.expected_profit.sum()),
        actual_profit_units=float(d.profit.sum()),realization_minus_model_units=float((d.profit-d.expected_profit).sum()),
        roi=float(d.profit.mean()) if n else None,
        expected_roi=float(d.expected_profit.mean()) if n else None)


def class_group(s):
    s=str(s).upper()
    if re.search(r'\b(MDN|MAIDEN)\b',s):return 'Maiden'
    m=re.search(r'\bBM\s*(\d+)',s)
    if m:return 'BM <=64' if int(m[1])<=64 else 'BM >=65'
    if re.search(r'\b(CLASS|CL)\s*\d',s):return 'Class restricted'
    if re.search(r'GROUP|LISTED|\bG[123]\b',s):return 'Group/Listed'
    if not s or s=='NAN':return 'Unknown'
    return 'Other (see raw class)'


def calibration(d, population):
    records=[]
    # Fixed intervals, not tuned around observed win rates. Right-open, final includes 1.
    definitions=[('10% vicinity',.05,.15),('20% vicinity',.15,.25),('40% vicinity',.35,.45)]
    definitions += [(f'{lo:.1f}–{hi:.1f}',lo,hi) for lo,hi in zip(np.arange(0,1,.1),np.arange(.1,1.1,.1))]
    for label,lo,hi in definitions:
        b=d[d.v7_probability.ge(lo)&(d.v7_probability.lt(hi) if hi<.999 else d.v7_probability.le(1))]
        s=summary(b);records.append(dict(population=population,bin=label,lower=lo,upper=hi,**s))
    return records


def day_bootstrap(d, label, seed=702, draws=4000):
    if d.empty:return dict(population=label,rows=0)
    daily=d.groupby('date').agg(n=('y','size'),wins=('y','sum'),expected=('v7_probability','sum'),profit=('profit','sum'))
    ix=np.random.default_rng(seed).integers(0,len(daily),(draws,len(daily)))
    n=daily.n.to_numpy()[ix].sum(1)
    gap=(daily.wins-daily.expected).to_numpy()[ix].sum(1)/n
    roi=daily.profit.to_numpy()[ix].sum(1)/n
    return dict(population=label,rows=len(d),days=len(daily),observed_minus_predicted_probability_95=np.quantile(gap,[.025,.975]).tolist(),
        quote_proxy_roi_day_bootstrap_95=np.quantile(roi,[.025,.975]).tolist())


def run(predictions,metadata,out,features=None):
    inputs={str(predictions):sha(predictions),str(metadata):sha(metadata)}
    d=pd.read_csv(predictions,dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    d=d[d.v6_probability.notna()].copy() # the original 139-bet comparison period only
    m=pd.read_csv(metadata,dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    key=['WIN_MARKET_ID','SELECTION_ID']; attrs=['date','SELECTION_NAME','going','class_text','RACE_TYPE']
    if m.duplicated(key).any():raise ValueError('Duplicate original metadata')
    z=d.merge(m[key+attrs],on=key,suffixes=('','_original'),validate='one_to_one',indicator=True)
    if not z._merge.eq('both').all() or not z.date.eq(z.date_original).all() or not z.SELECTION_NAME.eq(z.SELECTION_NAME_original).all():
        raise ValueError('Prediction metadata identity mismatch')
    z['odds']=z.BEST_AVAIL_BACK_AT_SCHEDULED_OFF
    z['rank']=z.groupby('WIN_MARKET_ID').v7_probability.rank(method='first',ascending=False)
    z['market_rank']=z.groupby('WIN_MARKET_ID').market_probability.rank(method='min',ascending=False)
    z['expected_profit']=z.v7_probability*(z.odds-1)*.95-(1-z.v7_probability)
    z['profit']=np.where(z.y.eq(1),(z.odds-1)*.95,-1.)
    z['odds_range']=pd.cut(z.odds,[1,3,5,10,20,np.inf],right=False,labels=['<3','3–<5','5–<10','10–<20','20+']).astype(str)
    z['probability_band']=pd.cut(z.v7_probability,[0,.2,.4,.6,1.000001],right=False,labels=['<20%','20–<40%','40–<60%','60%+']).astype(str)
    z['market_role']=np.where(z.market_rank.eq(1),'Favourite (including ties)',np.where(z.market_rank.le(3),'Market ranks 2–3','Outsider (market rank >=4)'))
    z['class_group']=z.class_text.map(class_group)
    top=z[z['rank'].eq(1)].copy(); top['original_value_bet']=top.expected_profit.ge(.05)
    bets=top[top.original_value_bet].copy();passed=top[~top.original_value_bet]
    if len(bets)!=139 or not np.isclose(bets.profit.sum(),-20.5325):raise ValueError('Original strategy reproduction failed')
    adjustment={}
    if features is not None:
        from .core import predict
        f=pd.read_csv(features)
        if len(f)!=len(m) or not np.array_equal(f.market_id.astype(str),m.WIN_MARKET_ID) or not np.array_equal(f.runner,m.SELECTION_NAME):
            raise ValueError('Feature identity mismatch for calibration audit')
        lookup={tuple(row):i for i,row in enumerate(m[key].itertuples(index=False,name=None))}
        loc=[lookup[tuple(row)] for row in z[key].itertuples(index=False,name=None)]
        z['uncalibrated_probability']=np.nan
        for fold,g in z.groupby('fold'):
            mp=predictions.parent/f'fold_{int(fold)}_model.json';model=json.loads(mp.read_text())
            X=f.iloc[np.array(loc)[g.index]][model['names']].to_numpy()
            reproduced=predict(model,X,g.market_probability,g.WIN_MARKET_ID)
            if not np.allclose(reproduced,g.v7_probability,atol=1e-12):raise ValueError('Frozen calibration replay mismatch')
            model['temperature']=1.
            z.loc[g.index,'uncalibrated_probability']=predict(model,X,g.market_probability,g.WIN_MARKET_ID)
        top['uncalibrated_probability']=z.loc[top.index,'uncalibrated_probability']
        bets['uncalibrated_probability']=z.loc[bets.index,'uncalibrated_probability']
        for name,pop in [('all runners',z),('all race leaders',top),('original 139 bets',bets)]:
            adjustment[name]=dict(rows=len(pop),actual_wins=int(pop.y.sum()),
                pre_temperature_expected_wins=float(pop.uncalibrated_probability.sum()),
                calibrated_expected_wins=float(pop.v7_probability.sum()))
        inputs[str(features)]=sha(features)
    rows=[]
    for dim in ['odds_range','going','probability_band','market_role','class_group','class_text','TRACK','fold']:
        for group,b in bets.groupby(dim,dropna=False,observed=True):rows.append(dict(dimension=dim,group=str(group),**summary(b)))
    breakdown=pd.DataFrame(rows);cal=[]
    for name,pop in [('all runners',z),('all race leaders',top),('original 139 bets',bets),('passed race leaders',passed)]:cal+=calibration(pop,name)
    sensitivities=[]
    for edge in [0,.025,.05,.075,.10,.15]:
        b=top[top.expected_profit.ge(edge)]
        sensitivities.append(dict(minimum_net_edge=edge,**summary(b)))
    uncertainty=[]
    for name,pop in [('all runners',z),('all race leaders',top),('original 139 bets',bets),('passed race leaders',passed)]:
        uncertainty.append(day_bootstrap(pop,name))
        for target in [.1,.2,.4]:
            b=pop[pop.v7_probability.ge(target-.05)&pop.v7_probability.lt(target+.05)]
            uncertainty.append(day_bootstrap(b,name+f' / {target:.0%} vicinity'))
    # Keep fold contrasts separate; each uses a different earlier-fitted model.
    folds=[dict(fold=int(f),**summary(b)) for f,b in bets.groupby('fold')]
    report=dict(status='CANDIDATE_2_DIAGNOSTIC_ONLY_NO_NEW_MODEL',period=[z.date.min(),z.date.max()],
        original_bets=summary(bets),passed_leaders=summary(passed),folds=folds,
        calibration_adjustment_fixed_selections=adjustment,bootstrap=uncertainty,threshold_sensitivity=sensitivities,input_sha256=inputs,
        warnings=['Threshold comparisons are post-hoc diagnostics, not selection/optimization or fresh validation.',
        'All 2025 dates already exposed. Calibration measured on disjoint test periods, not a fresh prospective sample.',
        'Condition/class metadata reconstructed historically; publication/as-of snapshots unavailable.',
        'Win-rate Wilson intervals are approximate. Day-block bootstrap accounts for date clustering, but few days remain uncertain.',
        'Confidence means numeric win-probability band, not a claim of independently validated certainty.',
        'Profit uses scheduled-off best-back quotes and 5% commission; liquidity/execution not verified.',
        'One leading-probability runner per race; not all possible runners, no meeting quotas.',
        'All-runner profit/ROI is descriptive only; no strategy bet every runner.',
        'Aggregate all-runner calibration gap is identically zero because each complete field sums to one; use probability bins, not that aggregate, to assess calibration.',
        'No original selections, probabilities, models or training parameters altered.'])
    out.mkdir(parents=True,exist_ok=True)
    breakdown.to_csv(out/'loss_breakdown.csv',index=False)
    pd.DataFrame(cal).to_csv(out/'calibration.csv',index=False)
    pd.DataFrame(sensitivities).to_csv(out/'threshold_sensitivity.csv',index=False)
    bets.to_csv(out/'original_139_bets_audited.csv',index=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    if any(sha(p)!=h for p,h in inputs.items()):raise ValueError('Input drift')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--predictions',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--features',type=Path)
    a=p.parse_args();r=run(a.predictions,a.metadata,a.output,a.features)
    print(json.dumps({'bets':r['original_bets'],'folds':r['folds'],'thresholds':r['threshold_sensitivity'],'bootstrap_bets':[x for x in r['bootstrap'] if x['population']=='original 139 bets']},indent=2))
