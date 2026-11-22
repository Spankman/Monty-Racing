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
    match = re.fullmatch(r'(RM[67](?:PS)?)(?:\s+([A-Za-z][A-Za-z .\x27-]{0,59})\s+R?([1-9]|[1-4][0-9]|50))?', text.strip(), re.I)
    if text.strip().upper() == 'C':
        return dict(command='C', view='status')
    if not match:
        raise ValueError('Use RM6, RM7, RM6PS, RM7PS, RM6 track race, RM7 track race, or C')
    model, track, race = match.groups()
    if model.upper().endswith('PS') and track:
        raise ValueError('Use RM6/RM7 track race for a single-race assessment')
    day = date or utcnow().astimezone(TZ).date().isoformat()
    datetime.strptime(day, '%Y-%m-%d')
    if country not in (None, 'AU', 'NZ'):
        raise ValueError('country must be AU or NZ')
    return dict(command=text.strip().upper(), version=model[:3].upper().replace('RM','V'),
                view='provisional' if model.upper().endswith('PS') or track else 'official',
                date=day, meeting=track, race=race, country=country)


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


def projection(forecast, request, now=None):
    """Explicit official/provisional view; never turn a stale price into a current tip."""
    if request.get('view') == 'status':
        return {k:forecast.get(k) for k in ('schema','run_id','status','date','generated_at','models','blockers','receipt')}
    selected=[]
    for race in forecast.get('races', []):
        if request.get('meeting') and race['meeting'].casefold() != request['meeting'].casefold():
            continue
        if request.get('race') and str(race['race']) != str(request['race']):
            continue
        if request.get('country') and race['country'] != request['country']:
            continue
        item=dict(race)
        result=dict(race['models'][request['version']])
        result['freshness_at_retrieval']=freshness(race, now)
        result['freshness_checked_at']=(now or utcnow()).isoformat()
        if request['view']=='official':
            # Current gates never authorise deployment. Preserve provisional output separately.
            result['ordered_selections']=[]
            result['recommended_bet_type']='NO BET'
        item['result']=result
        item.pop('models')
        selected.append(item)
    return dict(schema=SCHEMA,run_id=forecast['run_id'],date=forecast['date'],view=request['view'],
                version=request['version'],status=forecast['status'],races=selected,
                receipt=forecast.get('receipt'),blockers=forecast.get('blockers',[]))


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
    value_watch=None
    if version=='V7':
        value_watch=json.loads((directory/'provisional_selection.json').read_text()).get('provisional_value_candidate')
    return [dict(number=str(r['number'] if version=='V6' else r['runner_id']),horse=r['horse'],
                 odds=float(r['odds'] if version=='V6' else r['fixed_win_odds']),
                 probability=float(r['monty_prob'] if version=='V6' else r['v7_win_probability']),
                 research_category=r.get('research_category'),
                 value_watch=value_watch if value_watch and str(value_watch['number'])==str(r['runner_id']) else None) for r in rows]


def selection(rows,version='V6'):
    from monty_single_race_ladder import price_ladder
    if len({r['number'] for r in rows})!=len(rows) or not rows:
        raise ValueError('Invalid scoring identities')
    if not all(math.isfinite(r['probability']) and 0<r['probability']<=1 and math.isfinite(r['odds']) and r['odds']>1 for r in rows):
        raise ValueError('Invalid scored values')
    if not math.isclose(sum(r['probability'] for r in rows),1,abs_tol=1e-6):
        raise ValueError('Unnormalized race probabilities')
    ranked=sorted(rows,key=lambda r:-r['probability'])
    ladder=price_ladder(ranked,short_price=4.0)
    # Preserve existing V6's mechanical roughie definition; diagnostic only.
    roughies=[r for r in ranked if r['odds']>=6 and r['probability']*r['odds']>1] if version=='V6' else [r for r in ranked if r.get('value_watch') and r['odds']>=4 and r['probability']>=.06 and r['probability']*r['odds']>1]
    return dict(ordered_selections=ladder['selections'],progression_bet_type=ladder['bet_type'],
                recommended_bet_type='NO BET',best_bets=[],
                best_chance=ranked[0],roughies=[dict(**r,bet_type='WIN',classification='PROVISIONAL VALUE WATCH — NO BET') for r in roughies],
                official_classification='NO BET',provisional_classification='PROVISIONAL RESEARCH ONLY',
                betting_authorised=False)


def execute(day, output, v7_root, *, run_id, payload=None, captured=None, request=None, fixture=False, scorer=invoke):
    """Capture once, run both frozen models on byte-identical per-race snapshots."""
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    public=output/'public';public.mkdir()
    v7_root=Path(v7_root).resolve()
    started=utcnow();request=request or command('RM6',day)
    result=dict(schema=SCHEMA,date=day,timezone='Australia/Brisbane',run_id=str(run_id),
                generated_at=started.isoformat(),receipt=f'runs/{day}/{run_id}/receipt.json',source_mode='SIMULATED FIXTURE' if fixture else 'LIVE',
                status='FAILED',models={},races=[],blockers=[],coverage={},qualifying_forecasts=0)
    pins={}
    stage='frozen_artifact_verification'
    try:
        if not fixture and day!=started.astimezone(TZ).date().isoformat():
            raise ValueError('Live request date is not today in Brisbane')
        from monty.integrity import verify_artifacts
        verify_artifacts(ROOT/'monty_v6')
        pins={'V6':sha(ROOT/'monty_v6/results/frozen_model.json'),'V7':sha(v7_root/'v7/artifacts/fold_3_model.json')}
        if pins['V7']!=V7_MODEL_SHA:
            raise ValueError('Pinned V7 model hash mismatch')
        for version,root in [('V6',ROOT),('V7',v7_root)]:
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            if version=='V7' and commit!=V7_COMMIT:
                raise ValueError('Pinned V7 commit mismatch')
            result['models'][version]=dict(commit=commit,model_sha256=pins[version],status='NOT_RUN',research_only=version=='V7')
        stage='provider_capture'
        if payload is None:
            from krok_adapter import fetch
            key=os.environ.get('KROK_API_KEY','').strip()
            if not key:
                raise ValueError('KROK_API_KEY absent; live request not attempted')
            payload=fetch(day,key)
        captured=captured or utcnow()
        encoded=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        result['provider_snapshot_sha256']=hashlib.sha256(encoded).hexdigest()
        result['captured_at']=captured.isoformat()
        if not 0<=(utcnow()-captured).total_seconds()<=MAX_AGE_SECONDS:
            raise ValueError('Stale or future-dated provider snapshot')
        stage='snapshot_validation'
        meta=metadata(payload,day)
        snapshot,audit=normalized_snapshot(payload,day,bool(request.get('meeting')))
        result['coverage']=dict(provider_meetings=len({(r['country'],r['meeting']) for r in meta.values()}),provider_races=len(meta),
            accepted_races=len(snapshot['races']),scored_both=0,independently_verified=0,
            complete_au_nz_coverage_verified=False,provider_skips=audit['skipped'],
            jurisdictions_observed=sorted({r['country'] for r in meta.values()}),
            limitation='Provider-only AU/NZ card; independent TAB meeting completeness unavailable')
        if request.get('meeting'):
            matches=[m for m in meta.values() if m['meeting'].casefold()==request['meeting'].casefold() and m['race']==str(request['race']) and (not request.get('country') or m['country']==request['country'])]
            if len(matches)!=1:
                raise ValueError('Requested track/race absent or ambiguous; specify country')
        for race in snapshot['races']:
            k=(race['meeting'].casefold(),str(race['race']))
            m=meta.get(k)
            if not m:
                continue
            if request.get('meeting') and (k!=(request['meeting'].casefold(),str(request['race'])) or request.get('country') not in (None,m['country'])):
                continue
            m=dict(m,date=day,single_race=bool(request.get('meeting')))
            runners=[r for r in snapshot['runners'] if (r['meeting'].casefold(),str(r['race']))==k]
            record=dict(**{n:m[n] for n in ['meeting','race','country','scheduled_start','scratchings']},
                        captured_at=captured.isoformat(),independent_verification=False,
                        scratching_status='PROVIDER ASSERTION ONLY',models={})
            reasons=['independent_fields_scratchings_and_going_unverified','historical_form_incomplete','prospective_value_unverified']
            if any(r.get('_price_source')!='TAB' for r in runners):
                reasons.append('named_bookmaker_fixed_win_not_available_for_entire_field')
            try:
                if timestamp(m['scheduled_start'])<=utcnow():reasons.append('race_already_due')
            except (TypeError,ValueError):reasons.append('jump_time_unverified')
            if len(runners)<3:reasons.append('common_V7_minimum_three_runners_not_met')
            record['data_completeness']=dict(active_runners=len(runners),form_history_verified=False)
            if not any(x in reasons for x in ['named_bookmaker_fixed_win_not_available_for_entire_field','race_already_due','jump_time_unverified','common_V7_minimum_three_runners_not_met']):
                private=output/'private'/str(len(result['races']))
                common=private/'snapshot.json'
                write(common,dict(date=day,runners=runners,races=[race]))
                record['shared_model_input_sha256']=sha(common)
                for version in ['V6','V7']:
                    try:
                        rows=scorer(version,common,m,private/version,v7_root)
                        if sha(common)!=record['shared_model_input_sha256']:
                            raise ValueError('Shared input mutated')
                        if {(r['number'],r['horse'],r['odds']) for r in rows}!={(r['number'],r['horse'],r['odds']) for r in runners}:
                            raise ValueError('Model output identities/odds differ from common input')
                        if freshness(record)!='FRESH AT CHECK TIME':
                            raise ValueError('Race closed or snapshot expired during inference')
                        view=selection(rows,version)
                        view.update(status='SCORED',decision_at=utcnow().isoformat(),no_bet_reasons=reasons.copy(),
                                    bookmaker='TAB (Krok attributed)',quoted_at=captured.isoformat(),
                                    model_version=version,model_commit=result['models'][version]['commit'])
                        if version=='V7':view['no_bet_reasons'].append('V7_RESEARCH_ONLY_NOT_APPROVED')
                        record['models'][version]=view
                    except Exception as exc:
                        record['models'][version]=dict(status='FAILED',official_classification='NO BET',ordered_selections=[],
                            no_bet_reasons=['inference_failed_'+type(exc).__name__],betting_authorised=False)
                if all(x['status']=='SCORED' for x in record['models'].values()):result['coverage']['scored_both']+=1
            else:
                for v in ['V6','V7']:
                    record['models'][v]=dict(status='BLOCKED',official_classification='NO BET',ordered_selections=[],no_bet_reasons=reasons.copy(),betting_authorised=False)
            result['races'].append(record)
        for version in ['V6','V7']:
            scored=sum(r['models'][version]['status']=='SCORED' for r in result['races'])
            failed=sum(r['models'][version]['status']=='FAILED' for r in result['races'])
            result['models'][version].update(scored_races=scored,status='PARTIAL' if failed and scored else 'FAILED' if failed else 'SCORED' if scored else 'BLOCKED')
        result['status']='COMPLETED_NO_BET' if result['races'] and all(v['status']=='SCORED' for v in result['models'].values()) else 'PARTIAL_OR_BLOCKED'
        result['blockers']=['No independently verified TAB field/conditions attestation; official NO BET','V7 remains research only']
    except Exception as exc:
        # Do not expose arbitrary exception strings or URLs containing credentials.
        result['blockers']=[stage+': '+type(exc).__name__]
        result['status']='FAILED'
    finally:
        for version,path in [('V6',ROOT/'monty_v6/results/frozen_model.json'),('V7',v7_root/'v7/artifacts/fold_3_model.json')]:
            if version in pins and sha(path)!=pins[version]:raise RuntimeError('Frozen model changed')
    result['generated_at']=utcnow().isoformat()
    result['valid_until']=(captured+timedelta(seconds=MAX_AGE_SECONDS)).isoformat() if captured else None
    write(public/'forecast.json',result)
    receipt=dict(schema=SCHEMA,run_id=str(run_id),date=day,status=result['status'],
                 forecast_sha256=sha(public/'forecast.json'),provider_snapshot_sha256=result.get('provider_snapshot_sha256'),
                 models=result['models'],generated_at=result['generated_at'],source_mode=result['source_mode'],
                 qualifying_forecasts=0,model_artifacts_unchanged=True)
    write(public/'receipt.json',receipt)
    for version in ['V6','V7']:
        for mode in ['official','provisional']:
            write(public/(version.lower()+'-'+mode+'.json'),projection(result,dict(version=version,view=mode)))
    return result


def ticket(view):
    version=view['version'];mode=view['view']
    title=f'MONTY {version} — '+('OFFICIAL SELECTION SLIP' if version=='V6' and mode=='official' else 'SHADOW SELECTION SLIP (RESEARCH ONLY)' if version=='V7' else 'PROVISIONAL SELECTION SLIP')
    lines=[title,view['date']+' · Australia/Brisbane','NO BET — no qualified wagers','']
    for race in view['races']:
        lines.append(race['meeting']+' R'+str(race['race']))
        result=race['result'];rows=result.get('ordered_selections',[])
        if rows:
            lines.append(result['progression_bet_type']+' assessment only — NO BET')
            for i,r in enumerate(rows):
                text=f"#{r['number']} {r['horse']} — ${r['odds']:.2f}"
                lines.append(('**'+text+'**') if i==0 else text)
        lines.append('NO BET: '+', '.join(result.get('no_bet_reasons',[])))
        lines.append('Quote '+str(race['captured_at'])+' · '+result.get('freshness_at_retrieval','UNKNOWN'))
        lines.append('')
    lines.append('IN MONTY WE TRUST')
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('--command',default='RM6');p.add_argument('--date');p.add_argument('--country',choices=['AU','NZ'])
    p.add_argument('--output',type=Path,required=True);p.add_argument('--v7-root',type=Path,required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--fixture',type=Path)
    a=p.parse_args();req=command(a.command,a.date,a.country)
    if req.get('view')=='status':raise SystemExit('C reads published latest.json; it never starts inference')
    payload=json.loads(a.fixture.read_text()) if a.fixture else None
    result=execute(req['date'],a.output,a.v7_root,run_id=a.run_id,request=req,payload=payload,fixture=bool(a.fixture))
    for v in ['V6','V7']:
        for mode in ['official','provisional']:
            view=projection(result,dict(version=v,view=mode))
            (a.output/'public'/f'{v.lower()}-{mode}.txt').write_text(ticket(view))
    from operations.render import render_all
    render_all(a.output/'public')
    print(json.dumps({'run_id':a.run_id,'status':result['status'],'races':len(result['races']),'source_mode':result['source_mode']}))
    return 1 if result['status']=='FAILED' else 0


if __name__=='__main__':raise SystemExit(main())
