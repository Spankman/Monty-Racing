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
from operations.failure import failed
from operations.timing import forward_runner_timings, timed
from operations.transport import publish, read, record_request, request_for_issue, request_state, requests, write_index


RUNNER_TIMEOUT = 1000


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
    if issue is not None:
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
            run = subprocess.run(args, capture_output=True, text=True, timeout=RUNNER_TIMEOUT)
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
                primary = request_for_issue(number)
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError):
            # Fall back to normal discovery if the direct read was unavailable.
            pass
        if primary is not None:
            yield number, primary

    # GitHub retains only one pending job per concurrency group. Even when the
    # event request publishes first, drain older requests in the same workflow.
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
                with timed('request_index_read', run_id):
                    index = read(f'requests/{number}.json')
                state = request_state(index)
                if state == 'RUNNING':
                    # Global workflow concurrency means the previous worker has ended.
                    lifecycle(req, number, index['run_id'], index['workflow_url'], 'FAILED', 'worker_interrupted')
                    continue
                if state != 'QUEUED':
                    continue
                try:
                    with timed('queued_status_write', run_id):
                        lifecycle(req, number, run_id, workflow_url, 'QUEUED')
                except (RuntimeError, ValueError, OSError, subprocess.SubprocessError):
                    record_publication_failure(req, number, run_id, workflow_url)
                    raise RuntimeError('publication_failed') from None

            source = completed.get(scope(req))
            if number is not None and source and source.get('request_status') == 'COMPLETED':
                cached = retrieve(source, req=req)
                if cached.get('source_mode') == 'LIVE' and ('view' in cached or 'form_assessment_requests' in cached):
                    reused = dict(source, request_id=number, request=req, reused_from_request=source.get('request_id'))
                    record_request(reused)
                    print(json.dumps(reused))
                    continue
            result = operate(req, number, run_id, workflow_url, out)
            completed[scope(req)] = result
            print(json.dumps(result))
        except RuntimeError as exc:
            if str(exc) != 'publication_failed':
                raise
            publication_failed = True
            print(json.dumps(dict(request_id=number, run_id=run_id, workflow_url=workflow_url,
                                  status='FAILED', blocker='publication_failed')), file=sys.stderr)
    if publication_failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
