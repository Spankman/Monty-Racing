"""Normalize explicitly captured TAB fixed-win fields; no API, login or hidden state.

Capture is a point-in-time observation, not a guarantee that quotes remain available.
TAB form rows remain source observations until joined to V6's retained history.
"""
import argparse
import datetime as dt
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse,unquote
from assess_day import timestamp
from race_day import ROOT
from monty.normalization import condition,numeric_class,normal


def finite(value,label):
    if isinstance(value,bool):raise ValueError('Invalid '+label)
    try:value=float(value)
    except (TypeError,ValueError):raise ValueError('Invalid '+label) from None
    if not math.isfinite(value):raise ValueError('Invalid '+label)
    return value


def normalize(capture):
    url=urlparse(capture['source_url'])
    match=re.fullmatch(r'/racing/(\d{4}-\d{2}-\d{2})/([^/]+)/([^/]+)/R/(\d+)(?:/Win)?/?',url.path)
    if url.scheme!='https' or url.netloc!='www.tab.com.au' or not match or url.query or url.fragment:
        raise ValueError('Expected an observed TAB thoroughbred win race URL')
    date,slug,meeting_code,race=match.groups();dt.date.fromisoformat(date)
    if normal(capture['meeting'])!=normal(unquote(slug)):
        raise ValueError('Meeting name disagrees with TAB URL')
    timestamp(capture['captured_at_utc']);jump=timestamp(capture['jump_time'])
    if jump<=timestamp(capture['captured_at_utc']):raise ValueError('Race already due at capture')
    distance=finite(capture['distance_m'],'distance')
    if distance<=0:raise ValueError('Invalid distance')
    expected=capture['declared_runners']
    rows=capture['runners']
    if not isinstance(expected,int) or isinstance(expected,bool) or expected!=len(rows):
        raise ValueError('Declared runner count differs from captured rows')
    numbers=set();names=set();active=[];scratched=[];source_form={}
    for r in rows:
        number=str(r['number'])
        if not number.isdigit() or int(number)<=0 or number in numbers:raise ValueError('Duplicate/invalid saddlecloth')
        numbers.add(number)
        name=str(r['horse']).strip()
        if not name or name.casefold() in names:raise ValueError('Duplicate/missing horse name')
        names.add(name.casefold())
        price=r['fixed_win_text'].strip()
        # SCR must be observed in the fixed-win cell; absent/closed prices never imply scratching.
        if price=='SCR':scratched.append(number);continue
        odds=finite(price,'fixed win price')
        if odds<=1:raise ValueError('Fixed win odds must exceed one')
        barrier=finite(r['barrier'],'barrier')
        if barrier<=0 or not barrier.is_integer():raise ValueError('Invalid barrier')
        row=dict(meeting=capture['meeting'],race=race,number=number,horse=name,odds=odds,
                 barrier=barrier,distance_km=distance/1000,_price_source='TAB fixed win',
                 jockey=r.get('jockey'),trainer=r.get('trainer'),listed_weight=r.get('listed_weight'))
        # Displayed weights/claims are retained verbatim until their allocated/net convention is checked.
        if r.get('age') is not None:row['age']=finite(r['age'],'age')
        going=condition(capture['track_condition'])
        for g in ['good','soft','heavy','firm','synthetic','unknown']:row['going_'+g]=float(going==g)
        bm=numeric_class(capture['class_text'])
        if math.isfinite(bm):row['benchmark_class']=bm
        # Full form can contain trials and non-retained starts; do not silently replace V6's history.
        source_form[number]=r.get('form_observation')
        active.append(row)
    if len(active)<2:raise ValueError('Fewer than two priced active runners')
    nf=len(active)
    for row in active:
        b=row['barrier'];row.update(barrier_fraction=b/nf,inside_three=float(b<=3),
            outside_barrier=float(b>nf*.75),barrier_x_distance=b/nf*distance/1000)
    audit=dict(source='TAB rendered race page',source_url=capture['source_url'],tab_verified=True,
               verification_scope='These captured fields, scratchings, condition and fixed win cells only; no ongoing freshness guarantee.',
               quote_time_policy='capture_only',provider_quote_update_time_verified=False,
               declared_runners=expected,active_runners=nf,scratched_numbers=scratched,
               predictions_generated=False,betting_ready=False)
    return dict(captured_at_utc=capture['captured_at_utc'],
        snapshot=dict(date=date,runners=active,races=[dict(meeting=capture['meeting'],race=race,expected_active_runners=nf)]),
        races=[dict(meeting=capture['meeting'],race=race,jump_time=capture['jump_time'])],audit=audit,
        form_observations=source_form)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture');p.add_argument('--output-dir',default='race_day_output/tab')
    a=p.parse_args();bundle=normalize(json.loads(Path(a.capture).read_text()))
    from assess_day import assess
    report=assess(bundle)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'assessment_bundle.json').write_text(json.dumps(bundle,indent=2,allow_nan=False)+'\n')
    (out/'readiness.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'active_runners':bundle['audit']['active_runners'], 'race':bundle['races'][0], 'readiness':report['races'][0]}))

if __name__=='__main__':main()
