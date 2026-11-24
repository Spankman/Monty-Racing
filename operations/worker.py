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
from operations.transport import publish, read, record_request, request_state, requests, write_index


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


def main():
    started = monotonic()
    now = datetime.now(ZoneInfo('Australia/Brisbane'))
    day = now.date().isoformat()
    mode = os.environ.get('OPERATIONS_MODE', 'daily')
    issue = os.environ.get('OPERATIONS_ISSUE', '')
    workflow_id = os.environ['GITHUB_RUN_ID']
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    workflow_url = f'https://github.com/Spankman/Monty-Racing/actions/runs/{workflow_id}'
    if mode == 'queue':
        with timed('queue_discovery', f'{workflow_id}-{attempt}'):
            items = list(requests())
        # The event's request goes first; also drain older pending requests.
        # GitHub retains only one pending job in a concurrency group, so a
        # worker restricted to its own issue can strand cancelled burst events.
        items.sort(key=lambda item: (bool(issue) and item[0] != int(issue), item[0]))
        items = items[:10]
        if not issue and daily_due(now, read(f'daily/{day}/latest.json')):
            items.insert(0, (None, command('RM6', day)))
    else:
        items = [(None, command(os.environ.get('OPERATIONS_COMMAND') or 'RM6',
                                os.environ.get('OPERATIONS_DATE') or day))]
    pending = []
    for number, req in items:
        if req['view'] == 'status':
            continue
        run_id = f'{workflow_id}-{attempt}-{number if number else "daily"}'
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
        pending.append((number, req, run_id))

    publication_failed = False
    completed = {}
    from operations.client import scope, retrieve
    for number, req, run_id in pending:
        # Leave work queued for the next tick if another full inference may exceed the job budget.
        if monotonic() - started > RUNNER_TIMEOUT:
            break
        out = Path('operations_output') / run_id
        try:
            source=completed.get(scope(req))
            if number is not None and source and source.get('request_status')=='COMPLETED':
                cached=retrieve(source,req=req)
                if cached.get('source_mode')=='LIVE' and ('view' in cached or 'form_assessment_requests' in cached):
                    reused=dict(source,request_id=number,request=req,reused_from_request=source.get('request_id'))
                    record_request(reused)
                    print(json.dumps(reused))
                    continue
            result=operate(req, number, run_id, workflow_url, out)
            completed[scope(req)]=result
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
