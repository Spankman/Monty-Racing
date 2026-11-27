"""Finite preregistration, timing and private-evidence contracts; no new scoring."""
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib,json,re,subprocess,zipfile

TZ=ZoneInfo('Australia/Brisbane')
HERE=Path(__file__).resolve().parent
def protocol():return json.loads((HERE/'protocol.json').read_text())
def stamp(v):
    t=datetime.fromisoformat(v.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('Timezone required')
    return t.astimezone(timezone.utc)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

# Classification is explicit, not guessed from prize money, model ranking or
# sponsor words. Unknown venues are disclosed and never counted toward strata.
VENUES={
 'rockhampton':('QLD','provincial','rock'), 'doomben':('QLD','metropolitan','doom'),
 'eagle farm':('QLD','metropolitan','e_fm'), 'ipswich':('QLD','provincial','ipsw'),
 'sunshine coast':('QLD','provincial','scst'), 'toowoomba':('QLD','provincial','twba'),
 'townsville':('QLD','provincial','town'), 'gold coast':('QLD','provincial','gcst'),
 'mornington':('VIC','provincial',None),'hawkesbury':('NSW','provincial',None),
 'geraldton':('WA','country',None),'albany':('WA','country',None),
 'wodonga':('VIC','country',None),'bet365 wodonga':('VIC','country',None),
 'ballarat':('VIC','country',None),'bendigo':('VIC','country',None),'kilmore':('VIC','country',None),
 'warrnambool':('VIC','country',None),'geelong':('VIC','country',None),'hamilton':('VIC','country',None),
 'werribee':('VIC','country',None),'swan hill':('VIC','country',None),
 'grafton':('NSW','country',None),'ballina':('NSW','country',None),'taree':('NSW','country',None),
 'muswellbrook':('NSW','country',None),'scone':('NSW','country',None),'mudgee':('NSW','country',None),
 'wellington':('NSW','country',None),'wagga':('NSW','country',None),'wagga wagga':('NSW','country',None),
 'rosehill':('NSW','metropolitan',None),'rosehill gardens':('NSW','metropolitan',None),
 'randwick':('NSW','metropolitan',None),'royal randwick':('NSW','metropolitan',None),
 'warwick farm':('NSW','metropolitan',None),'canterbury':('NSW','metropolitan',None),
 'flemington':('VIC','metropolitan',None),'caulfield':('VIC','metropolitan',None),
 'sandown':('VIC','metropolitan',None),'sandown hillside':('VIC','metropolitan',None),
 'moonee valley':('VIC','metropolitan',None),'ascot':('WA','metropolitan',None),
 'morphettville':('SA','metropolitan',None),'strathalbyn':('SA','country',None)
}

def preregister(card,day,now):
    p=protocol()
    if day not in p['dates']:raise ValueError('Date outside finite trial')
    eligible=[];excluded=[]
    for race in card:
        venue=str(race.get('venue_canonical') or race.get('venue','')).casefold()
        key=VENUES.get(venue)
        try:
            jump=stamp(race['start_time']);local=jump.astimezone(TZ)
            label=' '.join(str(race.get(k) or '') for k in ('race_name','race_class','conditions')).casefold()
            if local.date().isoformat()!=day:continue
            if race.get('country')!='AU' or race.get('category')!='horse':raise ValueError('unconfirmed_jurisdiction_or_code')
            if not key:raise ValueError('venue_classification_unverified')
            if not p['jump_window_brisbane'][0]<=local.strftime('%H:%M')<=p['jump_window_brisbane'][1]:raise ValueError('outside_runner_window')
            if (jump-now).total_seconds()<p['minimum_notice_minutes']*60:raise ValueError('insufficient_preregistration_notice')
            if re.search(r'maiden|\bmdn\b|\b2yo\b|two.year.old|hurdle|steeple',label):raise ValueError('excluded_class')
            if not re.search(r'benchmark|\bbm\s*\d|handicap|class\s*\d|rating|open|listed|group',label):raise ValueError('race_class_unverified')
            eligible.append(dict(date=day,race_id=race['race_id'],venue=race['venue'],race_number=race['race_number'],
                start_time=race['start_time'],state=key[0],meeting_class=key[1],rq_code=key[2],
                weekday=local.strftime('%A'),country='AU',category='horse'))
        except (KeyError,ValueError,TypeError) as exc:
            excluded.append(dict(race_id=race.get('race_id'),reason=str(exc) if type(exc) is ValueError else 'invalid_card_metadata'))
    eligible.sort(key=lambda r:(r['start_time'],r['venue'],r['race_number'],r['race_id']))
    chosen=[]
    def pick(predicate):
        options=[r for r in eligible if r not in chosen and predicate(r) and all(
            abs((stamp(r['start_time'])-timedelta(minutes=a)-(stamp(c['start_time'])-timedelta(minutes=b))).total_seconds())
            >=p['minimum_window_spacing_seconds'] for c in chosen for a in p['capture_minutes'] for b in p['capture_minutes'])]
        options.sort(key=lambda r:(r['venue'] in {x['venue'] for x in chosen},r['start_time'],r['race_number']))
        if options:chosen.append(options[0])
    if day=='2026-11-26':
        pick(lambda r:r['state']=='QLD');pick(lambda r:r['state']!='QLD')
    if stamp(day+'T00:00:00+10:00').astimezone(TZ).weekday()==5:
        pick(lambda r:r['state']=='QLD' and r['meeting_class']=='metropolitan')
        pick(lambda r:r['state']!='QLD' and r['meeting_class']=='metropolitan')
    while len(chosen)<p['target_races_per_day']:
        before=len(chosen);pick(lambda r:r['meeting_class']=='country')
        if len(chosen)==before:pick(lambda r:True)
        if len(chosen)==before:break
    chosen.sort(key=lambda r:r['start_time'])
    plan=dict(trial_id=p['trial_id'],date=day,registered_at=now.isoformat(),protocol_sha256=digest(p),
        races=chosen,eligible_candidates=len(eligible),exclusions=excluded,
        status='PREREGISTERED' if len(chosen)==3 else 'PARTIAL_PREREGISTRATION',
        future_slots_are_not_claimed_registered_races=True)
    plan['plan_sha256']=digest(plan)
    return plan

def validate_plan(plan):
    saved=dict(plan);expected=saved.pop('plan_sha256')
    if digest(saved)!=expected or saved['protocol_sha256']!=digest(protocol()):raise ValueError('Preregistration integrity mismatch')
    if saved['date'] not in protocol()['dates']:raise ValueError('Date outside trial')
    if len({r['race_id'] for r in saved['races']})!=len(saved['races']):raise ValueError('Duplicate registered race')
    for race in saved['races']:
        if stamp(race['start_time'])<=stamp(saved['registered_at'])+timedelta(minutes=60):raise ValueError('Registration after first required window')
    return plan

def windows(plan):
    validate_plan(plan)
    return sorted([(stamp(r['start_time'])-timedelta(minutes=m),r,m) for r in plan['races'] for m in protocol()['capture_minutes']],key=lambda x:x[0])

def seal(folder,output):
    """Authenticated encryption; public recipient cert contains no private key."""
    folder=Path(folder);plain=Path(str(output)+'.plaintext.zip')
    with zipfile.ZipFile(plain,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(folder.rglob('*')):
            if file.is_file():archive.write(file,file.relative_to(folder))
    try:
        subprocess.run(['openssl','cms','-encrypt','-aes-256-gcm','-binary','-outform','DER','-in',str(plain),
            '-out',str(output),str(HERE/'recipient-public.pem')],check=True,capture_output=True)
    finally:plain.unlink(missing_ok=True)
    return hashlib.sha256(Path(output).read_bytes()).hexdigest()
