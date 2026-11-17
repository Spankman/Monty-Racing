import numpy as np,pandas as pd

def probabilities(scores,groups):
    maxima=np.full(groups.max()+1,-np.inf);np.maximum.at(maxima,groups,scores)
    e=np.exp(scores-maxima[groups]);return e/np.bincount(groups,weights=e)[groups]


def objective(w,X,offset,y,g,penalty):
    p=probabilities(offset+X@w,g);nr=g.max()+1
    loss=-np.log(np.maximum(p[y==1],1e-15)).mean()+penalty*np.dot(w,w)/2
    grad=X.T@(p-y)/nr+penalty*w
    return loss,grad


def metrics(d,p):
    z=d[['date','WIN_MARKET_ID','TRACK','STATE_CODE','RACE_NO','race_index','y','BEST_AVAIL_BACK_AT_SCHEDULED_OFF','WIN_BSP']].copy()
    z['p']=p;z['rank']=z.groupby('race_index').p.rank(method='first',ascending=False)
    z['square']=(p-z.y)**2;z['win_ll']=np.where(z.y.eq(1),-np.log(np.maximum(p,1e-15)),0)
    picks=z[z['rank'].eq(1)].copy();winners=z[z.y.eq(1)]
    table=z.groupby('race_index',sort=False).agg(date=('date','first'),market_id=('WIN_MARKET_ID','first'),track=('TRACK','first'),state=('STATE_CODE','first'),log_loss=('win_ll','sum'),brier=('square','sum'))
    table['hit']=picks.set_index('race_index').y
    table['winner_rank']=winners.set_index('race_index')['rank']
    table['quote_proxy_profit_5pct']=picks.set_index('race_index').apply(lambda r:(r.BEST_AVAIL_BACK_AT_SCHEDULED_OFF-1)*.95 if r.y else -1,axis=1)
    n=len(table);h=int(table.hit.sum());rate=h/n;zz=1.96;den=1+zz*zz/n
    centre=(rate+zz*zz/(2*n))/den;half=zz*np.sqrt(rate*(1-rate)/n+zz*zz/(4*n*n))/den
    return dict(races=n,wins=h,strike_rate=rate,strike_wilson_95=[centre-half,centre+half],log_loss=table.log_loss.mean(),brier=table.brier.mean(),winner_among_top4=table.winner_rank.le(4).mean(),quote_proxy_roi_5pct=table.quote_proxy_profit_5pct.mean(),real_bets=0),table


