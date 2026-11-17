"""Exact identity matching, metadata QA and timestamped optional overlays."""
import hashlib,sys
import numpy as np,pandas as pd
from .config import HERE,OUT,dump
from .normalization import normal,full_clock_seconds,clean_person,condition
sys.path.insert(0,str(HERE.parent/'monty_v5'))

def join_sources():
    path=HERE/'sources/github_racing_data.csv';raw=pd.read_csv(path,dtype=str,keep_default_na=False)
    a=raw.copy();a['date']=a.Date;a['track_key']=a.Track.map(normal);a['race']=pd.to_numeric(a['Race Number'],errors='coerce');a['name_key']=a.Horse.map(normal)
    key=['date','track_key','race','name_key'];attrs=['Barrier','Jockey','Trainer','Race Distance','Class','Track Condition']
    # Repeated identical static records are safe to consolidate. Never choose between conflicting records.
    a=a[key+attrs].drop_duplicates();conf=a.duplicated(key,keep=False);conflicting=int(conf.sum());a=a[~conf].copy()
    a=a.rename(columns={'Barrier':'barrier','Jockey':'jockey','Trainer':'trainer','Race Distance':'extra_distance','Class':'class_text','Track Condition':'going_text'})
    a.barrier=pd.to_numeric(a.barrier,errors='coerce');a.extra_distance=pd.to_numeric(a.extra_distance,errors='coerce')
    a.jockey=a.jockey.map(clean_person);a.trainer=a.trainer.map(clean_person);a['going']=a.going_text.map(condition)
    b=pd.read_csv(HERE.parent/'monty_v5/results/cleaned_eligible_runners.csv.gz',dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    b=b[b.date.le('2025-06-15')].copy()
    # April 2025 uses AM/PM clocks, which V5 conservatively excluded as unparseable.
    # Recover that month with the same eligibility checks, without altering V5 outputs.
    import run_research as common
    old_clock,old_out=common.seconds,common.OUT
    try:
        common.seconds=full_clock_seconds;common.OUT=OUT/'april_recovery';common.OUT.mkdir(exist_ok=True)
        recovered=common.load_sources(HERE/'sources/april_recovery')
    finally:common.seconds=old_clock;common.OUT=old_out
    b=pd.concat([b,recovered],ignore_index=True)
    if b.duplicated(['WIN_MARKET_ID','SELECTION_ID']).any():raise ValueError('Recovered month overlaps existing records')
    b['track_key']=b.TRACK.map(normal);b['race']=pd.to_numeric(b.RACE_NO);b.name_key=b.SELECTION_NAME.map(normal)
    b=b.merge(a,on=key,how='left',validate='one_to_one',indicator=True)
    matched=b._merge.eq('both')&b.DISTANCE.eq(b.extra_distance)
    for c in ['barrier','jockey','trainer','class_text','going_text','going']:
        b.loc[~matched,c]=np.nan
    b['matched_extra']=matched
    # Whole-race join coverage and known, consistent going only; labels never determine eligibility.
    g=b.groupby('WIN_MARKET_ID');complete=g.matched_extra.all();goingconsistent=g.going.nunique().eq(1)
    eligible=set(complete.index[complete&goingconsistent])
    b['enriched_eligible']=b.WIN_MARKET_ID.isin(eligible)&b.date.ge('2025-01-01')
    b=b.sort_values(['date','scheduled_seconds','WIN_MARKET_ID','SELECTION_ID'],kind='stable').reset_index(drop=True)
    dump('source_join_audit.json',dict(source_url='https://github.com/xx36Mostafa/horse-racing-ml-pipeline',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_raw_rows=len(raw),static_conflicting_rows_excluded=conflicting,matched_runner_rows=int(matched.sum()),enriched_runner_rows=int(b.enriched_eligible.sum()),enriched_races=int(b.loc[b.enriched_eligible,'WIN_MARKET_ID'].nunique()),source_results_used_as_training_labels=False,missing=dict(b.loc[b.enriched_eligible,['barrier','jockey','trainer','going']].isna().sum()),timestamp_caveat='Static fields reconstructed from historical TAB-derived result records, no pre-race publication snapshots supplied. Going may be final meeting condition rather than per-race known going.'))
    return b


def validate_overlay(frame):
    required={'date','track','race','horse','source_url','published_at','scheduled_start_utc'}
    if not required.issubset(frame.columns):raise ValueError('Overlay requires identity, source URL and both timestamps')
    a=pd.to_datetime(frame.published_at,utc=True,errors='coerce');b=pd.to_datetime(frame.scheduled_start_utc,utc=True,errors='coerce')
    if (a.isna()|b.isna()|a.gt(b)|frame.source_url.fillna('').eq('')).any():raise ValueError('Unverifiable or post-cutoff overlay')
    if frame.duplicated(['date','track','race','horse']).any():raise ValueError('Conflicting overlay identities')
    return frame


def add_overlays(d):
    # Optional externally verified static pre-race inputs, never inferred from current sex or later reports.
    extras=['allocated_weight','claim_kg','age','is_gelding','first_after_gelding','blinkers_first','blinkers_off','tongue_tie_first','winkers_first']
    for c in extras:d[c]=np.nan
    p=HERE/'verified_overlay.csv'
    if p.exists():
        a=validate_overlay(pd.read_csv(p));a['track_key']=a.track.map(normal);a['name_key']=a.horse.map(normal);a['race']=pd.to_numeric(a.race)
        k=['date','track_key','race','name_key'];keep=[c for c in extras if c in a]
        d=d.drop(columns=keep).merge(a[k+keep],on=k,how='left',validate='one_to_one').reset_index(drop=True)
    return d


