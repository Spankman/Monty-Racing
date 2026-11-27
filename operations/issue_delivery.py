"""Deliver and recover bounded Monty status and results on the originating issue."""
import hashlib
import json
import os
import subprocess

from monty_operations import projection, ticket, utcnow
from operations import transport


BOT = 'github-actions[bot]'
DELIVERY_ERRORS = (RuntimeError, ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError)


def enabled():
    return os.getenv('OPERATIONS_ISSUE_COMMENTS') == '1'


def marker(issue, phase):
    return f'<!-- monty-request:{issue}:{phase} -->'


def find(issue, phase):
    rows = transport.api(f'issues/{issue}/comments?per_page=100')
    tag = marker(issue, phase)
    return next((row for row in rows if (row.get('user') or {}).get('login') == BOT
                 and (row.get('body') or '').startswith(tag)), None)


def send(issue, phase, body):
    """Keep one bot comment per phase, including when a POST response is lost."""
    def write():
        existing = find(issue, phase)
        if existing:
            return existing
        return transport.api(f'issues/{issue}/comments', 'POST', {'body': marker(issue, phase) + '\n' + body})

    return transport.retry(write)


def report(issue, phase, body):
    try:
        return send(issue, phase, body)
    except DELIVERY_ERRORS as exc:
        print(json.dumps(dict(request_id=issue, phase=phase, issue_delivery_error=type(exc).__name__,
                              github_status=getattr(exc, 'status', None))))
        return None


def links(index):
    lines = []
    for label, key in [('Forecast', 'forecast_path'), ('Receipt', 'receipt_path')]:
        if index.get(key):
            lines.append(f"[{label}](https://github.com/{transport.REPO}/blob/{transport.BRANCH}/{index[key]})")
    return ' · '.join(lines)


def result_body(request, forecast, receipt, index):
    view = projection(forecast, request, utcnow())
    status = index['request_status']
    lines = [f"**Monty {status} — {forecast['status']}**", '',
             f"Requested view: `{request['command']}` · {forecast['date']} (Brisbane)",
             f"Run: `{forecast['run_id']}` · [Workflow]({index['workflow_url']})", '']
    model = forecast.get('models', {}).get(request['version'], {})
    lines.append(f"Requested model: {request['version']} · {model.get('status', 'NOT RUN')} · "
                 f"{model.get('scored_races', 0)} races scored · Source mode: {forecast.get('source_mode', 'UNKNOWN')}")
    if forecast.get('provider_snapshot_sha256'):
        lines.append('Field and odds data: ' + forecast.get('provider', 'Krok') + ' snapshot · SHA-256 `' + forecast['provider_snapshot_sha256'] + '`')
    if index.get('reused_from_request'):
        lines.append(f"Shared capture with verified file integrity from request #{index['reused_from_request']}.")
    if forecast.get('captured_at'):
        lines += [f"Captured: {forecast['captured_at']} · Valid until: {forecast.get('valid_until')}",
                  'Recheck the five-minute limit and race jump at retrieval. Expired slips are historical.', '']
    if forecast.get('delivery_status'):
        lines.append(f"Delivery: {forecast['delivery_status']}")
    if view['races']:
        lines.append(ticket(view))
    for race in view['races']:
        lines.append(f"{race['meeting']} R{race['race']} scheduled jump: {race.get('scheduled_start')}")
    if forecast.get('blockers'):
        lines.append('Outcome details: ' + '; '.join(forecast['blockers']))
    if request.get('meeting') and not any(r['result'].get('ordered_selections') for r in view['races']):
        lines.append('No current Monty model selections for this race. See the model status and blockers above.')
    if index.get('forecast_path'):
        lines += ['', links(index)]
    else:
        lines += ['', 'Results-branch publication unavailable. The verified slip is above; see the workflow artifact for files.']
    lines += [f"Forecast SHA-256: `{receipt['forecast_sha256']}`",
              f"Receipt SHA-256: `{index['receipt_sha256']}`"]
    return '\n'.join(lines)


def local_result(req, issue, run_id, workflow_url, public):
    raw = (public / 'forecast.json').read_bytes()
    receipt_raw = (public / 'receipt.json').read_bytes()
    forecast, receipt = json.loads(raw), json.loads(receipt_raw)
    if (forecast['run_id'] != run_id or receipt['run_id'] != run_id
            or forecast['date'] != req['date'] or receipt['date'] != req['date']
            or forecast['status'] != receipt['status']
            or hashlib.sha256(raw).hexdigest() != receipt['forecast_sha256']):
        raise ValueError('Issue result integrity mismatch')
    index = dict(request_id=issue, run_id=run_id, workflow_url=workflow_url, request=req,
                 status=forecast['status'], request_status='FAILED' if forecast['status'] == 'FAILED' else 'COMPLETED',
                 forecast_integrity_verified=True, forecast_sha256=receipt['forecast_sha256'],
                 receipt_sha256=hashlib.sha256(receipt_raw).hexdigest())
    return forecast, receipt, index


def archived_result(req, index):
    """Project a shared existing capture in the requested issue's model/view."""
    raw = transport.read_bytes(index['forecast_path'])
    receipt_raw = transport.read_bytes(index['receipt_path'])
    if hashlib.sha256(raw).hexdigest() != index['forecast_sha256'] or hashlib.sha256(receipt_raw).hexdigest() != index['receipt_sha256']:
        raise ValueError('Stored issue result integrity mismatch')
    forecast, receipt = json.loads(raw), json.loads(receipt_raw)
    if receipt['forecast_sha256'] != index['forecast_sha256'] or forecast['run_id'] != index['run_id']:
        raise ValueError('Stored issue result run mismatch')
    return result_body(req, forecast, receipt, index)
