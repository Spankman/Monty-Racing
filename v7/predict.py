"""Explicit V7 research inference; this is not the V6 operational entry point."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import predict,exotics,value_decision
from .candidate2 import score as score_candidate2
from .evidence import blackbook_matches


def run(model_path,features_path,out):
    config=json.loads(model_path.read_text())
    candidate2='candidate1_model' in config
    m=config['candidate1_model'] if candidate2 else config
    d=pd.read_csv(features_path,dtype={'race_id':str,'runner_id':str})
    needed={'race_id','runner_id','horse','date','country','fixed_win_odds','source_url'}
    if not needed.issubset(d):raise ValueError('Missing required field/quote provenance columns')
    if d.empty or d[list(needed)].isna().any().any() or d.duplicated(['race_id','runner_id']).any():raise ValueError('Incomplete or duplicate field records')
    if not d.country.isin(['AU','NZ']).all():raise ValueError('Other jurisdictions need explicit validation')
    if not d.groupby('race_id').date.nunique().eq(1).all() or not d.groupby('race_id').country.nunique().eq(1).all():raise ValueError('Conflicting race metadata')
    if (d.groupby('race_id').size()<3).any():raise ValueError('Need at least three active runners')
    if (d.date<=m['calibration_end']).any():raise ValueError('Inference must follow model calibration period')
    odds=pd.to_numeric(d.fixed_win_odds,errors='coerce')
    if not np.isfinite(odds).all() or (odds<=1).any():raise ValueError('Invalid fixed win quote')
    # Require explicit attestation that scratched runners were excluded and field checked.
    if 'field_verified' not in d or not d.field_verified.eq(True).all():raise ValueError('Complete active field verification required')
    inv=1/odds;base=inv/inv.groupby(d.race_id).transform('sum')
    X=np.column_stack([pd.to_numeric(d[n],errors='coerce') if n in d else np.full(len(d),np.nan) for n in m['names']])
    # Current market and field size are deterministic contemporaneous inputs.
    for name,values in [('log_market_probability',np.log(base)),('log_field_size',np.log(d.groupby('race_id').runner_id.transform('size')))]:
        if name in m['names']:X[:,m['names'].index(name)]=values
    d['v7_win_probability']=score_candidate2(config,X,base,d.race_id) if candidate2 else predict(m,X,base,d.race_id)
    d['research_model']='Candidate 2' if candidate2 else 'Candidate 1'
    d['known_feature_count']=np.isfinite(X).sum(1)
    d['within_race_rank']=d.groupby('race_id').v7_win_probability.rank(method='first',ascending=False).astype(int)
    d['status']='EXPERIMENTAL_V7_NOT_APPROVED_REPLACEMENT'
    d['country_warning']=np.where(d.country.eq('NZ'),'NZ_NOT_VALIDATED','AU_RETROSPECTIVE_ONLY')
    d['estimated_top3_probability']=np.nan;pairs=[]
    for race,g in d.groupby('race_id',sort=False):
        top,q=exotics(g.v7_win_probability.to_numpy(),3);d.loc[g.index,'estimated_top3_probability']=top
        rows=list(g.itertuples())
        for i in range(len(rows)):
            for j in range(i+1,len(rows)):
                pairs.append(dict(race_id=race,runner_a=rows[i].runner_id,runner_b=rows[j].runner_id,
                    estimated_quinella_probability=float(q[i,j]),fair_decimal_odds=float(1/q[i,j]),
                    status='UNCALIBRATED_HARVILLE_ESTIMATE'))
    decisions=[value_decision(p,o) for p,o in zip(d.v7_win_probability,odds)]
    d['research_value_label']=[x['decision'] for x in decisions];d['net_edge']=[x['net_edge'] for x in decisions]
    # Deployment remains NO BET until V7 is validated and approved separately.
    d['deployment_decision']='NO BET — V7 UNAPPROVED'
    out.mkdir(parents=True,exist_ok=True);d.to_csv(out/'v7_research_scores.csv',index=False)
    pd.DataFrame(pairs).to_csv(out/'quinella_estimates.csv',index=False)
    (out/'blackbook_next_starts.json').write_text(json.dumps(blackbook_matches(d.to_dict('records')),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--features',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.model,a.features,a.output)
