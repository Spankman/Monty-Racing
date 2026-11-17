"""Audit a captured Monty field before any live betting labels are permitted.

This does not create form histories, verify TAB, or validate a betting strategy.
"""
import argparse
import datetime as dt
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo
from race_day import ROOT
from monty.integrity import verify_artifacts, validate_model_contract


def timestamp(value):
    value = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return value


def assess(bundle, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    captured = timestamp(bundle['captured_at_utc'])
    age = (now - captured).total_seconds()
    snapshot = bundle['snapshot']
    if snapshot['date'] != now.astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat():
        raise ValueError('Snapshot is not for the current Queensland date')
    model = json.loads((ROOT / 'results/frozen_model.json').read_text())
    active = validate_model_contract(model, model['input_feature_names'])
    verified = verify_artifacts(ROOT)
    metadata = {(str(r['meeting']), str(r['race'])): r for r in bundle.get('races', [])}
    groups = {}
    for row in snapshot['runners']:
        groups.setdefault((str(row['meeting']), str(row['race'])), []).append(row)
    decisions = []
    for key, rows in groups.items():
        meta = metadata.get(key, {})
        jump = meta.get('jump_time') or meta.get('race_metadata', {}).get('jump_time')
        reasons = []
        if not 0 <= age <= 300:
            reasons.append('snapshot_not_fresh')
        try:
            if timestamp(jump) <= now:
                reasons.append('race_already_due')
        except (TypeError, ValueError):
            reasons.append('jump_time_unverified')
        if bundle.get('audit', {}).get('tab_verified') is not True:
            reasons.append('independent_fields_and_scratchings_unverified')
        # A capture timestamp is not evidence of the underlying quote's age.
        capture_only = bundle.get('audit', {}).get('quote_time_policy') == 'capture_only'
        if not capture_only:
            reasons.append('provider_quote_update_time_unverified')
        counts = {}
        for feature in active:
            if feature in ('log_field_size', 'log_market_probability'):
                counts[feature] = len(rows)
            else:
                counts[feature] = sum(isinstance(r.get(feature), (int, float))
                                      and not isinstance(r.get(feature), bool)
                                      and math.isfinite(r[feature]) for r in rows)
        missing = [f for f, count in counts.items() if count != len(rows)]
        if missing:
            reasons.append('active_form_features_incomplete')
        decisions.append(dict(meeting=key[0], race=key[1], runners=len(rows),
                              decision='BLOCKED', reasons=reasons,
                              fully_observed_active_features=len(active)-len(missing),
                              active_features=len(active), missing_features=missing,
                              quote_time_policy='capture_only' if capture_only else 'provider_update_required',
                              warnings=['Provider update time unknown; capture-time-only pricing accepted by user.'] if capture_only else []))
    if not decisions:
        raise ValueError('No runner fields to assess')
    return dict(assessed_at_utc=now.isoformat(), captured_at_utc=captured.isoformat(),
                artifact_hashes=verified, betting_ready=False, predictions_generated=False,
                races=decisions, next_requirement='As-of form features, independently verified fields/scratchings and captured current fixed-win odds; then prospective model validation.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot_bundle', help='JSON with captured_at_utc, snapshot, audit and races')
    parser.add_argument('--output', default='race_day_output/readiness.json')
    args = parser.parse_args()
    report = assess(json.loads(Path(args.snapshot_bundle).read_text()))
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'report': str(target), 'races': len(report['races']), 'betting_ready': False}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
