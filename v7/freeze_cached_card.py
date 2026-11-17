"""Explicit cached AU pilot. Does not refresh odds or assert current scratchings."""
import argparse,json,re,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from .core import predict
from .candidate2 import score
from .shadow import freeze


def run(inputs,cards,v6_root,c1_path,c2_path,out):
    from monty_v6.monty.scoring import score_features
    from monty_v6.monty.integrity import verify_artifacts
    verify_artifacts(v6_root)
    d=pd.read_csv(inputs);c1=json.loads(c1_path.read_text());c2=json.loads(c2_path.read_text())
    names=c1['names'];norm=lambda s:re.sub('[^a-z0-9]','',str(s).lower())
    starts={};sources={};urls={}
    tracks={'sandownlakeside':'Sandown','doomben':'Doomben','gawler':'Gawler','warwickfarm':'Warwick Farm','belmont':'Belmont'}
    for path in cards.glob('*.json'):
        c=json.loads(path.read_text());track=tracks.get(norm(c.get('track','')))
        if not track or c.get('date')!='2026-11-18':continue
        key=(track,int(c['raceNumber']));starts[key]=c['startTime'];sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        urls[key]='https://formfav.com/docs/endpoints/form'
        source_names={int(r['number']):norm(r['name']) for r in c['runners']}
        for r in d[(d.meeting==track)&d.race.eq(key[1])].itertuples():
            if source_names.get(int(r.number))!=norm(r.horse):raise ValueError('Cached card runner mismatch')
    ids=d.meeting+'|'+d.race.astype(str);inv=1/d.odds;base=inv/inv.groupby(ids).transform('sum')
    X=np.column_stack([pd.to_numeric(d[n],errors='coerce') if n in d else np.full(len(d),np.nan) for n in names])
    X[:,names.index('log_market_probability')]=np.log(base);X[:,names.index('log_field_size')]=np.log(d.groupby(ids).horse.transform('size'))
    v6=score_features(X,names,base,ids,root=v6_root);v7=predict(c1,X,base,ids);v2=score(c2,X,base,ids)
    rows=[]
    for i,r in d.iterrows():
        key=(r.meeting,int(r.race));start=starts[key]
        codes={'Sandown':('SANDOWN','SAN'),'Doomben':('DOOMBEN','DBN'),'Gawler':('GAWLER','GAW'),'Warwick Farm':('WARWICK-FARM','WFM'),'Belmont':('BELMONT','BEL')}
        venue,code=codes[r.meeting]
        rows.append(dict(race_id='2026-11-18|AU|'+ids[i],runner_id=str(int(r.number)),horse=r.horse,
            country='AU',number=int(r.number),odds=float(r.odds),odds_captured_at_utc=r.captured_at_utc,
            source_url=f'https://www.tab.com.au/racing/2026-11-18/{venue}/{code}/R/{int(r.race)}/Win',
            scheduled_start_utc=start,start_source=urls[key],v6_probability=float(v6[i]),v7_probability=float(v7[i]),candidate2_probability=float(v2[i]),market_probability=float(base[i]),
            known_features=int(np.isfinite(X[i]).sum()),field_snapshot='Previously TAB-reconciled cached active field; not refreshed at freeze'))
    models={label:hashlib.sha256(p.read_bytes()).hexdigest() for label,p in [('V6 frozen',v6_root/'results/frozen_model.json'),('V7 Candidate 1',c1_path),('V7 Candidate 2',c2_path)]}
    models['candidate2_form_weight']=c2['form_weight'];models['input_sha256']=hashlib.sha256(inputs.read_bytes()).hexdigest()
    models['card_sha256']=sources
    result=freeze(rows,out,models)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['inputs','cards','v6-root','c1-model','c2-model','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.inputs,a.cards,a.v6_root,a.c1_model,a.c2_model,a.output),indent=2))
