"""Run queued commands without executing request text as code."""
from datetime import datetime, time
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monty_operations import command, utcnow
from operations import issue_delivery, transport
from operations.failure import failed
from operations.timing import forward_runner_timings, timed
from operations.transport import publish, read, record_request, request_for_issue, request_state, requests, write_index


RUNNER_TIMEOUT = 1000
SINGLE_RACE_TIMEOUT = 85


def daily_due(now, latest):
    return now.time() >= time(8, 10) and latest is None


def lifecycle(req, issue, run_id, workflow_url, state, reason=None):
    index = dict(schema='monty.operations.index.v1', date=req['date'], request_id=issue,
                 run_id=run_id, workflow_url=workflow_url, request_status=state,
                 status=state, updated_at=utcnow().isoformat(), request=req)
    if reason:
        index['blockers'] = [reason]
    if issue is not None:
        record_request(index)
    else:
        write_index(f"daily/{req['date']}/latest.json", index)
    return index


def operate(req, issue, run_id, workflow_url, out):
    issue_output = issue is not None and issue_delivery.enabled()
    if issue_output:
        issue_delivery.report(issue, 'running', f'**Monty RUNNING** · [Workflow]({workflow_url})')
    elif issue is not None:
        try:
            with timed('running_status_write', run_id):
                lifecycle(req, issue, run_id, workflow_url, 'RUNNING')
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError):
            record_publication_failure(req, issue, run_id, workflow_url)
            raise RuntimeError('publication_failed') from None
    args = [sys.executable, 'monty_operations.py', '--command', req['command'],
            '--date', req['date'], '--output', str(out), '--v7-root', 'v7_engine', '--run-id', run_id, '--timings']
    if req.get('country'):
        args += ['--country', req['country']]

    public = out / 'public'
    reason = None
    try:
        with timed('runner_total', run_id):
            run = subprocess.run(args, capture_output=True, text=True,
                                 timeout=SINGLE_RACE_TIMEOUT if req.get('meeting') else RUNNER_TIMEOUT)
        forward_runner_timings(run.stderr, run_id)
        if not (public / 'receipt.json').exists() or not (public / 'forecast.json').exists():
            reason = 'runner_startup_failed'
        elif run.returncode and json.loads((public / 'receipt.json').read_text())['status'] != 'FAILED':
            reason = 'runner_exited_without_clean_completion'
    except subprocess.TimeoutExpired as exc:
        forward_runner_timings(exc.stderr, run_id)
        reason = 'runner_timeout'
    except OSError:
        reason = 'runner_launch_failed'
    except (ValueError, KeyError):
        reason = 'runner_invalid_receipt'
    if reason:
        # Keep partial files out of the published failure and uploaded public directory.
        if public.exists():
            public.rename(out / 'incomplete')
        failed(out, run_id, req['date'], reason)

    if issue_output:
        forecast, receipt, local = issue_delivery.local_result(req, issue, run_id, workflow_url, public)
        def publish_once():
            existing = read(f'requests/{issue}.json')
            if existing and existing.get('run_id') == run_id and existing.get('forecast_sha256') == local['forecast_sha256']:
                return existing
            return publish(public, run_id, req['date'], issue, workflow_url, request=req)
        try:
            with timed('result_publication', run_id):
                index = transport.retry(publish_once, conflicts=True)
        except issue_delivery.DELIVERY_ERRORS as exc:
            print(json.dumps(dict(request_id=issue, stage='result_publication', error=type(exc).__name__,
                                  github_status=getattr(exc, 'status', None))), file=sys.stderr)
            index = local
        with timed('issue_result_delivery', run_id):
            if not issue_delivery.report(issue, 'terminal', issue_delivery.result_body(req, forecast, receipt, index)):
                raise RuntimeError('issue_result_delivery_failed')
        return index
    try:
        with timed('result_publication', run_id):
            return publish(public, run_id, req['date'], issue, workflow_url, request=req)
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError):
        completed = record_publication_failure(req, issue, run_id, workflow_url)
        if completed:
            return completed
        raise RuntimeError('publication_failed') from None


def record_publication_failure(req, issue, run_id, workflow_url):
    # A response may have been lost after a successful terminal write.
    path = f'requests/{issue}.json' if issue is not None else f"daily/{req['date']}/latest.json"
    try:
        index = read(path)
        if index and index.get('run_id') == run_id and index.get('receipt_path'):
            return index
        lifecycle(req, issue, run_id, workflow_url, 'FAILED', 'publication_failed')
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError):
        print(json.dumps(dict(request_id=issue, run_id=run_id, workflow_url=workflow_url,
                              status='FAILED', blocker='publication_status_unavailable')), file=sys.stderr)
    return None


def work_items(mode, issue, now, run_tag):
    day = now.date().isoformat()
    if mode != 'queue':
        yield None, command(os.environ.get('OPERATIONS_COMMAND') or 'RM6',
                            os.environ.get('OPERATIONS_DATE') or day)
        return

    number = int(issue) if issue else None
    primary = None
    if number is not None:
        try:
            with timed('event_issue_lookup', f'{run_tag}-{number}'):
                primary = transport.retry(lambda: request_for_issue(number))
            if primary is None and issue_delivery.enabled():
                url = f'https://github.com/{transport.REPO}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
                issue_delivery.report(number, 'terminal',
                    f'**Monty FAILED — request invalid or closed.** Put RM6, RM7, RM6PS, RM7PS '
                    f'or a track and race number in the title. [Workflow]({url})')
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError):
            # Fall back to normal discovery if the direct read was unavailable.
            pass
        if primary is not None:
            yield number, primary

    # Drain the backlog after publishing the event request. This shares fresh
    # captures for matching requests and recovers missed triggers.
    with timed('queue_discovery', run_tag):
        backlog = sorted(((n, req) for n, req in requests() if primary is None or n != number),
                         key=lambda item: (number is not None and item[0] != number, item[0]))
    if not issue and daily_due(now, read(f'daily/{day}/latest.json')):
        yield None, command('RM6', day)
    yield from backlog[:9 if primary is not None else 10]


def main():
    started = monotonic()
    now = datetime.now(ZoneInfo('Australia/Brisbane'))
    mode = os.environ.get('OPERATIONS_MODE', 'daily')
    issue = os.environ.get('OPERATIONS_ISSUE', '')
    workflow_id = os.environ['GITHUB_RUN_ID']
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    run_tag = f'{workflow_id}-{attempt}'
    workflow_url = f'https://github.com/Spankman/Monty-Racing/actions/runs/{workflow_id}'
    publication_failed = False
    completed = {}
    from operations.client import scope, retrieve
    for number, req in work_items(mode, issue, now, run_tag):
        # Leave work queued for the next tick if another full inference may exceed the job budget.
        if monotonic() - started > RUNNER_TIMEOUT:
            break
        if req['view'] == 'status':
            continue
        run_id = f'{run_tag}-{number if number is not None else "daily"}'
        out = Path('operations_output') / run_id
        try:
            if number is not None:
                issue_output = issue_delivery.enabled()
                try:
                    with timed('request_index_read', run_id):
                        index = read(f'requests/{number}.json')
                except issue_delivery.DELIVERY_ERRORS:
                    if not issue_output:
                        raise
                    index = None
                state = request_state(index)
                if issue_output and state in ('QUEUED', 'RUNNING'):
                    try:
                        terminal = transport.retry(lambda: issue_delivery.find(number, 'terminal'))
                    except issue_delivery.DELIVERY_ERRORS:
                        terminal = None
                    if terminal:
                        continue
                elif issue_output:
                    if index.get('forecast_path') and not issue_delivery.find(number, 'terminal'):
                        if not issue_delivery.report(number, 'terminal', issue_delivery.archived_result(req, index)):
                            raise RuntimeError('issue_result_delivery_failed')
                    continue
                if state == 'RUNNING' and not issue_output:
                    # Global workflow concurrency means the previous worker has ended.
                    lifecycle(req, number, index['run_id'], index['workflow_url'], 'FAILED', 'worker_interrupted')
                    continue
                if not issue_output and state != 'QUEUED':
                    continue
                if not issue_output:
                    try:
                        with timed('queued_status_write', run_id):
                            lifecycle(req, number, run_id, workflow_url, 'QUEUED')
                    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError):
                        record_publication_failure(req, number, run_id, workflow_url)
                        raise RuntimeError('publication_failed') from None

            source = completed.get(scope(req))
            if number is not None and issue_output and not source:
                try:
                    source = transport.recent_scope_index(req, number, utcnow())
                except issue_delivery.DELIVERY_ERRORS:
                    pass  # A duplicate lookup failure must not prevent a fresh execution.
            if (number is not None and source and source.get('request_status') == 'COMPLETED'
                    and (not issue_output or transport.reusable(source, req, utcnow()))):
                try:
                    cached = transport.retry(lambda: retrieve(source, req=req)) if issue_output else retrieve(source, req=req)
                except issue_delivery.DELIVERY_ERRORS:
                    if not issue_output:
                        raise
                    cached = {}
                if cached.get('source_mode') == 'LIVE' and cached.get('provider') == os.getenv('MONTY_PRICE_PROVIDER','PuntersEdge') and ('view' in cached or cached.get('private_delivery') and cached.get('freshness')=='FRESH'):
                    reused = dict(source, request_id=number, request=req, reused_from_request=source.get('request_id'))
                    if issue_output:
                        body = issue_delivery.archived_result(req, reused)
                        try:
                            transport.retry(lambda: record_request(reused), conflicts=True)
                        except issue_delivery.DELIVERY_ERRORS as exc:
                            print(json.dumps(dict(request_id=number, stage='reuse_index',
                                                  github_status=getattr(exc, 'status', None))), file=sys.stderr)
                        if not issue_delivery.report(number, 'terminal', body):
                            raise RuntimeError('issue_result_delivery_failed')
                    else:
                        record_request(reused)
                    print(json.dumps(reused))
                    continue
            result = operate(req, number, run_id, workflow_url, out)
            completed[scope(req)] = result
            print(json.dumps(result))
        except issue_delivery.DELIVERY_ERRORS as exc:
            if number is not None and issue_delivery.enabled():
                try:
                    saved = read(f'requests/{number}.json')
                    body = issue_delivery.archived_result(req, saved) if saved and saved.get('forecast_path') else None
                except issue_delivery.DELIVERY_ERRORS:
                    body = None
                issue_delivery.report(number, 'terminal', body or
                    f'**Monty FAILED** · Worker or issue delivery interrupted ({type(exc).__name__}). '
                    f'[Workflow]({workflow_url}). Check any verified result under the same request before retrying.')
            elif str(exc) != 'publication_failed':
                raise
            publication_failed = True
            print(json.dumps(dict(request_id=number, run_id=run_id, workflow_url=workflow_url,
                                  status='FAILED', blocker='publication_failed')), file=sys.stderr)
    if publication_failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
