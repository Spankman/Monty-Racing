"""Emit monotonic stage durations without exposing input data or exceptions."""
from contextlib import contextmanager
import json
from math import isfinite
import sys
from time import monotonic


PREFIX = 'MONTY_TIMING '
RUNNER_STAGES = frozenset({'frozen_verification', 'provider_fetch'})


def emit(stage, elapsed, outcome, run_id):
    print(PREFIX + json.dumps(dict(stage=stage, elapsed_seconds=round(elapsed, 3),
                                  outcome=outcome, run_id=run_id)),
          file=sys.stderr, flush=True)


@contextmanager
def timed(stage, run_id, *, enabled=True):
    if not enabled:
        yield
        return
    started = monotonic()
    outcome = 'ok'
    try:
        yield
    except BaseException:
        outcome = 'error'
        raise
    finally:
        emit(stage, monotonic() - started, outcome, run_id)


def forward_runner_timings(output, run_id):
    """Only forward known stages and validated values from captured stderr."""
    if isinstance(output, bytes):
        output = output.decode(errors='replace')
    for line in (output or '').splitlines():
        if not line.startswith(PREFIX):
            continue
        try:
            entry = json.loads(line[len(PREFIX):])
            stage, seconds, outcome = (entry[k] for k in ('stage', 'elapsed_seconds', 'outcome'))
            if (stage in RUNNER_STAGES and type(seconds) in (int,float)
                    and 0 <= seconds <= 86400 and isfinite(seconds) and outcome in ('ok','error')):
                emit(stage, seconds, outcome, run_id)
        except (ValueError, TypeError, KeyError):
            continue
