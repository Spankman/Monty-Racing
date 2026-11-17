"""Reproducible retrospective expanding-window evaluation on immutable V6 data."""
import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from .core import fit,predict,calibrate,logloss,value_decision


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def metrics(d, p, commission=.05, edge=.05):
    z=d[['date','WIN_MARKET_ID','y','BEST_AVAIL_BACK_AT_SCHEDULED_OFF']].copy()
    z['p']=p;z['square']=(z.p-z.y)**2
    z['rank']=z.groupby('WIN_MARKET_ID').p.rank(method='first',ascending=False)
    picks=z[z['rank'].eq(1)].copy()
    quotes=picks.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    ev=picks.p.to_numpy()*(quotes-1)*(1-commission)-(1-picks.p.to_numpy())
    picks['bet']=ev>=edge
    picks['profit']=np.where(picks.y.eq(1),(quotes-1)*(1-commission),-1.)
    # Daily aggregation avoids implying unknown intra-day bet ordering.
    profit=picks[picks.bet].groupby('date').profit.sum().sort_index()
    equity=np.r_[0.,profit.cumsum().to_numpy()]
    drawdown=np.maximum.accumulate(equity)-equity
    bins=pd.cut(z.p,np.linspace(0,1,11),include_lowest=True)
    reliability=z.groupby(bins,observed=True).agg(count=('y','size'),prediction=('p','mean'),observed=('y','mean'))
    ece=float((reliability['count']*(reliability.prediction-reliability.observed).abs()).sum()/len(z))
    n=int(picks.bet.sum())
    return dict(races=len(picks),runners=len(z),log_loss=logloss(z.y,z.p),
        brier_per_race=float(z.groupby('WIN_MARKET_ID')['square'].sum().mean()),
        calibration_ece_runner=ece,top_pick_strike=float(picks.y.mean()),
        top_pick_quote_proxy_roi=float(picks.profit.mean()),value_bets=n,
        value_strike=float(picks.loc[picks.bet,'y'].mean()) if n else None,
        value_quote_proxy_roi=float(picks.loc[picks.bet,'profit'].mean()) if n else None,
        value_profit_units=float(picks.loc[picks.bet,'profit'].sum()),
        max_daily_drawdown_units=float(drawdown.max()),
        no_bet_races=int((~picks.bet).sum()),
        reliability=[dict(bin=str(i),**r) for i,r in reliability.to_dict('index').items()])


def load(root, history_package, scratch):
    from monty_v6.monty.integrity import verify_artifacts
    verify_artifacts(root)
    f=pd.read_csv(root/'results/development_features.csv.gz')
    d=pd.read_csv(root/'results/joined_development_runners.csv.gz')
    model=json.loads((root/'results/frozen_model.json').read_text())
    names=model['input_feature_names']
    if len(d)!=len(f) or not np.array_equal(d.WIN_MARKET_ID,f.market_id) or not np.array_equal(d.SELECTION_NAME,f.runner) or not np.array_equal(d.date,f.date) or not np.array_equal(d.y,f.outcome_y):
        raise ValueError('Feature/outcome identity mismatch')
    if d.duplicated(['WIN_MARKET_ID','SELECTION_ID']).any() or not d.date.is_monotonic_increasing:
        raise ValueError('Duplicate runners or unsorted dates')
    groups=d.groupby('WIN_MARKET_ID')
    if not groups.y.sum().eq(1).all() or not groups.date.nunique().eq(1).all() or not np.allclose(groups.market_probability.sum(),1):
        raise ValueError('Incomplete or invalid races')
    # Recompute causal history from originals, not merely trust exported features.
    from monty_v6.monty.features import build_features
    import sys
    from monty_v6.monty import ingestion
    sys.path.insert(0,str(history_package/'monty_v5'))
    old_here,old_out=ingestion.HERE,ingestion.OUT
    ingestion.HERE=history_package/'monty_v6'; ingestion.OUT=scratch
    try:
        full=ingestion.add_overlays(ingestion.join_sources())
    finally:
        ingestion.HERE,ingestion.OUT=old_here,old_out
    rebuilt,X,rebuilt_names=build_features(full)
    if not np.array_equal(rebuilt.WIN_MARKET_ID.astype(str),d.WIN_MARKET_ID.astype(str)) or not np.array_equal(rebuilt.SELECTION_NAME,d.SELECTION_NAME):
        raise ValueError('Warm-up reconstruction identity mismatch')
    if rebuilt_names!=names or not np.allclose(X,f[names].to_numpy(),equal_nan=True,atol=1e-12,rtol=1e-12):
        raise ValueError('Original causal feature replay mismatch')
    return d,X,names,model


def run(root,out,history_package):
    out.mkdir(parents=True,exist_ok=True)
    files=['development_features.csv.gz','joined_development_runners.csv.gz','frozen_model.json']
    before={n:digest(root/'results'/n) for n in files}
    d,X,names,v6=load(root,history_package,out)
    folds=[('2025-02-28','2025-03-01','2025-03-15','2025-03-16','2025-03-31','2025-04-01','2025-04-30'),
           ('2025-03-31','2025-04-01','2025-04-15','2025-04-16','2025-04-30','2025-05-01','2025-05-31'),
           ('2025-04-30','2025-05-01','2025-05-15','2025-05-16','2025-05-31','2025-06-01','2025-06-15')]
    predictions=[];reports=[]
    for i,(train_end,vs,ve,cs,ce,ts,te) in enumerate(folds,1):
        tr=d.date.le(train_end).to_numpy(); va=d.date.between(vs,ve).to_numpy()
        ca=d.date.between(cs,ce).to_numpy(); test=d.date.between(ts,te).to_numpy()
        assert d.loc[tr,'date'].max()<vs<=ve<cs<=ce<ts
        candidates=[]
        for penalty in (.01,.1,1.):
            m=fit(X[tr],d.y.to_numpy()[tr],d.market_probability.to_numpy()[tr],d.WIN_MARKET_ID.to_numpy()[tr],names,penalty)
            p=predict(m,X[va],d.market_probability.to_numpy()[va],d.WIN_MARKET_ID.to_numpy()[va])
            candidates.append((logloss(d.y.to_numpy()[va],p),m))
        _,m=min(candidates,key=lambda x:x[0])
        pc=predict(m,X[ca],d.market_probability.to_numpy()[ca],d.WIN_MARKET_ID.to_numpy()[ca])
        m['temperature']=calibrate(pc,d.y.to_numpy()[ca],d.WIN_MARKET_ID.to_numpy()[ca])
        p=predict(m,X[test],d.market_probability.to_numpy()[test],d.WIN_MARKET_ID.to_numpy()[test])
        z=d.loc[test,['date','TRACK','STATE_CODE','RACE_NO','WIN_MARKET_ID','SELECTION_ID','SELECTION_NAME','TAB_NUMBER','y','market_probability','BEST_AVAIL_BACK_AT_SCHEDULED_OFF']].copy()
        z['v7_probability']=p;z['fold']=i;z['v6_probability']=np.nan
        # Frozen V6 selected on April; comparing April with it would leak.
        if ts>'2025-04-30':
            from monty_v6.monty.scoring import score_features
            z['v6_probability']=score_features(X[test],names,z.market_probability,z.WIN_MARKET_ID,root)
        report=dict(fold=i,train_end=train_end,selection=[vs,ve],calibration=[cs,ce],test=[ts,te],
                    train_races=int(d.loc[tr,'WIN_MARKET_ID'].nunique()),selected_penalty=m['penalty'],temperature=m['temperature'],
                    v7=metrics(z,p),market=metrics(z,z.market_probability),v6=metrics(z,z.v6_probability) if z.v6_probability.notna().all() else None)
        m['training_end']=train_end;m['calibration_end']=ce;m['test_start']=ts
        (out/f'fold_{i}_model.json').write_text(json.dumps(m,indent=2))
        reports.append(report);predictions.append(z)
    pred=pd.concat(predictions,ignore_index=True)
    pred.to_csv(out/'walk_forward_predictions.csv.gz',index=False)
    common=pred[pred.v6_probability.notna()]
    # Paired day-block bootstrap, fixed seed, no strategy tuning on test outcomes.
    loss=common[['date','WIN_MARKET_ID','y']].copy()
    for method in ['v7','v6','market']:
        col='market_probability' if method=='market' else method+'_probability'
        loss[method]=np.where(common.y.eq(1),-np.log(np.maximum(common[col],1e-15)),0)
    daily=loss.groupby('date').agg(v7=('v7','sum'),v6=('v6','sum'),market=('market','sum'),races=('WIN_MARKET_ID','nunique'))
    rng=np.random.default_rng(700); idx=rng.integers(0,len(daily),(2000,len(daily)))
    uncertainty={}
    for method in ['v6','market']:
        delta=(daily.v7-daily[method]).to_numpy()[idx].sum(1)/daily.races.to_numpy()[idx].sum(1)
        uncertainty['v7_minus_'+method+'_log_loss_day_bootstrap_95']=np.quantile(delta,[.025,.975]).tolist()
    report=dict(uncertainty=uncertainty,status='RETROSPECTIVE_RESEARCH_NOT_APPROVED_FOR_REPLACEMENT',
        limitations=['Dates and features previously exposed during V5/V6 development; not fresh prospective evidence.',
        'Chronological computation verified; historical metadata publication/as-of times not established.',
        'Australia-only retained dataset. NZ and international transfer performance unvalidated.',
        'Scheduled-off best-back quotes are retrospective payout proxies, not guaranteed executable trades.',
        '5% commission assumption; no liquidity, slippage, latency or stake-impact model.',
        'No verified finishing-order/place outcomes; place and quinella estimates not calibrated or backtested.',
        'No historical sectionals, weather forecast vintages, interference, pace or bias inputs integrated into these fits.',
        'Expert weighting defaults zero; no timestamped expert history available.'],
        features=names,rows=len(d),races=int(d.WIN_MARKET_ID.nunique()),dates=[d.date.min(),d.date.max()],
        input_sha256=before,history_inputs_sha256={str(p.relative_to(history_package)):digest(p) for p in [history_package/'monty_v5/results/cleaned_eligible_runners.csv.gz',history_package/'monty_v6/sources/github_racing_data.csv',history_package/'monty_v6/sources/april_recovery/ANZ_Thoroughbreds_2025_04.csv']},folds=reports,
        pooled=dict(v7=metrics(pred,pred.v7_probability),market=metrics(pred,pred.market_probability)),
        common_v6_period=dict(dates=[common.date.min(),common.date.max()],v7=metrics(common,common.v7_probability),
                             market=metrics(common,common.market_probability),v6=metrics(common,common.v6_probability)),
        runtime=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__),
        protocol=dict(penalties=[.01,.1,1.],temperature_bounds=[.5,2.],value_edge=.05,commission=.05,stake='one unit per race at most',expert_weight=0))
    if before!={n:digest(root/'results'/n) for n in files}:raise ValueError('Original input modified')
    from monty_v6.monty.integrity import verify_artifacts
    report['preserved_artifact_hashes']=verify_artifacts(root)
    (out/'audit_backtest.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--history-package',type=Path,required=True);ap.add_argument('--v6-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();r=run(a.v6_root.resolve(),a.output.resolve(),a.history_package.resolve())
    print(json.dumps({'status':r['status'],'common_v6_period':r['common_v6_period'],'preserved':r['preserved_artifact_hashes']},indent=2))
