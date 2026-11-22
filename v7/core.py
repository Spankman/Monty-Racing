"""Race-conditional ridge model, chronological calibration and probability tools."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar


def probability(scores, races):
    scores = np.asarray(scores, float)
    g = pd.factorize(np.asarray(races))[0]
    if not len(g) or (g < 0).any() or not np.isfinite(scores).all():
        raise ValueError('Invalid scores/race identities')
    maxima = np.full(g.max()+1, -np.inf)
    np.maximum.at(maxima, g, scores)
    e = np.exp(scores-maxima[g])
    return e / np.bincount(g, weights=e)[g]


def logloss(y, p):
    return float(-np.log(np.maximum(np.asarray(p)[np.asarray(y)==1], 1e-15)).mean())


def fit(X, y, market, races, names, penalty):
    """Every transform fitted on training rows only; no outcome-derived inputs."""
    X = np.asarray(X, float)
    finite = np.isfinite(X)
    med = np.array([np.median(X[finite[:,i],i]) if finite[:,i].any() else 0.
                    for i in range(X.shape[1])])
    filled = np.where(finite, X, med)
    active = (filled.std(0) > 1e-10) & (np.array(names) != 'log_market_probability')
    Z = np.column_stack([filled[:,active], (~finite[:,active]).astype(float)])
    mean, scale = Z.mean(0), Z.std(0)
    scale[scale < 1e-8] = 1
    Z = (Z-mean)/scale
    market=np.asarray(market,float);y=np.asarray(y,float)
    if not np.isfinite(market).all() or (market<=0).any() or not np.isin(y,[0,1]).all():
        raise ValueError('Invalid market probabilities or win labels')
    g=pd.factorize(np.asarray(races))[0]
    if not np.allclose(np.bincount(g,weights=market),1) or not np.allclose(np.bincount(g,weights=y),1):
        raise ValueError('Full normalized single-winner races required')
    off = np.log(market)
    nr = len(set(races))
    def objective(w):
        p = probability(off+Z@w, races)
        return logloss(y,p)+penalty*(w@w)/2, Z.T@(p-y)/nr+penalty*w
    result = minimize(objective, np.zeros(Z.shape[1]), jac=True, method='L-BFGS-B',
                      options={'maxiter':300, 'gtol':1e-7})
    if not result.success:
        raise ValueError('Fit failed: '+str(result.message))
    return dict(names=list(names), medians=med.tolist(), active=active.tolist(),
                mean=mean.tolist(), scale=scale.tolist(), weights=result.x.tolist(),
                penalty=float(penalty), temperature=1.)


def predict(model, X, market, races):
    X = np.asarray(X,float)
    if X.ndim != 2 or X.shape[1] != len(model['names']):
        raise ValueError('Feature schema dimensions mismatch')
    market=np.asarray(market,float)
    g=pd.factorize(np.asarray(races))[0]
    if len(g)!=len(X) or (g<0).any() or not np.isfinite(market).all() or (market<=0).any() or not np.allclose(np.bincount(g,weights=market),1):
        raise ValueError('Invalid full-field market')
    finite = np.isfinite(X)
    filled = np.where(finite,X,np.array(model['medians']))
    active = np.array(model['active'])
    Z = np.column_stack([filled[:,active], (~finite[:,active]).astype(float)])
    Z = (Z-np.array(model['mean']))/np.array(model['scale'])
    return probability((np.log(market)+Z@np.array(model['weights']))/model['temperature'],races)


def calibrate(p, y, races):
    """Temperature selected on disjoint earlier calibration races, never test."""
    result = minimize_scalar(lambda t: logloss(y,probability(np.log(p)/t,races)),
                             bounds=(.5,2.),method='bounded')
    if not result.success:
        raise ValueError('Calibration failed')
    return float(result.x)


def exotics(p, places=3):
    """Plackett-Luce/Harville structural estimates, NOT calibrated place forecasts."""
    p = np.asarray(p,float)
    if p.ndim!=1 or len(p)<2 or not np.isfinite(p).all() or (p<=0).any() or not np.isclose(p.sum(),1):
        raise ValueError('Expected positive normalized full-field win probabilities')
    if places not in (2,3) or places>len(p):
        raise ValueError('Only top two/three estimates supported')
    q = np.zeros((len(p),len(p)))
    top = p.copy()
    for i in range(len(p)):
        for j in range(len(p)):
            if i==j: continue
            joint = p[i]*p[j]/(1-p[i])
            q[i,j] += joint
            top[j] += joint
            if places==3:
                for k in range(len(p)):
                    if k in (i,j): continue
                    top[k] += joint*p[k]/max(1-p[i]-p[j],1e-15)
    return top, q+q.T


def blend_expert(model_p, expert_p, weight=0.):
    """Default zero; external probabilities must cover the same complete field.

    A nonzero weight is experimental and must be chosen using prior validation,
    not discretionary tip votes or today's outcomes.
    """
    p=np.asarray(model_p,float); q=np.asarray(expert_p,float)
    if p.shape!=q.shape or not 0<=weight<=.25 or not np.isfinite(q).all() or (q<0).any() or not np.isclose(q.sum(),1) or (p<0).any() or not np.isclose(p.sum(),1):
        raise ValueError('Invalid full-field expert probabilities/weight')
    return (1-weight)*p+weight*q


def value_decision(p, odds, commission=.05, minimum_edge=.05):
    if not (0<=p<=1 and np.isfinite(odds) and odds>1 and 0<=commission<1 and minimum_edge>=0):
        raise ValueError('Invalid probability/quote/commission/edge')
    edge=p*(odds-1)*(1-commission)-(1-p)
    return {'net_edge':float(edge),'decision':'VALUE_CANDIDATE' if edge>=minimum_edge else 'NO BET',
            'fair_decimal_odds':1/p if p else None}
