"""Retrospective policy sensitivity with unchanged frozen probabilities."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from betfair_history import convert
from monty.integrity import verify_artifacts
from monty.scoring import score_features

ROOT = Path(__file__).resolve().parents[2]
V7_COMMIT = 'efc51abb1595ef1eb8417e2d4e0d591f6d3c9378'
V7_SHA = 'c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324'
BANDS = ((1, 4), (4, 6), (6, 10), (10, 20), (20, 40), (40, np.inf))


def read_months(directory):
    register = json.loads((ROOT/'operations/audit/Monty_Betfair_Monthly_Recovery.json').read_text())
    months = [f'{year}_{month:02d}' for year, numbers in
              ((2025, range(7, 13)), (2026, (1, 2, 3, 4, 6, 8, 9, 10))) for month in numbers]
    frames = []
    for month in months:
        path = directory/f'{month}.csv'
        entry = register[month]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['source_sha256']:
            raise ValueError(f'Pinned source mismatch for {month}')
        rows, audit = convert(pd.read_csv(path, dtype=str, keep_default_na=False))
        if audit['retained_runners'] != entry['retained_runners'] or audit['retained_races'] != entry['retained_races']:
            raise ValueError(f'Canonical count drift for {month}')
        frames.append(rows)
    data = pd.concat(frames, ignore_index=True)
    if data.duplicated(['WIN_MARKET_ID', 'SELECTION_ID']).any():
        raise ValueError('Repeated market/runner across input months')
    return data


def fixed_predictors(v7_root):
    v6 = ROOT/'monty_v6'
    count = verify_artifacts(v6)
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=v7_root, text=True).strip() != V7_COMMIT:
        raise ValueError('Pinned V7 checkout required')
    if subprocess.check_output(['git', 'diff', 'HEAD', '--', 'v7/core.py'], cwd=v7_root):
        raise ValueError('Pinned V7 predictor modified')
    raw = (v7_root/'v7/artifacts/fold_3_model.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != V7_SHA:
        raise ValueError('Pinned V7 model mismatch')
    spec = importlib.util.spec_from_file_location('v7_policy_study', v7_root/'v7/core.py')
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    v7 = json.loads(raw)
    names = json.loads((v6/'results/frozen_model.json').read_text())['input_feature_names']
    if names != v7['names']:
        raise ValueError('Feature schema mismatch')

    def score(data, matrix):
        market, race = data.market_probability.to_numpy(), data.WIN_MARKET_ID
        return {'market': market, 'v6': score_features(matrix, names, market, race, root=v6),
                'v7': core.predict(v7, matrix, market, race)}
    return names, score, count


def minimal(data, names):
    field_size = data.groupby('WIN_MARKET_ID').SELECTION_ID.transform('size')
    matrix = np.full((len(data), len(names)), np.nan)
    for name, values in {'log_market_probability': np.log(data.market_probability),
                         'log_field_size': np.log(field_size), 'distance_km': data.DISTANCE/1000}.items():
        matrix[:, names.index(name)] = values
    return matrix


class DayBootstrap:
    def __init__(self, dates):
        self.index, calendar = pd.factorize(dates, sort=True)
        self.days = len(calendar)
        self.draws = np.random.default_rng(20261125).integers(self.days, size=(2000, self.days))

    def totals(self, mask, weights=None):
        return np.bincount(self.index[mask], weights=None if weights is None else weights[mask],
                           minlength=self.days)[self.draws].sum(axis=1)

    def interval(self, mask, values, denominator=None):
        den = self.totals(mask, denominator)
        num = self.totals(mask, values)
        valid = den > 0
        return np.quantile(num[valid]/den[valid], [.025, .975]).tolist() if valid.any() else [None, None]


def probability_metrics(data, predictions):
    winners = data.y.to_numpy().astype(bool)
    boot = DayBootstrap(data.date)
    odds = data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    gross = 1+.95*(odds-1)
    net_return = winners*gross-1
    rows = []
    key = data.WIN_MARKET_ID
    for name, p in predictions.items():
        ranked = pd.Series(p).groupby(key).rank(ascending=False, method='first').to_numpy()
        comparisons = [k for k in ('market', name.replace('_original_inputs', '_minimal'))
                       if k in predictions and k != name]
        for dimension, labels in [('all', np.full(len(data), 'ALL')),
                                  ('going', data.going.to_numpy()),
                                  ('race_type', data.RACE_TYPE.to_numpy())]:
            for label in np.unique(labels):
                group = labels == label
                win, top = group & winners, group & (ranked == 1)
                if not win.any():
                    continue
                delta = np.log(predictions['market']) - np.log(p)
                paired = {ref: {'mean': float(np.mean(np.log(predictions[ref][win])-np.log(p[win]))),
                                'ci': boot.interval(win, np.log(predictions[ref])-np.log(p))}
                          for ref in comparisons}
                rows.append(dict(model=name, dimension=dimension, value=label, races=int(win.sum()),
                                 runners=int(group.sum()), log_loss=float(-np.log(p[win]).mean()),
                                 paired_logloss_vs_market=float(delta[win].mean()),
                                 paired_logloss_ci=boot.interval(win, delta),
                                 race_brier=float(np.square(p[group]-winners[group]).sum()/win.sum()),
                                 mean_winner_rank=float(ranked[win].mean()), strike=float(winners[top].mean()),
                                 top_pick_mean_probability=float(p[top].mean()),
                                 top_pick_calibration_gap=float((winners-p)[top].mean()),
                                 top_pick_ev=float((p*gross-1)[top].mean()),
                                 top_pick_roi=float(net_return[top].mean()),
                                 top_pick_roi_ci=boot.interval(top, net_return), paired_logloss=paired))
    return rows


def policy_metrics(data, predictions):
    # Only earlier dates contribute to the empirical lower bound. Calibrates a
    # band's selected subset as a group, never a per-runner confidence interval.
    prior = data.date.lt('2026-05-01').to_numpy()
    test = data.date.ge('2026-06-01').to_numpy()
    before, after = DayBootstrap(data.date[prior]), DayBootstrap(data.date[test])
    odds = data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    book = pd.Series(1/odds).groupby(data.WIN_MARKET_ID).transform('sum').to_numpy() >= 1-1e-12
    gross = 1+.95*(odds-1)
    adverse = 1+.95*.98*(odds-1)
    wins = data.y.to_numpy()
    actual = wins*gross-1
    observations = []
    for name, p in predictions.items():
        for lo, hi in BANDS:
            band = (odds >= lo) & (odds < hi)
            calibration = band & book & ((p*gross-1) > 1e-12)
            sample = calibration[prior]
            lower = None
            if sample.sum() >= 100 and data.loc[prior].date[sample].nunique() >= 30:
                lower = before.interval(sample, wins[prior], p[prior])[0]
            rules = {
                'all_runners': band, 'point_positive_6pct': band & book & (p >= .06) & (p*odds > 1+1e-12),
                'point_positive_3pct': band & book & (p >= .03) & (p*odds > 1+1e-12),
                'point_positive_no_floor': band & book & (p*odds > 1+1e-12),
                'positive_net_ev': calibration,
                'commission_and_2pct_price_haircut': band & book & (p*adverse > 1+1e-12),
                'prior_band_lower_bound_at_haircut': calibration & (p*min(1, lower or 0)*adverse > 1+1e-12),
            }
            for rule, mask in rules.items():
                subset = mask & test
                result = dict(model=name, band_floor=lo, policy=rule, runners=int(subset.sum()),
                              prior_candidates=int(sample.sum()), prior_band_lower_ratio=lower)
                if subset.any():
                    result.update(wins=int(wins[subset].sum()), strike=float(wins[subset].mean()),
                                  mean_probability=float(p[subset].mean()),
                                  calibration_gap=float((wins-p)[subset].mean()),
                                  calibration_gap_ci=after.interval(mask[test], (wins-p)[test]),
                                  ev=float((p*gross-1)[subset].mean()), roi=float(actual[subset].mean()),
                                  roi_ci=after.interval(mask[test], actual[test]),
                                  adverse_roi=float((wins*adverse-1)[subset].mean()))
                observations.append(result)
    return observations


def archive_price_band_metrics(data, predictions):
    odds = data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    wins = data.y.to_numpy()
    gross = 1+.95*(odds-1)
    actual = wins*gross-1
    book = pd.Series(1/odds).groupby(data.WIN_MARKET_ID).transform('sum').to_numpy() >= 1-1e-12
    boot = DayBootstrap(data.date)
    output = []
    for name, p in predictions.items():
        for lo, hi in BANDS:
            band = (odds >= lo) & (odds < hi)
            edge = p*gross-1
            for sample, mask in (('all_runners', band), ('positive_net_ev', band & book & (edge > 1e-12))):
                row = dict(model=name, band_floor=lo, sample=sample, runners=int(mask.sum()))
                if mask.any():
                    row.update(wins=int(wins[mask].sum()), strike=float(wins[mask].mean()),
                               calibration_gap=float((wins-p)[mask].mean()),
                               calibration_gap_ci=boot.interval(mask, wins-p),
                               runner_brier=float(np.square(p-wins)[mask].mean()),
                               expected_ev=float(edge[mask].mean()), exchange_roi=float(actual[mask].mean()),
                               roi_ci=boot.interval(mask, actual))
                output.append(row)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('months', type=Path)
    parser.add_argument('v7', type=Path)
    parser.add_argument('output', type=Path)
    a = parser.parse_args()
    names, score, verified = fixed_predictors(a.v7)
    data = read_months(a.months)
    later = data.date.ge('2026-06-01').to_numpy()
    p = score(data, minimal(data, names))
    root = ROOT/'monty_v6/results'
    original = pd.read_csv(root/'joined_development_runners.csv.gz', dtype={'WIN_MARKET_ID': str})
    with np.load(root/'frozen_feature_matrix.npz', allow_pickle=False) as frozen:
        if frozen['names'].tolist() != names or len(frozen['X']) != len(original):
            raise ValueError('Historical matrix identity/schema mismatch')
        original['archive_row'] = np.arange(len(original))
        original = original.loc[original.date.between('2025-06-01', '2025-06-15')].reset_index(drop=True)
        complete = frozen['X'][original.archive_row.to_numpy()]
    full_p = score(original, complete)
    sparse_p = score(original, minimal(original, names))
    active_v6 = json.loads((root/'frozen_model.json').read_text())['numeric_feature_names']
    active_v6 = [names.index(n) for n in active_v6[:len(active_v6)//2]]
    raw_v7 = json.loads((a.v7/'v7/artifacts/fold_3_model.json').read_text())
    active_v7 = np.asarray(raw_v7['active'], bool)
    historic_predictions = {'market': full_p['market'], 'v6_minimal': sparse_p['v6'], 'v7_minimal': sparse_p['v7'],
                             'v6_original_inputs': full_p['v6'], 'v7_original_inputs': full_p['v7']}
    report = dict(verified_v6_artifacts=verified, v7_commit=V7_COMMIT,
                  prior_dates=['2025-07-01', '2026-04-30'],
                  later_dates=['2026-06-01', '2026-10-31'], excluded_months=['2026-05', '2026-07'],
                  later_probability_metrics=probability_metrics(data.loc[later].reset_index(drop=True),
                                                                {k:v[later] for k,v in p.items()}),
                  later_policy_metrics=policy_metrics(data, p),
                  original_archive_dates=['2025-06-01', '2025-06-15'],
                  original_archive_probability_metrics=probability_metrics(original, historic_predictions),
                  original_archive_price_bands=archive_price_band_metrics(original, historic_predictions),
                  original_archive_coverage=dict(runners=len(original), all_inputs_complete=int(np.isfinite(complete).all(axis=1).sum()),
                      active_v7_inputs_complete=int(np.isfinite(complete[:,active_v7]).all(axis=1).sum()),
                      median_observed_inputs=float(np.median(np.isfinite(complete).sum(axis=1))),
                      active_v6_inputs_complete=int(np.isfinite(complete[:,active_v6]).all(axis=1).sum()),
                      per_feature_observed=dict(zip(names, np.isfinite(complete).sum(axis=0).tolist()))),
                  limitations=['Already accessed historical test dates; no prospective holdout.',
                               'Scheduled-off exchange best-back, no verified fill/liquidity or bookmaker quote.',
                               'Flat per-selection unit and 5% winner commission proxy, not exchange net-market settlement.',
                               'Original archive comparison uses frozen V7 fold 3 on its June test period; shared historical context was previously exposed.'])
    with a.output.open('x') as f:
        json.dump(report, f, allow_nan=False, indent=2)
        f.write('\n')


if __name__ == '__main__':
    main()
