"""Audit availability and provenance of expert sources without inventing tips.

Input CSV contains source,source_url,status,attempted_at,details.
Status is one of located, captured, verified, rejected, unavailable.
This is a discovery audit, not a live web collector or model input.
"""
import argparse,json,re
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd

STATUSES={'located','captured','verified','rejected','unavailable'}
def summarize(path):
    df=pd.read_csv(path,dtype=str).fillna('')
    required={'source','source_url','status','attempted_at','details'}
    if not required.issubset(df):raise ValueError('Source register missing fields')
    if df.empty:return {'sources':0,'status_counts':{},'records':[]}
    if df.source.str.strip().eq('').any() or (~df.status.isin(STATUSES)).any():
        raise ValueError('Invalid source or status')
    if not df.source_url.map(lambda x:urlparse(x).scheme=='https' and bool(urlparse(x).netloc)).all():
        raise ValueError('Source URL must be HTTPS')
    tz=re.compile(r'(?:Z|[+-][0-9]{2}:[0-9]{2})$')
    if not df.attempted_at.map(lambda x:bool(tz.search(x))).all():
        raise ValueError('Attempt timestamps require timezone')
    times=pd.to_datetime(df.attempted_at,utc=True,errors='coerce')
    if times.isna().any():raise ValueError('Invalid attempt timestamps')
    if df.duplicated(['source','source_url','attempted_at']).any():
        raise ValueError('Duplicate source discovery attempts')
    return {'sources':int(df.source.nunique()),
      'status_counts':{str(k):int(v) for k,v in df.status.value_counts().items()},
      'records':df.to_dict(orient='records'),
      'note':'Source discovery alone is not evidence of verified pre-race tips'}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('register');p.add_argument('--output',default='expert_source_audit.json')
    a=p.parse_args()
    result=summarize(a.register)
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sources':result['sources'],'status_counts':result['status_counts']}))
