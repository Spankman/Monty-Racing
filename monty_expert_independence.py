"""Prevent syndicated expert opinions from being counted as independent votes.

A website is not an independent analyst. This module accepts verified tip
records with author and publisher fields and groups identical author identities.
Unknown authors are conservatively grouped by normalized pick fingerprints
within a race, rather than being awarded independent consensus votes.
"""
import argparse,json,re
from pathlib import Path
import pandas as pd

KEY=['meeting','race','number']
def normalize(value):
    return re.sub(r'[^a-z0-9]+',' ',str(value).casefold()).strip()

def audit(path):
    df=pd.read_csv(path,dtype={k:str for k in KEY}).fillna('')
    needed=set(KEY+['source','author'])
    if not needed.issubset(df.columns):raise ValueError('Missing source/author fields')
    if df.empty:return {'races':[],'note':'No expert records'}
    if df[list(KEY)+['source']].astype(str).apply(lambda s:s.str.strip().eq('')).any().any():
        raise ValueError('Blank runner/source identity')
    df['author_key']=df.author.map(normalize)
    df['source_key']=df.source.map(normalize)
    rows=[]
    for (meeting,race),g in df.groupby(['meeting','race'],sort=True):
        # Each named author is one independent opinion, irrespective of the
        # number of sites publishing it. Unknown author/source pairs with
        # identical race picks are treated as one provisional opinion.
        identities={}
        for author,group in g[g.author_key!=''].groupby('author_key'):
            identities['author:'+author]=sorted(group.number.unique().tolist())
        unknown=g[g.author_key=='']
        fingerprints={}
        for source,group in unknown.groupby('source_key'):
            fingerprint=tuple(sorted(group.number.unique().tolist()))
            fingerprints.setdefault(fingerprint,[]).append(source)
        for i,(fingerprint,sources) in enumerate(sorted(fingerprints.items())):
            identities['unknown_group:'+str(i)]=list(fingerprint)
        rows.append({'meeting':meeting,'race':race,
            'published_sources':int(g.source_key.nunique()),
            'provisional_independent_opinions':len(identities),
            'named_authors':sorted(g.loc[g.author_key!='','author_key'].unique().tolist()),
            'warning':'Unknown-author duplicates grouped by identical picks; independence still requires manual evidence'})
    return {'races':rows,'note':'Audit only; not a verified weight or betting recommendation'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('tips');p.add_argument('--output',default='expert_independence.json')
    a=p.parse_args()
    report=audit(a.tips)
    Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'races':len(report['races'])}))
