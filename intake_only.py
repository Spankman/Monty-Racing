"""Capture Krok input and coverage; never score or emit betting selections."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import uuid
from zoneinfo import ZoneInfo

from krok_adapter import fetch, normalize
from monty.integrity import verify_artifacts, validate_model_contract

ROOT = Path(__file__).resolve().parent


def capture(date, output, fixture=None):
    dt.date.fromisoformat(date)
    verified = verify_artifacts(ROOT / 'monty_v6')
    model = json.loads((ROOT / 'monty_v6/results/frozen_model.json').read_text())
    names = model['input_feature_names']
    active = validate_model_contract(model, names)
    key = os.environ.get('KROK_API_KEY', '')
    if fixture is None and not key:
        raise ValueError('KROK_API_KEY is absent; live ingestion was not attempted.')
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = json.loads(Path(fixture).read_text()) if fixture else fetch(date, key)
    # Never retain a provider echo of the credential in captured files.
    encoded = json.dumps(payload)
    if key:
        encoded = encoded.replace(key, '[REDACTED]')
    payload = json.loads(encoded)
    snapshot, audit = normalize(payload, date)
    # User-approved capture-time-only fixed-win quote policy. This is a policy
    # declaration, NOT proof of the bookmaker's last quote update or TAB verification.
    audit['quote_time_policy'] = 'capture_only'
    captured = dt.datetime.now(dt.timezone.utc)
    out = Path(output) / (captured.strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    coverage = {}
    for name in active:
        if name in ('log_market_probability', 'log_field_size'):
            coverage[name] = {'status': 'derivable_from_accepted_field', 'runners': len(snapshot['runners'])}
        else:
            count = sum(name in row for row in snapshot['runners'])
            coverage[name] = {'status': 'present' if count else 'missing', 'runners': count}
    report = dict(requested_date=date, fetch_started_utc=started, captured_at_utc=captured.isoformat(),
                  source='local_fixture' if fixture else 'Krok Odds API', live=fixture is None,
                  artifact_hashes=verified, adapter_audit=audit, active_feature_coverage=coverage,
                  predictions_generated=False, betting_ready=False,
                  limitations=['Coverage is field presence, not verification of meaning or freshness.',
                               'Historical features are not built from this feed.',
                               'Independent TAB verification is still required.',
                               'Capture time is not a verified quote-update time.',
                               'AU/NZ meeting completeness is not independently established.'])
    race_times = [dict(meeting=m.get('venue'), race=str(r.get('number')), jump_time=r.get('jump_time'))
                  for m in payload['data'] for r in m.get('races', [])
                  if m.get('country') in ('AU', 'NZ', None)]
    bundle = dict(captured_at_utc=captured.isoformat(), snapshot=snapshot, audit=audit, races=race_times)
    for filename, value in [('assessment_bundle.json', bundle), ('provider_response.json', payload), ('snapshot.json', snapshot), ('intake_report.json', report)]:
        (out / filename).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    return out, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', default=dt.datetime.now(ZoneInfo('Australia/Brisbane')).date().isoformat())
    parser.add_argument('--output-dir', default='intake_output')
    parser.add_argument('--fixture', help='Offline input only; explicitly labelled non-live.')
    args = parser.parse_args()
    try:
        out, report = capture(args.date, args.output_dir, args.fixture)
    except ValueError as exc:
        # ValueErrors from adapters contain no credential-bearing request objects.
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print('BLOCKED: ingestion failed (' + type(exc).__name__ + '); no predictions generated.', file=sys.stderr)
        return 2
    from assess_day import assess
    readiness = assess(json.loads((out / 'assessment_bundle.json').read_text()))
    (out / 'readiness.json').write_text(json.dumps(readiness, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(out), 'live': report['live'],
                      'races': report['adapter_audit']['races_accepted'], 'predictions_generated': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
