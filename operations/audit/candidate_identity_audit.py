"""Audit candidate IDs and event participation; never approve name-only joins."""
import hashlib,json
from pathlib import Path
import pandas as pd
from operations.audit.verification import name


def candidates(directory, runners):
    files=sorted(Path(directory).glob('*.canonical.csv.gz'))
    if not files:raise ValueError('No independently hash-verified canonical histories supplied')
    d=pd.concat([pd.read_csv(p,dtype={'SELECTION_ID':str,'WIN_MARKET_ID':str}) for p in files],ignore_index=True)
    # Only candidate discovery tolerates a terminal country suffix; accepted
    # identity resolution still requires exact same-race evidence and attributes.
    import re
    key=lambda s:name(re.sub(r'\s*\((?:AUS|NZ|GB|IRE|FR|USA)\)\s*$','',s,flags=re.I))
    d['candidate_name']=d.SELECTION_NAME.map(key)
    records=[]
    for runner in runners:
        match=d[d.candidate_name.eq(key(runner['horse']))]
        possible=[]
        for ident,g in match.groupby('SELECTION_ID'):
            possible.append(dict(betfair_selection_id=ident,first_seen=g.date.min(),last_seen=g.date.max(),
                appearances=len(g),event_footprints=[dict(date=str(r.date),jurisdiction=str(r.STATE_CODE),meeting=str(r.TRACK),race=str(r.RACE_NO),distance_m=int(r.DISTANCE),market_id=str(r.WIN_MARKET_ID),saddlecloth=int(r.TAB_NUMBER)) for r in g.sort_values('date').tail(3).itertuples()]))
        records.append(dict(number=runner['number'],horse=runner['horse'],candidate_ids=len(possible),candidates=possible,
            accepted_identity_links=0,reason='Candidate names are not registration evidence; require independently verified same-event participation and source IDs'))
    return dict(schema='monty.identity.candidates.v1',source_months=len(files),retained_races=int(d.WIN_MARKET_ID.nunique()),retained_runners=len(d),
        accepted_identity_links=0,model_inputs_modified=False,records=records,
        source_canonical_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
