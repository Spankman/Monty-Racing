"""Merge authenticated FormFav race-card captures into existing complete fields.

No network, credentials, predictions or aggregate-to-V6-history substitutions.
"""
import numpy as np
import pandas as pd
from monty.normalization import normal,condition,numeric_class
import copy,re
from urllib.parse import urlparse

def reconcile_tab(card,observation):
    """Apply a complete rendered TAB field, preserving disagreements in an audit."""
    u=urlparse(observation['url']);parts=u.path.strip('/').split('/')
    if u.hostname!='www.tab.com.au' or len(parts)<6 or parts[0]!='racing' or parts[4]!='R':
        raise ValueError('Invalid TAB observation URL')
    if parts[1]!=card['date'] or int(parts[5])!=int(card['raceNumber']):
        raise ValueError('TAB race/date disagreement')
    # Standard TAB paths are racing/date/venue/code/R/race[/market].
    venue=parts[2]
    aliases={'SANDOWN':'sandownlakeside','WARWICK-FARM':'warwickfarm',
             'DOOMBEN':'doomben','GAWLER':'gawler','BELMONT':'belmont'}
    if aliases.get(venue)!=normal(card['track']):raise ValueError('TAB meeting disagreement')
    rendered={};audit=[]
    for row in observation['runners']:
        match=re.fullmatch(r'runner-number-(\d+)',row['id'])
        identity=re.fullmatch(r'(.+?)\s*\((\d+)\)',row['name'].split('\n')[0])
        if not match or not identity:raise ValueError('Unreadable TAB runner identity')
        number=int(match[1])
        if number in rendered:raise ValueError('Duplicate TAB runner')
        price=row['fixed_win'].strip()
        if price!='SCR' and (not np.isfinite(float(price)) or float(price)<=1):
            raise ValueError('Invalid TAB fixed win quote')
        rendered[number]={'name':identity[1].strip(),'barrier':int(identity[2]),
                          'scratched':price=='SCR','odds':np.nan if price=='SCR' else float(price)}
    if len({int(r['number']) for r in card['runners']})!=len(card['runners']):
        raise ValueError('Duplicate FormFav runner')
    if set(rendered)!={int(r['number']) for r in card['runners']}:
        raise ValueError('TAB/FormFav complete card disagreement')
    updated=copy.deepcopy(card)
    for runner in updated['runners']:
        r=rendered[int(runner['number'])]
        if normal(runner['name'])!=normal(r['name']):raise ValueError('TAB/FormFav runner name disagreement')
        if bool(runner.get('scratched',False))!=r['scratched']:
            audit.append({'number':runner['number'],'horse':runner['name'],
                          'formfav_scratched':runner.get('scratched',False),'tab_scratched':r['scratched']})
        runner['scratched']=r['scratched'];runner['barrier']=r['barrier']
    going=re.search(r'\b(Good|Soft|Heavy|Firm|Synthetic)\s*\((\d+)\)',observation.get('main_text',''))
    if going:updated['condition']=going[1]+' '+going[2]
    return updated,rendered,audit

def merge_card(frame,card):
    if card.get('abandoned'):raise ValueError('Race abandoned')
    if not isinstance(card.get('runners'),list) or not card['runners']:
        raise ValueError('Missing race-card field')
    numbers=[str(x['number']) for x in card['runners']]
    if len(numbers)!=len(set(numbers)):raise ValueError('Duplicate saddlecloth in race card')
    active={str(x['number']):x for x in card['runners'] if not x.get('scratched',False)}
    result=frame[frame.number.astype(str).isin(active)].copy()
    if set(result.number.astype(str))!=set(active):raise ValueError('Active field lacks saved odds')
    distance=card.get('distance','')
    import re
    match=re.fullmatch(r'(\d+)m',str(distance).replace(' ',''))
    if not match:raise ValueError('Unknown distance unit')
    metres=int(match[1]);going=condition(card.get('condition','unknown'))
    for idx,row in result.iterrows():
        runner=active[str(row.number)]
        if normal(row.horse)!=normal(runner['name']):raise ValueError('Runner identity disagreement')
        old_distance=row.get('distance_km',np.nan)*1000
        if pd.notna(row.get('distance_change_km',np.nan)):
            previous_distance=old_distance-row.distance_change_km*1000
            delta=metres-previous_distance
            result.loc[idx,'distance_change_km']=delta/1000
            result.loc[idx,'up_200m']=float(delta>=200)
            result.loc[idx,'down_200m']=float(delta<=-200)
        old_class=row.get('benchmark_class',np.nan)
        bm=numeric_class(card.get('raceClass',''))
        if pd.notna(row.get('benchmark_class_change',np.nan)):
            previous_class=old_class-row.benchmark_class_change
            result.loc[idx,'benchmark_class_change']=bm-previous_class
        result.loc[idx,'benchmark_class']=bm
        result.loc[idx,'distance_km']=metres/1000
        for f in ['barrier','age']:
            result.loc[idx,f]=runner.get(f,np.nan)
        result.loc[idx,'allocated_weight']=runner.get('weight',np.nan)
        result.loc[idx,'claim_kg']=runner.get('claim',0)
        result.loc[idx,'effective_weight']=runner.get('weight',np.nan)-runner.get('claim',0)
        result.loc[idx,'is_gelding']=float(str(runner['sex']).lower()=='gelding') if 'sex' in runner else np.nan
        for g in ['good','soft','heavy','firm','synthetic','unknown']:
            result.loc[idx,'going_'+g]=float(going==g)
    result['barrier_fraction']=result.barrier/len(result)
    result['inside_three']=np.where(result.barrier.notna(),(result.barrier<=3).astype(float),np.nan)
    result['outside_barrier']=np.where(result.barrier.notna(),(result.barrier>len(result)*.75).astype(float),np.nan)
    result['barrier_x_distance']=result.barrier/len(result)*metres/1000
    return result
