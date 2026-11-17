"""Validate public Hub metadata against retained Betfair market identities.

No price or outcome substitution; extra metadata entries remain outside the
retained market. This source is unsupported and incomplete.
"""
from datetime import datetime
import re
import pandas as pd
from monty.normalization import normal,clean_person

def match_metadata(rows,payload):
    if rows.empty or rows.WIN_MARKET_ID.nunique()!=1:raise ValueError('One retained market required')
    market=str(rows.iloc[0].WIN_MARKET_ID)
    if payload.get('raceEventId')!='1.'+market:raise ValueError('Market identity mismatch')
    date=datetime.strptime(payload['day'],'%d-%m-%Y').strftime('%Y-%m-%d')
    if rows.date.nunique()!=1 or rows.iloc[0].date!=date:raise ValueError('Historical date mismatch')
    if any(normal(x)!=normal(payload.get('venueName')) for x in rows.TRACK):raise ValueError('Historical venue mismatch')
    source=payload.get('runners',[]);ids=[str(r['selectionId']) for r in source]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate metadata identity')
    indexed=dict(zip(ids,source));matched={}
    for row in rows.itertuples():
        runner=indexed.get(str(row.SELECTION_ID))
        if runner is None or normal(runner.get('runnerName'))!=normal(row.SELECTION_NAME):
            raise ValueError('Retained runner identity mismatch')
        matched[str(row.SELECTION_ID)]=runner
    return matched,sorted(set(indexed)-set(matched))

def jockey_change(previous,current,tab_name_cell):
    """Return unknown for abbreviations, absent bookings or nonmatching TAB evidence."""
    def tokens(s):return re.findall(r'[A-Za-z]+',str(s))
    a=tokens(previous);b=tokens(current)
    if len(a)<2 or len(b)<2 or len(a[0])<3 or len(b[0])<3:return None
    if not clean_person(previous) or not clean_person(current):return None
    booking=normal(str(tab_name_cell).split('\n')[1]) if '\n' in str(tab_name_cell) else ''
    expected='j'+normal(b[0][0]+''.join(b[1:]))
    if not booking.startswith(expected):return None
    return float(clean_person(previous)!=clean_person(current))
