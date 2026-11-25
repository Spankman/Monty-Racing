"""Aggregate admitted and independently settled races without fitting models."""
import argparse
from collections import Counter, defaultdict
from datetime import timezone
import hashlib
import json
import math
from pathlib import Path
from random import Random
from statistics import fmean
from tempfile import TemporaryDirectory

from operations.prospective import admission_blockers, settle, timestamp

ARMS = ('V6', 'V7', 'MARKET')
ODDS_BANDS = (4, 6, 10, 20, 40, math.inf)


def read_verified(path):
    with path.open('rb') as stream:
        raw = stream.read()
    receipt = json.loads(Path(str(path) + '.receipt.json').read_text())
    digest = hashlib.sha256(raw).hexdigest()
    if receipt['record_sha256'] != digest:
        raise ValueError('Forecast integrity mismatch')
    return json.loads(raw), digest


def report(entries, *, start, end):
    """Each entry identifies one predeclared AU race and its optional ledger files."""
    start, end = timestamp(start), timestamp(end)
    if start >= end:
        raise ValueError('Invalid predeclared cohort')
    counts = Counter()
    blockers = Counter()
    samples = {arm: [] for arm in ARMS}
    seen = set()
    with TemporaryDirectory() as scratch:
        for entry in entries:
            key = tuple(entry[field] for field in ('date', 'country', 'meeting', 'race'))
            if key in seen or key[1] != 'AU':
                raise ValueError('Duplicate race or non-AU entry')
            seen.add(key)
            counts['registered'] += 1
            if not entry.get('forecast'):
                counts['unavailable'] += 1
                blockers[entry['reason']] += 1
                if entry.get('settlement'):
                    raise ValueError('Settlement without a forecast')
                continue
            path = Path(entry['forecast'])
            record, digest = read_verified(path)
            if tuple(record[field] for field in ('date', 'country', 'meeting', 'race')) != key:
                raise ValueError('Forecast cohort identity mismatch')
            freeze_at = timestamp(record['frozen_at'])
            if not start <= freeze_at < end or not freeze_at < timestamp(record['scheduled_start']):
                raise ValueError('Forecast outside predeclared window or not pre-jump')
            reasons = admission_blockers(record)
            if record.get('cohort_admitted') is not True or reasons:
                counts['excluded'] += 1
                blockers.update(reasons or ['diagnostic_not_admitted'])
                if entry.get('settlement'):
                    raise ValueError('Excluded diagnostics cannot enter performance metrics')
                continue
            counts['admitted'] += 1
            if not entry.get('settlement'):
                counts['pending_settlement'] += 1
                continue
            saved = json.loads(Path(entry['settlement']).read_text())
            if saved['forecast_sha256'] != digest:
                raise ValueError('Settlement points at a different forecast')
            verified = settle(path, saved['official_result'], Path(scratch) / 'check.json',
                              now=timestamp(saved['settled_at']))
            if verified['metrics'] != saved['metrics']:
                raise ValueError('Settlement metric mismatch')
            counts['settled'] += 1
            winner = verified['official_result']['winners'][0]
            for arm in ARMS:
                rows = record['market_baseline'] if arm == 'MARKET' else record['models'][arm]['rows']
                samples[arm].append((key[0], verified['metrics'][arm], rows, winner))

    output = {'counts': dict(counts), 'blockers': dict(blockers),
              'predeclared_window': [x.astimezone(timezone.utc).isoformat() for x in (start, end)],
              'models': {}, 'actual_roi': None,
              'roi_definition': 'One-unit top-ranked WIN fixed-quote proxy. No stakes, fills, deductions or actual ROI inferred.'}
    for arm, data in samples.items():
        if not data:
            continue
        probability = defaultdict(list)
        proxy = []
        paired = defaultdict(list)
        for (day, metrics, rows, winner), (_, market, _, _) in zip(data, samples['MARKET']):
            for row in rows:
                band = next(bound for bound in ODDS_BANDS if row['odds'] < bound)
                probability[str(band)].append((row['probability'], row['number'] == winner))
            top = max(rows, key=lambda row: row['probability'])
            proxy.append(top['odds'] - 1 if top['number'] == winner else -1)
            paired[day].append(metrics['log_loss'] - market['log_loss'])
        output['models'][arm] = {
            'mean_log_loss': fmean(m['log_loss'] for _, m, _, _ in data),
            'mean_brier': fmean(m['brier'] for _, m, _, _ in data),
            'top_pick_strike': fmean(m['top_pick_won'] for _, m, _, _ in data),
            'top_pick_fixed_quote_proxy_roi': fmean(proxy),
            'paired_log_loss_delta_vs_market': fmean(delta for day in paired.values() for delta in day),
            'paired_log_loss_day_bootstrap_95': day_interval(paired),
            'calibration_by_odds_upper_bound': {
                band: {'runners': len(rows), 'mean_probability': fmean(p for p, _ in rows),
                       'observed_win_rate': fmean(y for _, y in rows)}
                for band, rows in probability.items()},
        }
    return output


def day_interval(days):
    values = [(sum(rows), len(rows)) for rows in days.values()]
    if len(values) < 2:
        return None
    rng = Random(226)
    draws = []
    for _ in range(2000):
        sample = rng.choices(values, k=len(values))
        draws.append(sum(total for total, _ in sample) / sum(n for _, n in sample))
    draws.sort()
    return [draws[49], draws[1949]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path)
    args = parser.parse_args()
    cohort = json.loads(args.cohort.read_text())
    print(json.dumps(report(cohort['races'], start=cohort['start'], end=cohort['end']), indent=2))


if __name__ == '__main__':
    main()
