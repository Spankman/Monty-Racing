"""Prepare auditable public tipster selections for Monty V7 shadow blend.

Input is an independently captured source CSV with columns:
meeting,race,number,horse,source,source_url,captured_at,race_off_at.
Source capture must be contemporaneous and pre-off; never backdate.
Model field and score CSVs must be from the same race-day snapshot.
"""
import argparse
from urllib.parse import urlparse
import pandas as pd
from monty_v7_shadow_blend import KEY

def prepare(scores_path, tips_path, output_path):
    scores=pd.read_csv(scores_path,dtype={k:str for k in KEY})
    tips=pd.read_csv(tips_path,dtype={k:str for k in KEY})
    required=set(KEY+['horse','source','source_url','captured_at','race_off_at'])
    if not required.issubset(tips.columns):raise ValueError('Missing tip provenance columns')
    if tips.empty:
        pd.DataFrame(columns=KEY+['expert_score','source','captured_at','race_off_at']).to_csv(output_path,index=False)
        return 0
    if tips[list(required)].isna().any().any() or tips[list(required)].astype(str).apply(lambda c:c.str.strip().eq('')).any().any():
        raise ValueError('Empty tip provenance')
    if not tips.source_url.map(lambda x:urlparse(x).scheme=='https' and bool(urlparse(x).netloc)).all():
        raise ValueError('Source URLs must be HTTPS')
    if tips.duplicated(KEY+['source']).any():raise ValueError('Duplicate source per runner')
    if scores.duplicated(KEY).any():raise ValueError('Duplicate model runner')
    joined=tips.merge(scores[KEY+['horse']],on=KEY,how='left',validate='many_to_one',suffixes=('','_model'),indicator=True)
    if (joined._merge!='both').any() or not joined.horse_model.fillna('').str.casefold().eq(joined.horse.str.casefold()).all():
        raise ValueError('Tip horse identity does not match model field')
    # A source's listed picks receive equal source-local mass. The blend
    # subsequently gives each distinct source equal weight.
    tips['expert_score']=1.0
    out=tips[KEY+['expert_score','source','captured_at','race_off_at']]
    out.to_csv(output_path,index=False)
    return len(out)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('scores');p.add_argument('tips');p.add_argument('--output',default='expert_scores.csv')
    a=p.parse_args()
    print({'verified_field_matches':prepare(a.scores,a.tips,a.output)})
