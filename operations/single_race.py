"""Single-race eligibility and evidence handoff, never a replacement predictor."""
import math

CLOSED={'abandoned','cancelled','canceled','resulted','closed','final'}
RESEARCH=['current fields and scratchings','recent and relevant form','jockeys and trainers',
          'barriers and weights','track conditions and distance suitability','available market prices and capture times']


def prepare(payload,day,request):
    """Scope the actual source field; publish only selected factual evidence."""
    if not isinstance(payload,dict) or payload.get('success') is not True or not isinstance(payload.get('data'),list):
        raise ValueError('Invalid provider envelope')
    meta=payload.get('meta') or {}
    if not isinstance(meta,dict) or any(meta.get(k) for k in ['truncated','has_more','next_cursor','next_page','next']):
        raise ValueError('Incomplete provider envelope')
    from krok_adapter import price
    matches=[]
    for meeting in payload['data']:
        if (str(meeting.get('date',''))[:10]!=day or meeting.get('country') not in ('AU','NZ')
            or meeting.get('type') not in ('T','R') or str(meeting.get('venue','')).casefold()!=request['meeting'].casefold()
            or request.get('country') not in (None,meeting.get('country'))):continue
        for race in meeting.get('races',[]):
            if str(race.get('number'))==str(request['race']):matches.append((meeting,race))
    if len(matches)!=1:raise ValueError('Requested race absent or ambiguous')
    meeting,race=matches[0]
    field=[]
    for runner in race.get('runners',[]) if isinstance(race.get('runners'),list) else []:
        if not isinstance(runner,dict) or runner.get('number') is None or not isinstance(runner.get('name'),str) or not runner['name'].strip():continue
        quote,origin=price(runner)
        row=dict(number=str(runner['number']),horse=runner['name'],scratched=runner.get('is_scratched') if type(runner.get('is_scratched')) is bool else None,
                 odds=quote,price_source=origin)
        # Observations only: no invented historical form or replacement features.
        for key in ['barrier','weight','claim_kg','age']:
            value=runner.get(key)
            if type(value) in (int,float) and math.isfinite(value):row[key]=value
        for key in ['jockey','trainer']:
            if isinstance(runner.get(key),str) and len(runner[key])<=160:row[key]=runner[key]
        field.append(row)
    facts=dict(date=day,meeting=meeting['venue'],race=str(race['number']),country=meeting['country'],
               source=(meta.get('provider', 'Krok') + ' provider assertions; not independently TAB verified'),provider_status=race.get('status'),
               known_runners=field,active_runners=sum(r['scratched'] is False for r in field),
               priced_active_runners=sum(r['scratched'] is False and r['odds'] is not None for r in field),
               field_identity_ambiguous=len({r['number'] for r in field})!=len(field),
               unknown_scratching_count=sum(r['scratched'] is None for r in field),
               historical_form_available=False,required_research=RESEARCH)
    distance=race.get('distance_m',race.get('distance'))
    if type(distance) in (int,float) and math.isfinite(distance) and distance>0:facts['distance_m']=distance
    going=race.get('track_condition') or meeting.get('track_hint')
    if isinstance(going,str) and len(going)<=160:facts['track_condition']=going
    scoped=dict(success=True,data=[dict(meeting,races=[race])],meta={'has_more':False})
    return scoped,facts


def annotate(record,version):
    """Keep model outcomes intact and attach the next step, never fake rankings."""
    model=record['models'][version]
    model['assessment_level']='PROVISIONAL' if model['status']=='SCORED' else 'MODEL RANKINGS UNAVAILABLE'
    model['model_inference']=model['status']=='SCORED'
    if model['status']=='SCORED':return
    if str(record['assessment_facts'].get('provider_status','')).lower() in CLOSED:
        model['assessment_level']='NO CURRENT ASSESSMENT — RACE CLOSED'
        model['no_bet_reasons'].append('provider_reports_race_closed')
        return
    facts=record['assessment_facts']
    model['form_assessment_request']=research_request(
        dict(date=facts['date'],meeting=facts['meeting'],race=facts['race'],country=facts['country'],version=version),
        model.get('no_bet_reasons',[]),model['status'],facts)


def research_request(request,reasons,status='UNAVAILABLE',facts=None):
    return dict(classification='FORM ASSESSMENT — INDEPENDENT, NOT A MONTY PREDICTION',
        model_version_requested=request['version'],model_inference=False,model_status=status,
        target={k:request.get(k) for k in ['date','meeting','race','country']},reasons=reasons,
        facts=facts,required_research=RESEARCH,requires_fresh_public_sources=True,
        instruction='Report the model status and blocker. No Monty selection can be given without genuine inference.')


def handoffs(view):
    return [race['result']['form_assessment_request'] for race in view.get('races',[])
            if race['result'].get('form_assessment_request')
            and not race['result'].get('freshness_at_retrieval','').startswith(('STALE','CLOSED'))
            and str(race.get('assessment_facts',{}).get('provider_status','')).lower() not in CLOSED]


def quote_text(row):
    value=row.get('odds')
    return '$'+format(value,'.2f') if type(value) in (int,float) and math.isfinite(value) and value>1 else 'ODDS UNAVAILABLE'
