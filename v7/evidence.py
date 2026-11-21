"""Strict point-in-time numeric evidence joins; absent/unverified data stays NaN.

Source adapters normalize into this contract; source branding alone is not
proof of identity, chronology, racing code or historical availability.
"""
from datetime import datetime, timezone
import numpy as np
import pandas as pd

FEATURES = ('last600_seconds','early_pace_mps','prior_interference_score',
            'prior_track_bias_residual','forecast_rain_mm','forecast_wind_kmh',
            'jockey_90d_strike','trainer_90d_strike')


def utc(s):
    d=datetime.fromisoformat(str(s).replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('Timezone required')
    return d.astimezone(timezone.utc)


def join_evidence(runners, observations):
    """ID join only, reject post-cutoff observations and ambiguous duplicates.

    runners: race_id, runner_id, decision_at, country.
    observations: same IDs/country plus feature,value,source_url,published_at,
    available_at,captured_at,event_at,event_kind,identity_verified.
    available_at is the verified vendor availability, NOT event time or a
    publication date guessed from today's download. Historical download capture
    may be later; the row explicitly records both.
    """
    r=runners.copy()
    if r.duplicated(['race_id','runner_id']).any():raise ValueError('Duplicate runners')
    for f in FEATURES:r[f]=np.nan
    index={(str(x.race_id),str(x.runner_id)):i for i,x in r.iterrows()}
    accepted=set();audit=[]
    for o in observations:
        reason=None; key=(str(o.get('race_id')),str(o.get('runner_id')))
        try:
            if key not in index:raise ValueError('Unmatched identity')
            i=index[key]; f=o['feature']; cutoff=utc(r.at[i,'decision_at'])
            if f not in FEATURES:raise ValueError('Unsupported feature')
            if o.get('identity_verified') is not True or o.get('country')!=r.at[i,'country']:
                raise ValueError('Unverified identity/country')
            if not str(o.get('source_url','')).startswith('https://'):raise ValueError('Missing source URL')
            if utc(o['available_at'])>cutoff or utc(o['published_at'])>cutoff:
                raise ValueError('Evidence unavailable at decision')
            if utc(o['captured_at'])<utc(o['available_at']):raise ValueError('Capture precedes availability')
            if o['event_kind'] not in ('forecast','prior_race'):raise ValueError('Unknown event kind')
            if f.startswith('forecast_') and o['event_kind']!='forecast':raise ValueError('Observed weather is not a forecast')
            if not f.startswith('forecast_') and o['event_kind']!='prior_race':raise ValueError('Prior-race feature requires earlier race')
            if o['event_kind']=='prior_race' and utc(o['event_at'])>=cutoff:
                raise ValueError('Current/future race outcome leakage')
            value=float(o['value'])
            if not np.isfinite(value):raise ValueError('Nonfinite value')
            if (key,f) in accepted:raise ValueError('Ambiguous duplicate evidence')
            r.at[i,f]=value;accepted.add((key,f))
        except (KeyError,ValueError,TypeError) as e:
            reason=str(e)
            # Duplicate evidence cannot leave an arbitrary first source active.
            if key in index and o.get('feature') in FEATURES and (key,o['feature']) in accepted:
                r.at[index[key],o['feature']]=np.nan
        audit.append({'race_id':key[0],'runner_id':key[1],'feature':o.get('feature'),
                      'status':'REJECTED' if reason else 'ACCEPTED','reason':reason})
    return r,audit


BLACKBOOK = ('Revelare','Argerich',"Bred 'em All",'Calamari Ring')


def blackbook_matches(fields):
    """Produce review alerts from verified published fields, not betting orders.

    Exact normalized names create candidates. They still require stable identity
    confirmation when countries/namesakes collide. Scratchings stay visible.
    """
    def norm(s):return ''.join(c.lower() for c in str(s) if c.isalnum())
    wanted={norm(s):s for s in BLACKBOOK}
    found=[]
    for row in fields:
        name=wanted.get(norm(row.get('horse','')))
        if not name:continue
        if not row.get('source_url') or not row.get('race_id') or not row.get('date'):
            raise ValueError('Blackbook match requires published field provenance')
        found.append(dict(row,blackbook_name=name,status='SCRATCHED' if row.get('scratched') else 'REVIEW_NEXT_START',
                          automatic_bet=False))
    return found
