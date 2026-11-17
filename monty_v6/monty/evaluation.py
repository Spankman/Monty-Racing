"""Already-exposed diagnostic reporting, separate from model selection."""
import numpy as np,pandas as pd
from .config import OUT,dump
from .model_math import probabilities,metrics

def evaluate_diagnostic(d,fit):
    train,valid,test,models,selected,gb,off,F,Z=[fit[k] for k in ['train','valid','test','models','selected','gb','off','F','Z']]
    # Diagnostic scored only now, after validation-only selection. No refit or retuning.
    sg=pd.factorize(d.loc[test,'WIN_MARKET_ID'])[0];base=d.loc[test,'market_probability'].to_numpy();m=models[selected]
    if m['kind']=='market':p=base
    elif m['kind']=='linear':p=probabilities(off[test]+F[test]@np.array(m['weights']),sg)
    else:
        q=gb.predict_proba(Z[test])[:,1];q=q/np.bincount(sg,weights=q)[sg];p=(1-m['blend'])*base+m['blend']*q
    result={'selected_method':selected,'split_races':{name:int(d.loc[mask,'WIN_MARKET_ID'].nunique()) for name,mask in [('train',train),('validation',valid),('diagnostic',test)]},'warning':'Retrospective feature-development diagnostic; dates already exposed to V5. Not fresh out-of-sample proof.'}
    tables={}
    for name,prob in [('market',base),('selected',p)]:
        result[name],table=metrics(d[test],prob);tables[name]=table;table.to_csv(OUT/f'diagnostic_{name}_races.csv',index=False)
    diff=(tables['selected'].log_loss-tables['market'].log_loss).groupby(tables['market'].date).agg(['sum','count']);rng=np.random.default_rng(600);draw=rng.integers(0,len(diff),(2000,len(diff)));deltas=diff['sum'].to_numpy()[draw].sum(1)/diff['count'].to_numpy()[draw].sum(1)
    result['paired_log_loss_difference']={'selected_minus_market':float((tables['selected'].log_loss-tables['market'].log_loss).mean()),'day_bootstrap_95':np.quantile(deltas,[.025,.975]).tolist()}
    dump('evaluation.json',result)
    pred=d.loc[test,['date','TRACK','RACE_NO','WIN_MARKET_ID','TAB_NUMBER','SELECTION_NAME','market_probability','y']].copy();pred['selected_probability']=p;pred.to_csv(OUT/'diagnostic_predictions.csv.gz',index=False)
    return result
