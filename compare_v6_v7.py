"""Compare timestamped V6 and V7 selections, never infer absent V6 picks.

Both inputs must contain meeting,race,number,horse,selection,captured_at.
Each capture timestamp must be timezone-aware. Comparison is research-only.
"""
import argparse, json, re
from pathlib import Path
import pandas as pd

KEY=['meeting','race']
REQUIRED=KEY+['number','horse','selection','captured_at']
TZ=re.compile(r'(?:Z|[+-][0-9]{2}:[0-9]{2})$')

def read(path, version):
    df=pd.read_csv(path,dtype={'meeting':str,'race':str,'number':str,'horse':str,'selection':str,'captured_at':str})
    if not set(REQUIRED).issubset(df):raise ValueError(f'{version} missing required columns')
    if df.empty:raise ValueError(f'{version} missing selections')
    if df[REQUIRED].isna().any().any():raise ValueError(f'{version} incomplete selections')
    if not df.captured_at.map(lambda v:bool(TZ.search(str(v)))).all():raise ValueError(f'{version} missing timestamp offset')
    if pd.to_datetime(df.captured_at,utc=True,errors='coerce').isna().any():raise ValueError(f'{version} invalid timestamp')
    if df.duplicated(KEY+['selection']).any():raise ValueError(f'{version} duplicate selection label')
    if df.duplicated(KEY+['number']).any():raise ValueError(f'{version} duplicate horse')
    return df

def compare(v6,v7):
    a=read(v6,'V6');b=read(v7,'V7')
    x=a.merge(b,on=KEY+['selection'],how='outer',suffixes=('_v6','_v7'),indicator=True)
    x['comparison']=x['_merge'].map({'both':'DIFFERENT','left_only':'V6 ONLY','right_only':'V7 ONLY'}).astype(str)
    both=x['_merge'].eq('both')
    same=both & x.number_v6.eq(x.number_v7) & x.horse_v6.str.casefold().eq(x.horse_v7.str.casefold())
    x.loc[same,'comparison']='SAME'
    return x.drop(columns=['_merge'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('v6');p.add_argument('v7');p.add_argument('--output',default='v6_v7_comparison.csv')
    a=p.parse_args();x=compare(a.v6,a.v7);Path(a.output).parent.mkdir(parents=True,exist_ok=True);x.to_csv(a.output,index=False)
    print(json.dumps({'rows':len(x),'same':int((x.comparison=='SAME').sum()),'different':int((x.comparison=='DIFFERENT').sum()),'status':'AUDIT COMPARISON ONLY'}))
