"""Request and retrieval contract. C only uses read operations."""
import argparse
from datetime import timedelta
import hashlib
import json
import re
import subprocess
import sys
from time import monotonic, sleep

from monty_operations import MAX_AGE_SECONDS, TZ, command, projection, ticket, timestamp, utcnow
from operations import transport
from operations.render import render
from operations.single_race import handoffs, research_request


RETRIEVAL_ERRORS = (RuntimeError, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError)


def with_form_handoff(result, req):
    if req and req.get('meeting'):
        blockers = result.get('blockers') or [result['semantic_outcome']]
        reason = result['semantic_outcome'] or result.get('delivery_status')
        result['form_assessment_requests'] = [research_request(req, blockers, reason)]
    return result


def archived_rankings(forecast, req, now):
    """Deliver a scored single-race record without presenting old odds or a live ticket."""
    if not req.get('meeting'):
        return []
    records = []
    for race in forecast.get('races', []):
        if (race['meeting'].casefold() != req['meeting'].casefold() or str(race['race']) != str(req['race'])
                or req.get('country') not in (None, race['country'])):
            continue
        result = race['models'][req['version']]
        if result['status'] != 'SCORED' or not result.get('ranked_runners'):
            continue
        captured, decided, jump = map(timestamp, (race['captured_at'], result['decision_at'], race['scheduled_start']))
        if not (captured <= decided < jump and decided <= now and (decided - captured).total_seconds() <= MAX_AGE_SECONDS):
            continue
        records.append(dict(label='HISTORICAL PRE-RACE ASSESSMENT — NO BET', meeting=race['meeting'],
                            race=race['race'], version=req['version'], decision_at=result['decision_at'],
                            scheduled_start=race['scheduled_start'],
                            rankings=[{key: row[key] for key in ('number', 'horse')} for row in result['ranked_runners']]))
    return records


def retrieve(index, request_id=None, req=None, now=None):
    state = transport.request_state(index)
    result = dict(request_id=request_id, request_status=state, run_id=None, workflow_url=None,
                  workflow_status=None, workflow_conclusion=None, semantic_outcome=None,
                  captured_at=None, capture_age_seconds=None,
                  valid_until=None, receipt=None)
    if index is None:
        return result
    result.update(run_id=index.get('run_id'), workflow_url=index.get('workflow_url'),
                  blockers=index.get('blockers', []))
    if state in transport.PENDING:
        return result
    result['semantic_outcome'] = index['status']
    if not index.get('receipt_path') or not index.get('forecast_path'):
        return with_form_handoff(result, req) if state == 'FAILED' else result
    try:
        raw = transport.read_bytes(index['forecast_path'])
        if index.get('receipt_sha256'):
            receipt_bytes = transport.read_bytes(index['receipt_path'])
            if not receipt_bytes or hashlib.sha256(receipt_bytes).hexdigest() != index['receipt_sha256']:
                raise ValueError('Invalid receipt hash')
            receipt = json.loads(receipt_bytes)
        else:
            receipt = transport.read(index['receipt_path'])
        if not raw or not receipt or hashlib.sha256(raw).hexdigest() != index['forecast_sha256']:
            raise ValueError('Invalid forecast')
        if (receipt.get('forecast_sha256'), receipt.get('run_id'), receipt.get('status')) != (
            index['forecast_sha256'], index['run_id'], index['status']
        ):
            raise ValueError('Invalid receipt')
        forecast = json.loads(raw)
        if forecast['run_id'] != index['run_id'] or forecast['status'] != index['status']:
            raise ValueError('Forecast references another run')
    except (ValueError, KeyError, TypeError):
        return with_form_handoff(dict(result, semantic_outcome='INTEGRITY_CHECK_FAILED'), req)
    result.update(receipt=receipt, receipt_path=index['receipt_path'],
                  captured_at=forecast.get('captured_at'), valid_until=forecast.get('valid_until'),
                  blockers=forecast.get('blockers', []), source_mode=forecast.get('source_mode'),
                  models=forecast.get('models', {}))
    now = now or utcnow()
    captured = result['captured_at']
    if captured:
        try:
            capture = timestamp(captured)
            age = (now - capture).total_seconds()
            result['capture_age_seconds'] = age
            valid_until = min(timestamp(result['valid_until']), capture + timedelta(seconds=MAX_AGE_SECONDS))
            result['freshness'] = 'FRESH' if age >= 0 and now <= valid_until else 'EXPIRED'
        except (ValueError, TypeError):
            result['freshness'] = 'UNVERIFIED'
    if req and req.get('meeting') and result.get('freshness')=='FRESH':
        pending=handoffs(projection(forecast,req,now))
        if pending:result['form_assessment_requests']=pending
    if req and req.get('meeting') and state=='FAILED' and not result.get('form_assessment_requests'):
        with_form_handoff(result, req)
    if state == 'COMPLETED' and result.get('freshness') == 'FRESH' and req:
        view = projection(forecast, req, now)
        if view['races'] and all(race['result']['freshness_at_retrieval'] != 'FRESH AT CHECK TIME'
                                 for race in view['races']):
            result['freshness'] = 'EXPIRED' if all(
                race['result']['freshness_at_retrieval'].startswith(('CLOSED', 'STALE'))
                for race in view['races']) else 'UNVERIFIED'
        elif not view['races']:
            result.update(semantic_outcome='REQUEST_SCOPE_NOT_PRESENT', freshness='UNVERIFIED')
        else:
            result.update(view=view, ticket=ticket(view, now=now), html=render(view, now=now))
    if state == 'COMPLETED' and req and result.get('freshness') == 'EXPIRED':
        try:
            historical = archived_rankings(forecast, req, now)
        except (ValueError, TypeError, KeyError):
            historical = []
        if historical:
            result['archived_assessments'] = historical
    return result


def with_workflow_status(result, req=None, now=None):
    run_id = (result['run_id'] or '').split('-', 1)[0]
    if not re.fullmatch(r'[0-9]+', run_id):
        return result
    try:
        run = transport.api(f'actions/runs/{run_id}', optional=True)
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError):
        run = None
    result.update(workflow_status=run.get('status') if run else None,
                  workflow_conclusion=run.get('conclusion') if run else None)
    if result['request_id'] is not None and result['request_status'] in transport.PENDING and result['workflow_status'] == 'completed':
        # The worker may have published between the initial read and the Actions query.
        index = transport.read(f"requests/{result['request_id']}.json")
        if transport.request_state(index) not in transport.PENDING:
            return dict(retrieve(index, result['request_id'], req if req and req['view'] != 'status' else None, now),
                        workflow_status=result['workflow_status'],
                        workflow_conclusion=result['workflow_conclusion'])
        result.update(request_status='FAILED', semantic_outcome='WORKFLOW_ENDED_WITHOUT_PUBLICATION')
        with_form_handoff(result, req)
    return result


def scope(req):
    # Each execution already computes both frozen versions and all views.
    return (req['date'], (req.get('meeting') or '').casefold(), req.get('race'), req.get('country'))


def wait_for_request(request_id, req, *, timeout=120, interval=3):
    """Poll exactly the accepted issue. A local timeout never changes its state."""
    deadline = monotonic() + timeout
    result = retrieve(None, request_id)
    while True:
        try:
            index = transport.read(f'requests/{request_id}.json')
            result = retrieve(index, request_id, req)
            if result['request_status'] not in transport.PENDING:
                return result
        except RETRIEVAL_ERRORS:
            result['delivery_status'] = 'RESULT_READ_UNAVAILABLE'
        remaining = deadline - monotonic()
        if remaining <= 0:
            try:
                result = with_workflow_status(result, req)
            except RETRIEVAL_ERRORS:
                pass
            if result['request_status'] not in transport.PENDING:
                return result
            reason = ('GITHUB_RESULT_READ_TIMEOUT' if result.get('delivery_status') else
                      'RESULT_PUBLICATION_TIMEOUT' if result.get('run_id') else 'WORKER_ACKNOWLEDGEMENT_TIMEOUT')
            return with_form_handoff(dict(result, delivery_status=reason, blockers=[reason]), req)
        sleep(min(interval, remaining))


def handle(text, *, date=None, country=None, request_id=None, now=None):
    day = date or (now or utcnow()).astimezone(TZ).date().isoformat()
    req = command(text, day, country)
    status_only=req['view']=='status'
    target=None
    if status_only and request_id is None:
        match=next(((n,item) for n,item in transport.requests(include_processed=True)
                    if item['date']==day and (not country or item['country']==country)),None)
        if match:request_id,target=match
        else:
            index=transport.read(f'daily/{day}/latest.json')
            return with_workflow_status(retrieve(index,req=index.get('request') if index else None,now=now))
    if request_id is not None:
        index=transport.read(f'requests/{request_id}.json')
        target=(target or (index.get('request') if index else None)) if status_only else req
        if status_only and target is None:
            target=next((item for n,item in transport.requests(include_processed=True) if n==request_id),None)
        result=retrieve(index,request_id,target,now)
        return with_workflow_status(result,target,now) if status_only or result['request_status'] in transport.PENDING else result

    # Reuse only the newest matching scope, never an unrelated/older request.
    # A failed/expired newest request does not fall back to earlier selections.
    match=next(((n,item) for n,item in transport.requests(include_processed=True)
                if scope(item)==scope(req)),None)
    if match:
        number,_=match
        saved=retrieve(transport.read(f'requests/{number}.json'),number,req,now)
        if saved['request_status'] in transport.PENDING:
            return with_workflow_status(saved,req,now)
        legacy_block=bool(req.get('meeting') and any(r['result'].get('status') in ('BLOCKED','FAILED') and not r['result'].get('assessment_level') for r in saved.get('view',{}).get('races',[])))
        if not legacy_block and saved['request_status']=='COMPLETED' and saved.get('source_mode')=='LIVE' and ('view' in saved or 'form_assessment_requests' in saved):return saved
    elif req['command'] in ('RM6','RM7') and not country:
        saved=retrieve(transport.read(f'daily/{day}/latest.json'),req=req,now=now)
        legacy_block=bool(req.get('meeting') and any(r['result'].get('status') in ('BLOCKED','FAILED') and not r['result'].get('assessment_level') for r in saved.get('view',{}).get('races',[])))
        if not legacy_block and saved['request_status']=='COMPLETED' and saved.get('source_mode')=='LIVE' and ('view' in saved or 'form_assessment_requests' in saved):return saved
    number=transport.enqueue(req)
    return retrieve(None,number,now=now)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command')
    parser.add_argument('--date')
    parser.add_argument('--country', choices=['AU', 'NZ'])
    parser.add_argument('--request-id', type=int)
    parser.add_argument('--no-wait', action='store_true')
    args = parser.parse_args()
    result = handle(args.command, date=args.date, country=args.country, request_id=args.request_id)
    req = command(args.command, args.date, args.country)
    if (req['view'] != 'status' and not args.no_wait and result['request_id'] is not None
            and result['request_status'] in transport.PENDING):
        print(f"Monty request #{result['request_id']} — {result['request_status']}", file=sys.stderr, flush=True)
        result = wait_for_request(result['request_id'], req)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
