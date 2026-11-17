"""Training and validation-only candidate selection; unchanged research grid."""
import numpy as np,pandas as pd
from scipy.optimize import minimize
from sklearn.ensemble import HistGradientBoostingClassifier
import sklearn
from .config import OUT,dump
from .model_math import probabilities,objective,metrics

def fit_candidates(d,X,names,registry):
    train=d.date.le('2025-03-31').to_numpy();valid=d.date.between('2025-04-01','2025-04-30').to_numpy();test=d.date.ge('2025-05-01').to_numpy()
    # Retain NaNs in exported features. Impute only in the numeric model matrix, with explicit missing flags.
    finite=np.isfinite(X);count=finite[train].sum(0);med=np.array([np.nanmedian(X[train,i]) if count[i] else 0 for i in range(X.shape[1])]);Xi=np.where(finite,X,med)
    coverage={n:dict(known_rows=int(finite[:,i].sum()),fraction=float(finite[:,i].mean()),training_known_rows=int(count[i])) for i,n in enumerate(names)};dump('feature_coverage.json',coverage)
    active=(count>0)&(np.std(Xi[train],axis=0)>1e-10);active_names=[n for n,k in zip(names,active) if k]
    Z=np.column_stack([Xi[:,active],(~finite[:,active]).astype(float)]);znames=active_names+[n+'_missing' for n in active_names]
    mean=Z[train].mean(0);scale=Z[train].std(0);scale[scale<1e-8]=1;Z=(Z-mean)/scale
    # Log market is already an offset; prevent duplicate free market scale in the form residual model.
    formidx=[i for i,n in enumerate(znames) if n!='log_market_probability'];F=Z[:,formidx]
    off=np.log(d.market_probability.to_numpy());y=d.y.to_numpy(float);tg=pd.factorize(d.loc[train,'WIN_MARKET_ID'])[0];vg=pd.factorize(d.loc[valid,'WIN_MARKET_ID'])[0]
    validation={'market':metrics(d[valid],d.loc[valid,'market_probability'].to_numpy())[0]};models={'market':dict(kind='market')}
    for pen in [.01,.1,1.]:
        fit=minimize(objective,np.zeros(F.shape[1]),args=(F[train],off[train],y[train],tg,pen),jac=True,method='L-BFGS-B',options={'maxiter':200,'gtol':1e-7})
        if not fit.success:raise RuntimeError(fit.message)
        name=f'linear_{pen}';models[name]=dict(kind='linear',weights=fit.x.tolist());validation[name]=metrics(d[valid],probabilities(off[valid]+F[valid]@fit.x,vg))[0]
    gb=HistGradientBoostingClassifier(**registry['boosting']).fit(Z[train],y[train])
    q=gb.predict_proba(Z[valid])[:,1];q=q/np.bincount(vg,weights=q)[vg]
    for blend in [.1,.25]:
        name=f'boost_blend_{blend}';models[name]=dict(kind='boost',blend=blend);p=(1-blend)*d.loc[valid,'market_probability'].to_numpy()+blend*q;validation[name]=metrics(d[valid],p)[0]
    selected=min(validation,key=lambda n:validation[n]['log_loss'])
    frozen=dict(input_feature_names=list(names),sklearn_version=sklearn.__version__,selected=selected,models=models,validation=validation,numeric_feature_names=znames,linear_feature_names=[znames[i] for i in formidx],imputation_medians=med.tolist(),mean=mean.tolist(),scale=scale.tolist())
    dump('frozen_model.json',frozen)
    import pickle
    with (OUT/'boosting_model.pkl').open('wb') as f:pickle.dump(gb,f)
    return dict(train=train,valid=valid,test=test,models=models,selected=selected,gb=gb,off=off,F=F,Z=Z,frozen=frozen)
