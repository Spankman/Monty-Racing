"""Simple prior-calibration-selected shrinkage to market. No extra features invented."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import predict,logloss
from .evaluate import metrics,digest
from .diagnose import day_bootstrap


def score(config,X,market,races):
    p=predict(config['candidate1_model'],X,market,races)
    w=config['form_weight']
    if isinstance(w,bool) or not isinstance(w,(int,float)) or not 0 <= w <= 1:
        raise ValueError('Invalid Candidate 2 form weight')
    return w*p+(1-w)*np.asarray(market)


def run(root,candidate1_dir,out):
    from monty_v6.monty.integrity import verify_artifacts
    verify_artifacts(root)
    prior=json.loads((candidate1_dir/'audit_backtest.json').read_text())
    for name,h in prior['input_sha256'].items():
        if digest(root/'results'/name)!=h:raise ValueError('Candidate 1 source changed')
    d=pd.read_csv(root/'results/joined_development_runners.csv.gz',dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    f=pd.read_csv(root/'results/development_features.csv.gz')
    if not np.array_equal(f.market_id.astype(str),d.WIN_MARKET_ID) or not np.array_equal(f.runner,d.SELECTION_NAME):raise ValueError('Identity mismatch')
    pred=pd.read_csv(candidate1_dir/'walk_forward_predictions.csv.gz',dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    lookup={tuple(row):i for i,row in enumerate(d[['WIN_MARKET_ID','SELECTION_ID']].itertuples(index=False,name=None))}
    pred['candidate2_probability']=np.nan;choices=[];out.mkdir(parents=True,exist_ok=True)
    for fold in prior['folds']:
        k=fold['fold'];m=json.loads((candidate1_dir/f'fold_{k}_model.json').read_text())
        cs,ce=fold['calibration'];ts,te=fold['test']
        if not cs<=ce<ts or not m['training_end']<cs:raise ValueError('Chronology violated')
        ca=d.date.between(cs,ce);test=pred.fold.eq(k)
        X=f.loc[ca,m['names']].to_numpy();base=d.loc[ca,'market_probability'].to_numpy()
        pc=predict(m,X,base,d.loc[ca,'WIN_MARKET_ID'])
        # Grid fixed in this follow-up; no choosing an edge cutoff from test profit.
        grid=[dict(form_weight=w,calibration_log_loss=logloss(d.loc[ca,'y'],w*pc+(1-w)*base)) for w in [0.,.5,1.]]
        best=min(grid,key=lambda r:(r['calibration_log_loss'],r['form_weight']))
        config=dict(candidate1_model=m,form_weight=best['form_weight'],selection_period=[cs,ce],evaluation_period=[ts,te],selection_grid=grid,
                    warning='Retrospective development on previously exposed dates. No prospective superiority established.')
        ids=[lookup[tuple(r)] for r in pred.loc[test,['WIN_MARKET_ID','SELECTION_ID']].itertuples(index=False,name=None)]
        v=score(config,f.iloc[ids][m['names']].to_numpy(),pred.loc[test,'market_probability'],pred.loc[test,'WIN_MARKET_ID'])
        reproduced=predict(m,f.iloc[ids][m['names']].to_numpy(),pred.loc[test,'market_probability'],pred.loc[test,'WIN_MARKET_ID'])
        if not np.allclose(reproduced,pred.loc[test,'v7_probability'],atol=1e-12):raise ValueError('Candidate 1 replay drift')
        pred.loc[test,'candidate2_probability']=v
        choices.append(dict(fold=k,**best,grid=grid,calibration=[cs,ce],test=[ts,te]))
        (out/f'fold_{k}_candidate2.json').write_text(json.dumps(config,indent=2))
    common=pred[pred.v6_probability.notna()]
    comparisons={};profitability={}
    for name,col in [('Candidate 2','candidate2_probability'),('Candidate 1','v7_probability'),('V6','v6_probability'),('Market','market_probability')]:
        comparisons[name]=metrics(common,common[col])
        z=common.copy();z['v7_probability']=z[col]
        z['odds']=z.BEST_AVAIL_BACK_AT_SCHEDULED_OFF
        z['expected_profit']=z.v7_probability*(z.odds-1)*.95-(1-z.v7_probability)
        z['profit']=np.where(z.y.eq(1),(z.odds-1)*.95,-1.)
        z['rank']=z.groupby('WIN_MARKET_ID').v7_probability.rank(method='first',ascending=False)
        top=z[z['rank'].eq(1)];bets=top[top.expected_profit.ge(.05)]
        profitability[name]={'all_top_picks':day_bootstrap(top,name+' all leaders'),'filtered_value_bets':day_bootstrap(bets,name+' filtered bets')}
    coverage=[]
    merged=pred.merge(d[['WIN_MARKET_ID','SELECTION_ID','going','class_text']],on=['WIN_MARKET_ID','SELECTION_ID'],validate='one_to_one')
    for fold,g in merged.groupby('fold'):
        races=g.drop_duplicates('WIN_MARKET_ID')
        coverage.append(dict(fold=int(fold),dates=[g.date.min(),g.date.max()],races=len(races),runners=len(g),tracks=int(g.TRACK.nunique()),states=races.STATE_CODE.value_counts().to_dict(),conditions=races.going.fillna('unknown').value_counts().to_dict(),track_names=sorted(g.TRACK.unique())))
    report=dict(status='CANDIDATE_2_SHRINKAGE_RESEARCH_NOT_DEPLOYED',choices=choices,common_dates=[common.date.min(),common.date.max()],comparison= comparisons,
        pooled={name:metrics(pred,pred[col]) for name,col in [('Candidate 2','candidate2_probability'),('Candidate 1','v7_probability'),('Market','market_probability')]},
        profitability_uncertainty=profitability,fold_coverage=coverage,
        source_hashes={'candidate1_predictions':digest(candidate1_dir/'walk_forward_predictions.csv.gz'),'candidate1_audit':digest(candidate1_dir/'audit_backtest.json')},
        preserved_artifacts=verify_artifacts(root),NZ={'status':'NOT_VALIDATED','historical_races_in_cohort':0},
        caveats=['All test dates previously exposed. Earlier-only selection protects computational chronology, not research-level holdout freshness.',
                 'All folds are April–mid-June 2025, adjacent and overlapping in tracks. Not representative of a full year, spring, or multiple market regimes.',
                 'No newly acquired point-in-time features integrated. Static metadata publication snapshots still unavailable.',
                 'V6 profitability independently uncertain: bootstrap filtered-profit intervals, sample size and executable-price limitations must be considered.',
                 'Do not select new odds/condition/class exclusion filters from this same diagnostic sample.'])
    (out/'comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False));pred.to_csv(out/'candidate2_predictions.csv.gz',index=False)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v6-root',type=Path,required=True);p.add_argument('--candidate1-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.v6_root,a.candidate1_dir,a.output)
    print(json.dumps({'choices':r['choices'],'comparison':{k:{a:b for a,b in v.items() if a!='reliability'} for k,v in r['comparison'].items()},'V6_uncertainty':r['profitability_uncertainty']['V6'],'coverage':r['fold_coverage']},indent=2))
