"""Offline, fixed-coefficient V6 ablation on the already-exposed diagnostic set."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'monty_v6'))
from monty.integrity import verify_artifacts
from monty.scoring import score_features


def run(frozen, live_observed):
    verify_artifacts(frozen)
    results = frozen / 'results'
    with np.load(results / 'frozen_feature_matrix.npz', allow_pickle=False) as archive:
        names = archive['names'].tolist()
        matrix = archive['X']
    rows = pd.read_csv(results / 'joined_development_runners.csv.gz',
                       dtype={'WIN_MARKET_ID': str, 'SELECTION_ID': str})
    rows = rows.loc[rows.date.ge('2025-05-01')].reset_index(drop=True)
    matrix = matrix[-len(rows):]
    groups = rows.groupby('WIN_MARKET_ID', sort=False)
    wins = rows.y.to_numpy() == 1
    odds = rows.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    market = rows.market_probability.to_numpy()
    rng = np.random.default_rng(20261125)
    days = rows.loc[wins, 'date']
    day_index, dates = pd.factorize(days, sort=True)
    samples = rng.integers(len(dates), size=(4000, len(dates)))
    day_sizes = np.bincount(day_index)

    def score(data):
        return score_features(data, names, market, rows.WIN_MARKET_ID, root=frozen)

    def metrics(probabilities, reference):
        loss = -np.log(probabilities[wins])
        diff = loss + np.log(reference[wins])
        by_day = np.bincount(day_index, weights=diff)
        bootstrap = by_day[samples].sum(axis=1) / day_sizes[samples].sum(axis=1)
        top = pd.Series(probabilities).groupby(rows.WIN_MARKET_ID, sort=False).idxmax().to_numpy()
        net = np.where(wins[top], (odds[top] - 1) * .95, -1)
        equity = np.r_[0, np.cumsum(net)]
        return dict(races=groups.ngroups, log_loss=loss.mean(),
                    brier=np.square(probabilities - wins).sum()/groups.ngroups,
                    top_pick_strike_rate=wins[top].mean(),
                    top_pick_quote_proxy_roi=net.mean(),
                    top_pick_quote_proxy_drawdown=float((np.maximum.accumulate(equity) - equity).max()),
                    paired_log_loss_difference=float(diff.mean()),
                    day_bootstrap_95=np.quantile(bootstrap, [.025, .975]).tolist())

    full = score(matrix)
    live_cols = [i for i, name in enumerate(names) if name in live_observed]
    masked = np.full_like(matrix, np.nan)
    masked[:, live_cols] = matrix[:, live_cols]
    sparse = score(masked)
    individual = {}
    for i, name in enumerate(names):
        without_one = matrix.copy()
        without_one[:, i] = np.nan
        full_delta = metrics(score(without_one), full)
        with_one = masked.copy()
        with_one[:, i] = matrix[:, i]
        sparse_delta = metrics(score(with_one), sparse)
        individual[name] = dict(full_mask_delta=full_delta['paired_log_loss_difference'],
                                full_mask_ci=full_delta['day_bootstrap_95'],
                                sparse_restore_delta=sparse_delta['paired_log_loss_difference'],
                                sparse_restore_ci=sparse_delta['day_bootstrap_95'])
    return dict(dates=[rows.date.min(), rows.date.max()], runners=len(rows),
                history_dates=pd.read_csv(results / 'joined_development_runners.csv.gz',
                                          usecols=['date']).date.agg(['min','max']).tolist(),
                market=metrics(market, market), v6_full=metrics(full, market),
                v6_sparse_mask=metrics(sparse, market), full_vs_sparse=metrics(full, sparse),
                live_mask=sorted(live_observed), features=individual,
                scope='Already-exposed historical AU races, scheduled-off exchange quote proxy.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('forecast', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    races = json.loads(args.forecast.read_text())['races']
    counts = [r['models']['V6']['input_evidence']['observed_counts'] for r in races
              if r['models']['V6']['status'] == 'SCORED']
    if not counts:
        parser.error('Forecast has no scored V6 races')
    live = {name for name in counts[0] if all(row[name] > 0 for row in counts)}
    result = run(ROOT / 'monty_v6', live)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
