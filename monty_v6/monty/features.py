"""Prior-day history features; all same-day outcome updates are deferred."""
from collections import defaultdict
from datetime import datetime
import numpy as np,pandas as pd
from .normalization import numeric_class,distance_band

def statistics(events,day,window=None,shrink=5):
    if not events:return (0,.1,0.)
    e=[x for x in events if window is None or day-x[0]<=window]
    n=len(e);w=sum(x[1] for x in e);expected=sum(x[2] for x in e)
    return n,(w+.1*shrink)/(n+shrink),(w-expected)/(n+shrink)


def residual(events,day,window=365,shrink=10):return statistics(events,day,window,shrink)[2]


def build_features(d):
    horse=defaultdict(list);track=defaultdict(list);dist=defaultdict(list);td=defaultdict(list);go=defaultdict(list)
    jockey=defaultdict(list);trainer=defaultdict(list);pair=defaultdict(list);hj=defaultdict(list)
    last={};rows=[];indices=[];names=None
    fieldsize=d.groupby('WIN_MARKET_ID').size().to_dict()
    # All updates occur after the whole local day. Contextual histories use matched metadata only.
    for date,day in d.groupby('date',sort=False):
        ordinal=datetime.fromisoformat(date).toordinal()
        for r in day.itertuples():
            if not r.enriched_eligible:continue
            k=(r.SELECTION_ID,r.name_key);h=horse[k];prev=last.get(k);n,wr,res=statistics(h,ordinal);n365,w365,res365=statistics(h,ordinal,365)
            recent3=h[-3:];recent5=h[-5:];ds=distance_band(r.DISTANCE)
            j=r.jockey if isinstance(r.jockey,str) else '';t=r.trainer if isinstance(r.trainer,str) else '';going=r.going if isinstance(r.going,str) else 'unknown'
            barrier=float(r.barrier) if pd.notna(r.barrier) and r.barrier>0 else np.nan;nf=fieldsize[r.WIN_MARKET_ID];days=ordinal-prev['day'] if prev else np.nan
            bm=numeric_class(r.class_text);lastbm=prev['bm'] if prev else np.nan
            weight=float(r.allocated_weight) if pd.notna(r.allocated_weight) else np.nan
            claim=float(r.claim_kg) if pd.notna(r.claim_kg) and r.claim_kg>=0 else np.nan
            f={'log_market_probability':np.log(r.market_probability),'log_field_size':np.log(nf),'distance_km':r.DISTANCE/1000,'barrier':barrier,'barrier_fraction':barrier/nf,'inside_three':float(barrier<=3) if np.isfinite(barrier) else np.nan,'outside_barrier':float(barrier>nf*.75) if np.isfinite(barrier) else np.nan,'barrier_x_distance':barrier/nf*r.DISTANCE/1000,'observed_starts_log':np.log1p(n),'observed_win_rate':wr,'observed_market_residual':res,'year_starts_log':np.log1p(n365),'year_win_rate':w365,'year_market_residual':res365,'last3_win_rate':(sum(e[1] for e in recent3)+.3)/(len(recent3)+3),'last5_win_rate':(sum(e[1] for e in recent5)+.5)/(len(recent5)+5),'last3_market_residual':sum(e[1]-e[2] for e in recent3)/(len(recent3)+3),'last5_market_residual':sum(e[1]-e[2] for e in recent5)/(len(recent5)+5),'track_win_residual':residual(track[(k,r.TRACK)],ordinal,3650,3),'distance_win_residual':residual(dist[(k,ds)],ordinal,3650,3),'track_distance_residual':residual(td[(k,r.TRACK,ds)],ordinal,3650,3),'going_win_residual':residual(go[(k,going)],ordinal,3650,3) if going!='unknown' else np.nan,'jockey_year_residual':residual(jockey[j],ordinal,365,20) if j else np.nan,'jockey_90d_residual':residual(jockey[j],ordinal,90,20) if j else np.nan,'trainer_year_residual':residual(trainer[t],ordinal,365,20) if t else np.nan,'trainer_90d_residual':residual(trainer[t],ordinal,90,20) if t else np.nan,'jockey_trainer_residual':residual(pair[(j,t)],ordinal,365,10) if j and t else np.nan,'horse_jockey_residual':residual(hj[(k,j)],ordinal,3650,3) if j else np.nan,'days_since_run_log':np.log1p(min(days,730)) if pd.notna(days) else np.nan,'resuming_60d':float(days>=60) if pd.notna(days) else np.nan,'quick_backup_7d':float(days<=7) if pd.notna(days) else np.nan,'distance_change_km':(r.DISTANCE-prev['distance'])/1000 if prev else np.nan,'up_200m':float(r.DISTANCE-prev['distance']>=200) if prev else np.nan,'down_200m':float(prev['distance']-r.DISTANCE>=200) if prev else np.nan,'benchmark_class':bm,'benchmark_class_change':bm-lastbm if np.isfinite(bm) and np.isfinite(lastbm) else np.nan,'jockey_changed':float(j!=prev['jockey']) if j and prev and prev['jockey'] else np.nan,'trainer_changed':float(t!=prev['trainer']) if t and prev and prev['trainer'] else np.nan,'allocated_weight':weight,'claim_kg':claim,'effective_weight':weight-claim if np.isfinite(weight) and np.isfinite(claim) else np.nan,'weight_change':weight-prev['weight'] if prev and np.isfinite(weight) and np.isfinite(prev['weight']) else np.nan}
            for g in ['good','soft','heavy','firm','synthetic','unknown']:f['going_'+g]=float(going==g)
            for c in ['age','is_gelding','first_after_gelding','blinkers_first','blinkers_off','tongue_tie_first','winkers_first']:f[c]=float(getattr(r,c)) if pd.notna(getattr(r,c)) else np.nan
            names=list(f);rows.append(list(f.values()));indices.append(r.Index)
        for r in day.itertuples():
            k=(r.SELECTION_ID,r.name_key);e=(ordinal,int(r.y),float(r.market_probability));horse[k].append(e)
            ds=distance_band(r.DISTANCE);track[(k,r.TRACK)].append(e)
            if ds>=0:dist[(k,ds)].append(e);td[(k,r.TRACK,ds)].append(e)
            j=r.jockey if isinstance(r.jockey,str) else '';t=r.trainer if isinstance(r.trainer,str) else '';going=r.going if isinstance(r.going,str) else 'unknown'
            if going!='unknown':go[(k,going)].append(e)
            if j:jockey[j].append(e);hj[(k,j)].append(e)
            if t:trainer[t].append(e)
            if j and t:pair[(j,t)].append(e)
            last[k]=dict(day=ordinal,distance=r.DISTANCE,bm=numeric_class(r.class_text),jockey=j,trainer=t,weight=float(r.allocated_weight) if pd.notna(r.allocated_weight) else np.nan)
    X=np.array(rows,float);return d.loc[indices].reset_index(drop=True),X,names


