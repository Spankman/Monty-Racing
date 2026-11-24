"""ChatGPT command contract and shared-snapshot inference; no model fitting."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo
from operations.timing import timed
from operations.assessment import OutputContractError, classify, diagnostic, feature_evidence, validate_output, provider_inventory

TZ = ZoneInfo('Australia/Brisbane')
V7_COMMIT = 'efc51abb1595ef1eb8417e2d4e0d591f6d3c9378'
V7_MODEL_SHA = 'c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324'
MAX_AGE_SECONDS = 300
SCHEMA = 'monty.operations.v1'
ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'monty_v6'))


def utcnow():
    return datetime.now(timezone.utc)


def timestamp(s):
    d = datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Timezone required')
    return d.astimezone(timezone.utc)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def command(text, date=None, country=None):
    text = ' '.join(text.split())
    text = re.sub(r'^(?:please\s+)?run\s+monty\s+(?:for\s+)?', '', text, flags=re.I)
    text = re.sub(r'\s+please[.!]?$', '', text, flags=re.I)
    text = re.sub(r'^RMV([67])PS(?=\s|$)', r'RM\1PS', text, flags=re.I)
    race_suffix = r'\s+(?:race\s+|R\s*)?([1-9]|[1-4][0-9]|50)'
    track_name = r"([A-Za-z][A-Za-z .\x27-]{0,59}?)"
    if re.fullmatch(track_name + race_suffix, text, re.I):
        text='RM6 '+text
    match = re.fullmatch(r'(RM[67](?:PS)?)(?:\s+' + track_name + race_suffix + r')?', text, re.I)
    if text.strip().upper() == 'C':
        return dict(command='C', view='status')
    if not match:
        raise ValueError('Use RM6, RM7, RM6PS, RM7PS, RM6 track race, RM7 track race, or C')
    model, track, race = match.groups()
    day = date or utcnow().astimezone(TZ).date().isoformat()
    if datetime.strptime(day, '%Y-%m-%d').date().isoformat() != day:
        raise ValueError('Date must be YYYY-MM-DD')
    if country not in (None, 'AU', 'NZ'):
        raise ValueError('country must be AU or NZ')
    canonical = model.upper() + (f' {track.upper()} {race}' if track else '')
    return dict(command=canonical, version=model[:3].upper().replace('RM','V'),
                view='provisional' if model.upper().endswith('PS') or track else 'shadow' if model.upper() == 'RM7' else 'official',
                date=day, meeting=track, race=race, country=country,
                provisional_requested=model.upper().endswith('PS'))


def freshness(record, now=None):
    now = now or utcnow()
    try:
        age = (now-timestamp(record['captured_at'])).total_seconds()
        if age < 0 or age > MAX_AGE_SECONDS:
            return 'STALE — REQUEST A FRESH RUN'
        if timestamp(record['scheduled_start']) <= now:
            return 'CLOSED — JUMP TIME REACHED'
    except (ValueError, KeyError, TypeError):
        return 'UNVERIFIED TIMING — NO BET'
    return 'FRESH AT CHECK TIME'


def current_result(race, saved, mode, now):
    result = dict(saved)
    result['freshness_at_retrieval']=freshness(race, now)
    result['freshness_checked_at']=now.isoformat()
    result.pop('diagnostic_assessment', None)
    if mode=='official' and result['freshness_at_retrieval'] == 'FRESH AT CHECK TIME':
        result['diagnostic_assessment'] = saved.get('diagnostic_assessment') or diagnostic(saved)
    if mode=='official' or result['freshness_at_retrieval'] != 'FRESH AT CHECK TIME':
        for key in ('best_bets', 'ordered_selections', 'roughies'):
            result[key] = []
        result.pop('best_chance', None)
        for key in ('ranked_runners','most_likely','value_selection'):result.pop(key,None)
        result['progression_bet_type'] = result['recommended_bet_type'] = 'NO BET'
    return result


def refresh_view(view, now=None):
    now = now or utcnow()
    return dict(view, races=[
        dict(race, result=current_result(race, race['result'], view['view'], now))
        for race in view['races']
    ])


def projection(forecast, request, now=None):
    """Explicit official/provisional view; never turn a stale price into a current tip."""
    if request.get('view') == 'status':
        return {k:forecast.get(k) for k in ('schema','run_id','status','date','generated_at','models','blockers','receipt')}
    now = now or utcnow()
    selected=[]
    for race in forecast.get('races', []):
        if request.get('meeting') and race['meeting'].casefold() != request['meeting'].casefold():
            continue
        if request.get('race') and str(race['race']) != str(request['race']):
            continue
        if request.get('country') and race['country'] != request['country']:
            continue
        item=dict(race)
        result = current_result(race, race['models'][request['version']], request['view'], now)
        item['result']=result
        item.pop('models')
        selected.append(item)
    return dict(schema=SCHEMA,run_id=forecast['run_id'],date=forecast['date'],view=request['view'],
                version=request['version'],status=forecast['status'],races=selected,
                receipt=forecast.get('receipt'),blockers=forecast.get('blockers',[]),
                captured_at=forecast.get('captured_at'),valid_until=forecast.get('valid_until'))


def normalized_snapshot(payload, day, allow_restricted=False):
    from krok_adapter import normalize
    snapshot,audit=normalize(payload, day, allow_restricted_classes=allow_restricted)
    # V7 requires explicit false authorisation flags; these are safety labels,
    # not claims that a provider verified field completeness or eligibility.
    for row in snapshot['runners']:
        row['betting_authorised']=False
    for row in snapshot['races']:
        row['betting_authorised']=False
    return snapshot,audit


def metadata(payload, day):
    result={}
    for meeting in payload.get('data',[]):
        if str(meeting.get('date',''))[:10]!=day or meeting.get('country') not in ('AU','NZ') or meeting.get('type') not in ('T','R'):
            continue
        for race in meeting.get('races',[]):
            key=(str(meeting.get('venue','')).casefold(),str(race.get('number')))
            row=dict(country=meeting['country'],meeting=meeting.get('venue'),race=str(race.get('number')),
                     scheduled_start=race.get('jump_time'),provider_status=race.get('status'),
                     provider_track_condition=race.get('track_condition') or meeting.get('track_hint'),
                     provider_surface=race.get('surface') or meeting.get('surface'),
                     scratchings=[dict(number=str(r.get('number')),horse=r.get('name')) for r in race.get('runners',[]) if r.get('is_scratched') is True])
            if key in result:
                raise ValueError('Ambiguous country or duplicate race identity')
            result[key]=row
    return result


def invoke(version, snapshot_path, meta, directory, v7_root):
    """Separate interpreters avoid monty/v7 import collisions; no fallback."""
    directory.mkdir(parents=True)
    if version=='V6':
        program='from run_day import run; import sys; run(sys.argv[1],sys.argv[2],sys.argv[3])'
        args=[sys.executable,'-c',program,str(snapshot_path),meta['date'],str(directory)]
        cwd=ROOT
    else:
        args=[sys.executable,'-m','v7.run_provisional_race',str(snapshot_path),
              '--meeting',meta['meeting'],'--race',meta['race'],'--date',meta['date'],
              '--country',meta['country'],'--output-dir',str(directory)]
        # Caller already classified/restricted request explicitly; only a single
        # requested race can reach the restricted-class opt-in.
        if meta.get('single_race'):
            args.append('--allow-restricted')
        cwd=v7_root
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,timeout=120)
    if p.returncode:
        raise RuntimeError(version+' inference failed')  # No private stdout/error disclosure.
    import csv
    file=directory/('monty_selections.csv' if version=='V6' else 'v7_research_scores.csv')
    with file.open() as f:
        rows=list(csv.DictReader(f))
    from operations.model_audit import trace
    component_trace=trace(version,directory,v7_root,ROOT/'monty_v6')
    value_watch=None
    if version=='V7':
        value_watch=json.loads((directory/'provisional_selection.json').read_text()).get('provisional_value_candidate')
    return [dict(number=str(r['number'] if version=='V6' else r['runner_id']),horse=r['horse'],
                 odds=float(r['odds'] if version=='V6' else r['fixed_win_odds']),
                 probability=float(r['monty_prob'] if version=='V6' else r['v7_win_probability']),
                 score_trace=component_trace[str(r['number'] if version=='V6' else r['runner_id'])],
                 feature_coverage=float(r['feature_coverage']) if version=='V6' else None,
                 known_feature_count=int(r['known_feature_count']) if version=='V7' else None,
                 research_category=r.get('research_category'),
                 value_watch=value_watch if value_watch and str(value_watch['number'])==str(r['runner_id']) else None) for r in rows]


def selection(rows,version='V6'):
    from monty_single_race_ladder import price_ladder
    if len({r['number'] for r in rows})!=len(rows) or not rows:
        raise OutputContractError('invalid_scoring_identities')
    if not all(math.isfinite(r['probability']) and 0<r['probability']<=1 and math.isfinite(r['odds']) and r['odds']>1 for r in rows):
        raise OutputContractError('invalid_scored_values')
    if not math.isclose(sum(r['probability'] for r in rows),1,abs_tol=1e-6):
        raise OutputContractError('unnormalized_race_probabilities')
    market_total=sum(1/r['odds'] for r in rows)
    ranked=[dict(r,market_probability=(1/r['odds'])/market_total,
                 fair_win_odds=1/r['probability'],numerical_win_edge=r['probability']*r['odds']-1)
            for r in sorted(rows,key=lambda r:-r['probability'])]
    ladder=price_ladder(ranked,short_price=4.0)
    # V7's single value-watch marker is separate from the roughie shortlist.
    min_odds, min_probability = (6, 0) if version == 'V6' else (4, .06)
    roughies = [r for r in ranked if r['odds'] >= min_odds
                and r['probability'] >= min_probability
                and r['probability'] * r['odds'] > 1]
    return dict(ranked_runners=ranked,ordered_selections=ladder['selections'],progression_bet_type=ladder['bet_type'],
                recommended_bet_type='NO BET',best_bets=[],
                best_chance=ranked[0],roughies=[dict(**r,bet_type='WIN',classification='PROVISIONAL VALUE WATCH — NO BET') for r in roughies],
                official_classification='DATA BLOCKED',provisional_classification='RESEARCH ONLY' if version=='V7' else 'PROVISIONAL',
                value_evidence=dict(calibration_verified=False,
                    method='probability * captured fixed-win odds - 1; diagnostic only',
                    approval_evaluator='not implemented; numerical edge cannot authorise betting'),
                betting_authorised=False)


def execute(day, output, v7_root, *, run_id, payload=None, captured=None, request=None, fixture=False, scorer=invoke, timings=False):
    """Capture once, run both frozen models on byte-identical per-race snapshots."""
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    public=output/'public';public.mkdir()
    v7_root=Path(v7_root).resolve()
    started=utcnow();request=request or command('RM6',day)
    result=dict(schema=SCHEMA,date=day,timezone='Australia/Brisbane',run_id=str(run_id),
                generated_at=started.isoformat(),receipt=f'runs/{day}/{run_id}/receipt.json',source_mode='SIMULATED FIXTURE' if fixture else 'LIVE',
                status='FAILED',models={},races=[],blockers=[],coverage={},qualifying_forecasts=0)
    pins={}
    from krok_adapter import IncompleteFields
    stage='date_validation'
    try:
        if not fixture and day!=started.astimezone(TZ).date().isoformat():
            raise ValueError('Live request date is not today in Brisbane')
        stage='frozen_artifact_verification'
        with timed('frozen_verification', run_id, enabled=timings):
            from monty.integrity import verify_artifacts, validate_model_contract
            verify_artifacts(ROOT/'monty_v6')
            pins={'V6':sha(ROOT/'monty_v6/results/frozen_model.json'),'V7':sha(v7_root/'v7/artifacts/fold_3_model.json')}
            if pins['V7']!=V7_MODEL_SHA:
                raise ValueError('Pinned V7 model hash mismatch')
            for version,root in [('V6',ROOT),('V7',v7_root)]:
                commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
                if version=='V7' and commit!=V7_COMMIT:
                    raise ValueError('Pinned V7 commit mismatch')
                result['models'][version]=dict(commit=commit,model_sha256=pins[version],status='NOT_RUN',research_only=version=='V7')
        v6_model=json.loads((ROOT/'monty_v6/results/frozen_model.json').read_text())
        v7_model=json.loads((v7_root/'v7/artifacts/fold_3_model.json').read_text())
        schemas={'V6':(v6_model['input_feature_names'],validate_model_contract(v6_model,v6_model['input_feature_names'])),
                 'V7':(v7_model.get('names',[]),[n for n,a in zip(v7_model.get('names',[]),v7_model.get('active',[])) if a])}
        stage='provider_capture'
        if payload is None:
            from krok_adapter import fetch
            key=os.environ.get('KROK_API_KEY','').strip()
            result['provider_credentials_configured']=bool(key)
            if not key:
                raise ValueError('KROK_API_KEY absent; live request not attempted')
            with timed('provider_fetch', run_id, enabled=timings):
                payload=fetch(day,key)
        captured=captured or utcnow()
        encoded=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        result['provider_snapshot_sha256']=hashlib.sha256(encoded).hexdigest()
        result['captured_at']=captured.isoformat()
        if not 0<=(utcnow()-captured).total_seconds()<=MAX_AGE_SECONDS:
            raise ValueError('Stale or future-dated provider snapshot')
        stage='snapshot_validation'
        single=bool(request.get('meeting'))
        facts=None;model_ready=True
        if single:
            from operations.single_race import prepare
            source,facts=prepare(payload,day,request)
        else:source=payload
        meta=metadata(source,day)
        from krok_adapter import IncompleteFields
        try:
            snapshot,audit=normalized_snapshot(source,day,single)
        except IncompleteFields:
            if not single:raise
            model_ready=False
            snapshot=dict(runners=[],races=[dict(meeting=facts['meeting'],race=facts['race'])])
            audit={'skipped':['Requested field lacks complete valid active identities/prices or is closed']}
        result['coverage']=dict(provider_inventory=provider_inventory(source,day),provider_meetings=len({(r['country'],r['meeting']) for r in meta.values()}),provider_races=len(meta),
            accepted_races=len(snapshot['races']),scored_both=0,independently_verified=0,
            complete_au_nz_coverage_verified=False,provider_skips=audit['skipped'],
            jurisdictions_observed=sorted({r['country'] for r in meta.values()}),
            limitation='Provider-only AU/NZ card; independent TAB meeting completeness unavailable')
        for race in snapshot['races']:
            k=(race['meeting'].casefold(),str(race['race']))
            m=meta.get(k)
            if not m or request.get('country') and m['country'] != request['country']:
                continue
            if request.get('meeting') and (k!=(request['meeting'].casefold(),str(request['race'])) or request.get('country') not in (None,m['country'])):
                continue
            m=dict(m,date=day,single_race=bool(request.get('meeting')))
            runners=[r for r in snapshot['runners'] if (r['meeting'].casefold(),str(r['race']))==k]
            record=dict(**{n:m[n] for n in ['meeting','race','country','scheduled_start','scratchings']},
                        captured_at=captured.isoformat(),independent_verification=False,
                        provider_track_condition=m.get('provider_track_condition'),provider_surface=m.get('provider_surface'),
                        scratching_status='PROVIDER ASSERTION ONLY',models={})
            if single:
                record['single_race_assessment']=True
                record['assessment_facts']=dict(facts,captured_at=captured.isoformat(),scheduled_start=m['scheduled_start'])
            reasons=['independent_fields_scratchings_and_going_unverified','historical_form_incomplete','prospective_value_unverified']
            if single and not model_ready:reasons.append('complete_market_field_required_by_frozen_models')
            if any(not r.get('_bookmaker') for r in runners):
                reasons.append('named_bookmaker_fixed_win_not_available_for_entire_field')
            try:
                if timestamp(m['scheduled_start'])<=utcnow():reasons.append('race_already_due')
            except (TypeError,ValueError):reasons.append('jump_time_unverified')
            record['data_completeness']=dict(active_runners=facts['active_runners'] if single else len(runners),form_history_verified=False)
            blocked_by=['race_already_due','jump_time_unverified','complete_market_field_required_by_frozen_models']
            # A missing TAB attribution is an official evidence gap, not a
            # missing market input. Complete provider prices support research.
            if not any(x in reasons for x in blocked_by):
                private=output/'private'/str(len(result['races']))
                common=private/'snapshot.json'
                write(common,dict(date=day,runners=runners,races=[race]))
                record['shared_model_input_sha256']=sha(common)
                for version in ['V6','V7']:
                    try:
                        if version=='V7':
                            v7_gap='V7_minimum_three_runners_not_met' if len(runners)<3 else 'V7_requires_consistent_price_provenance' if len({r['_price_source'] for r in runners})!=1 else None
                            if v7_gap:
                                record['models'][version]=dict(status='BLOCKED',official_classification='NO BET',ordered_selections=[],no_bet_reasons=reasons+[v7_gap],betting_authorised=False)
                                continue
                        rows=scorer(version,common,m,private/version,v7_root)
                        if sha(common)!=record['shared_model_input_sha256']:
                            raise OutputContractError('shared_model_input_mutated')
                        validate_output(rows,runners)
                        books={r['number']:r.get('_bookmaker') for r in runners}
                        rows=[dict(r,bookmaker=books[r['number']]) for r in rows]
                        if freshness(record)!='FRESH AT CHECK TIME':
                            raise OutputContractError('race_closed_or_snapshot_expired_during_inference')
                        view=selection(rows,version)
                        view['input_evidence']=feature_evidence(runners,*schemas[version])
                        if single:
                            origins={r['number']:r['_price_source'] for r in runners}
                            ranked=[dict(r,price_source=origins[r['number']]) for r in view['ranked_runners']]
                            candidates=view['roughies'] if version=='V7' else [r for r in ranked if r.get('research_category') in ('BEST BET','RUFFY') and r['probability']*r['odds']>1]
                            view.update(ranked_runners=ranked,most_likely=ranked[0],value_selection=max(candidates,key=lambda r:r['probability']*r['odds']-1) if candidates else None,reduced_confidence=True)
                        view.update(status='SCORED',decision_at=utcnow().isoformat(),no_bet_reasons=reasons.copy(),
                                    bookmaker='TAB (Krok attributed)' if all(r.get('_price_source')=='TAB' for r in runners) else 'Named fixed-win quotes (Krok attributed)' if all(r.get('_bookmaker') for r in runners) else 'Provider win quotes — attribution incomplete',quoted_at=captured.isoformat(),
                                    model_version=version,model_commit=result['models'][version]['commit'])
                        if version=='V7':view['no_bet_reasons'].append('V7_RESEARCH_ONLY_NOT_APPROVED')
                        record['models'][version]=view
                    except Exception as exc:
                        record['models'][version]=dict(status='FAILED',official_classification='NO BET',ordered_selections=[],
                            no_bet_reasons=[exc.code if isinstance(exc,OutputContractError) else 'inference_failed_'+type(exc).__name__],betting_authorised=False)
                if all(x['status']=='SCORED' for x in record['models'].values()):result['coverage']['scored_both']+=1
            else:
                for v in ['V6','V7']:
                    record['models'][v]=dict(status='BLOCKED',official_classification='NO BET',ordered_selections=[],no_bet_reasons=reasons.copy(),betting_authorised=False)
            for version in ['V6','V7']:classify(record['models'][version],version)
            if single:
                from operations.single_race import annotate
                for version in ['V6','V7']:annotate(record,version)
            result['races'].append(record)
        for version in ['V6','V7']:
            scored=sum(r['models'][version]['status']=='SCORED' for r in result['races'])
            failed=sum(r['models'][version]['status']=='FAILED' for r in result['races'])
            result['models'][version].update(scored_races=scored,status='PARTIAL' if failed and scored else 'FAILED' if failed else 'SCORED' if scored else 'BLOCKED')
        result['status']='COMPLETED_ASSESSMENTS' if result['races'] and all(v['status']=='SCORED' for v in result['models'].values()) else 'PARTIAL_OR_BLOCKED'
        result['blockers']=['Betting approval DATA BLOCKED: no independent field/conditions attestation, compatible as-of history or validated prospective approval evaluator','V7 remains research only']
    except Exception as exc:
        # Do not expose arbitrary exception strings or URLs containing credentials.
        result['blockers']=[stage+': '+type(exc).__name__]
        result['status']='DATA_BLOCKED' if isinstance(exc,IncompleteFields) else 'FAILED'
    finally:
        for version,path in [('V6',ROOT/'monty_v6/results/frozen_model.json'),('V7',v7_root/'v7/artifacts/fold_3_model.json')]:
            if version in pins and sha(path)!=pins[version]:raise RuntimeError('Frozen model changed')
    result['generated_at']=utcnow().isoformat()
    result['valid_until']=(captured+timedelta(seconds=MAX_AGE_SECONDS)).isoformat() if captured else None
    write(public/'forecast.json',result)
    receipt=dict(schema=SCHEMA,run_id=str(run_id),date=day,status=result['status'],
                 forecast_sha256=sha(public/'forecast.json'),provider_snapshot_sha256=result.get('provider_snapshot_sha256'),
                 models=result['models'],generated_at=result['generated_at'],source_mode=result['source_mode'],
                 qualifying_forecasts=0,model_artifacts_unchanged=len(pins)==2)
    write(public/'receipt.json',receipt)
    for version in ['V6','V7']:
        modes = ['official', 'provisional', 'shadow'] if version == 'V7' else ['official', 'provisional']
        for mode in modes:
            view = projection(result, dict(version=version, view=mode))
            write(public/(version.lower()+'-'+mode+'.json'), dict(view, snapshot_only=True))
    return result


def ticket(view, *, archived=False, now=None):
    if not archived:
        view = refresh_view(view, now)
    version=view['version'];mode=view['view']
    title=f'MONTY {version} — '+('OFFICIAL SELECTION SLIP' if version=='V6' and mode=='official' else 'SHADOW SELECTION SLIP (RESEARCH ONLY)' if version=='V7' else 'PROVISIONAL SELECTION SLIP')
    lines=[title,view['date']+' · Australia/Brisbane','No qualified wagers — see prediction and betting decisions separately','']
    if mode=='provisional':lines.insert(2,'PROVISIONAL ASSESSMENT — incomplete verification; not a qualified bet')
    if archived:
        lines.insert(2, 'ARCHIVED SNAPSHOT — check request freshness before use')
    from operations.single_race import quote_text
    for race in view['races']:
        lines.append(race['meeting']+' R'+str(race['race']))
        result=race['result'];rows=result.get('ordered_selections',[])
        lines.append('Prediction: '+result.get('prediction_classification',result.get('status','UNKNOWN'))+' · Betting: '+result.get('betting_decision',result.get('official_classification','UNKNOWN')))
        diag=result.get('diagnostic_assessment')
        if diag:
            lines.append('DIAGNOSTIC '+diag['classification']+' — genuine model assessment; NOT QUALIFIED')
            rows=diag['ordered_selections']
        if race.get('single_race_assessment'):
            lines.append(result.get('assessment_level','NO CURRENT ASSESSMENT'))
            lines.append('REDUCED CONFIDENCE — missing data disclosed; betting approval unavailable')
        if result.get('form_assessment_request') and not result.get('freshness_at_retrieval','').startswith(('STALE','CLOSED')):
            lines.append('No Monty model rankings were generated.')
        if rows:
            lines.append((diag['progression_bet_type'] if diag else result['progression_bet_type'])+' assessment only — no wager authorised')
            for i,r in enumerate(rows):
                text=f"#{r['number']} {r['horse']} — {quote_text(r)}"
                if r.get('bookmaker'):text+=' ('+r['bookmaker']+')'
                lines.append(('**'+text+'**') if i==0 else text)
        if race.get('single_race_assessment') and rows:
            value=result.get('value_selection')
            lines.append('MOST LIKELY: #'+str(rows[0]['number'])+' '+rows[0]['horse']+' — not automatically a value bet')
            lines.append(('PROVISIONAL VALUE WATCH · WIN ONLY · #'+str(value['number'])+' '+value['horse']+' — '+quote_text(value)+' · NO BET') if value else 'VALUE: no supported positive-edge candidate')
        if mode in ('provisional', 'shadow'):
            for roughie in result.get('roughies',[]):
                lines.append(f"RUFFY / VALUE WATCH · WIN ONLY · #{roughie['number']} {roughie['horse']} — {quote_text(roughie)} · NO BET")
        lines.append('Limitations: '+', '.join(result.get('no_bet_reasons',[])))
        timing = 'Historical quote' if archived else result.get('freshness_at_retrieval', 'UNKNOWN')
        lines.append('Quote '+str(race['captured_at'])+' · '+timing)
        lines.append('')
    lines.append('IN MONTY WE TRUST')
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('--command',default='RM6');p.add_argument('--date');p.add_argument('--country',choices=['AU','NZ'])
    p.add_argument('--output',type=Path,required=True);p.add_argument('--v7-root',type=Path,required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--fixture',type=Path)
    p.add_argument('--timings', action='store_true')
    a=p.parse_args();req=command(a.command,a.date,a.country)
    if req.get('view')=='status':raise SystemExit('C reads published latest.json; it never starts inference')
    payload=json.loads(a.fixture.read_text()) if a.fixture else None
    result=execute(req['date'],a.output,a.v7_root,run_id=a.run_id,request=req,payload=payload,fixture=bool(a.fixture),timings=a.timings)
    for path in (a.output/'public').glob('v[67]-*.json'):
        view = json.loads(path.read_text())
        path.with_suffix('.txt').write_text(ticket(view, archived=True))
    from operations.render import render_all
    render_all(a.output/'public')
    print(json.dumps({'run_id':a.run_id,'status':result['status'],'races':len(result['races']),'source_mode':result['source_mode']}))
    return 1 if result['status']=='FAILED' else 0


if __name__=='__main__':raise SystemExit(main())
