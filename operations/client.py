"""Request and retrieval contract. C only uses read operations."""
import argparse
from datetime import timedelta
import hashlib
import json
import re
import subprocess

from monty_operations import MAX_AGE_SECONDS, TZ, command, projection, ticket, timestamp, utcnow
from operations import transport
from operations.render import render


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
        return result
    try:
        raw = transport.read_bytes(index['forecast_path'])
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
        return dict(result, semantic_outcome='INTEGRITY_CHECK_FAILED')
    result.update(receipt=receipt, receipt_path=index['receipt_path'],
                  captured_at=forecast.get('captured_at'), valid_until=forecast.get('valid_until'),
                  blockers=forecast.get('blockers', []), source_mode=forecast.get('source_mode'))
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
    if state == 'COMPLETED' and result.get('freshness') == 'FRESH' and req:
        view = projection(forecast, req, now)
        if view['races'] and all(race['result']['freshness_at_retrieval'] != 'FRESH AT CHECK TIME'
                                 for race in view['races']):
            result['freshness'] = 'EXPIRED' if all(
                race['result']['freshness_at_retrieval'].startswith(('CLOSED', 'STALE'))
                for race in view['races']) else 'UNVERIFIED'
        else:
            result.update(view=view, ticket=ticket(view, now=now), html=render(view, now=now))
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
    if result['request_status'] == 'RUNNING' and result['workflow_status'] == 'completed':
        # The worker may have published between the initial read and the Actions query.
        index = transport.read(f"requests/{result['request_id']}.json")
        if transport.request_state(index) not in transport.PENDING:
            return dict(retrieve(index, result['request_id'], req if req and req['view'] != 'status' else None, now),
                        workflow_status=result['workflow_status'],
                        workflow_conclusion=result['workflow_conclusion'])
        result.update(request_status='FAILED', semantic_outcome='WORKFLOW_ENDED_WITHOUT_PUBLICATION')
    return result


def handle(text, *, date=None, country=None, request_id=None, now=None):
    day = date or (now or utcnow()).astimezone(TZ).date().isoformat()
    req = command(text, day, country)
    if req['view'] == 'status':
        if request_id is None:
            request_id = next((n for n, item in transport.requests(include_processed=True)
                               if item['date'] == day and (not country or item['country'] == country)), None)
        if request_id is None:
            return with_workflow_status(retrieve(transport.read(f'daily/{day}/latest.json'), now=now))
    if request_id is not None:
        result = retrieve(transport.read(f'requests/{request_id}.json'), request_id,
                          None if req['view'] == 'status' else req, now)
        return with_workflow_status(result, req, now) if req['view'] == 'status' or result['request_status'] == 'RUNNING' else result

    if req['command'] in ('RM6', 'RM7') and not country:
        saved = retrieve(transport.read(f'daily/{day}/latest.json'), req=req, now=now)
        if saved.get('source_mode') == 'LIVE' and 'view' in saved:
            return saved
    # Following this exact ID is a separate read, never an automatic requeue.
    number = transport.enqueue(req)
    return retrieve(None, number, now=now)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command')
    parser.add_argument('--date')
    parser.add_argument('--country', choices=['AU', 'NZ'])
    parser.add_argument('--request-id', type=int)
    args = parser.parse_args()
    print(json.dumps(handle(args.command, date=args.date, country=args.country,
                            request_id=args.request_id), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
