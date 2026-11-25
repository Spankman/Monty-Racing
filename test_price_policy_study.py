import unittest

import pandas as pd

from operations.audit.price_policy_study import DayBootstrap, archive_price_band_metrics, policy_metrics


class PricePolicyStudyTests(unittest.TestCase):
    def test_point_ev_floors_do_not_admit_underround_or_prior_rows(self):
        data = pd.DataFrame({
            'date': ['2026-04-01']*2 + ['2026-06-01']*4,
            'WIN_MARKET_ID': ['prior', 'prior', 'test', 'test', 'under', 'under'],
            'BEST_AVAIL_BACK_AT_SCHEDULED_OFF': [25, 1.01, 25, 1.01, 25, 2],
            'y': [1, 0, 0, 1, 1, 0],
        })
        p = pd.Series([.05, .95, .05, .95, .05, .95]).to_numpy()
        rows = {r['policy']: r for r in policy_metrics(data, {'v7': p}) if r['band_floor'] == 20}
        self.assertEqual(rows['all_runners']['runners'], 2)
        self.assertEqual(rows['point_positive_6pct']['runners'], 0)
        self.assertEqual(rows['point_positive_3pct']['runners'], 1)
        self.assertEqual(rows['point_positive_no_floor']['roi'], -1)
        self.assertEqual(rows['prior_band_lower_bound_at_haircut']['runners'], 0)

    def test_archive_band_requires_net_edge_and_non_underround(self):
        data = pd.DataFrame({
            'date': ['2025-06-01']*4,
            'WIN_MARKET_ID': ['book', 'book', 'under', 'under'],
            'BEST_AVAIL_BACK_AT_SCHEDULED_OFF': [10, 1.01, 10, 2],
            'y': [1, 0, 1, 0],
        })
        p = pd.Series([.102, .898, .2, .8]).to_numpy()
        rows = {r['sample']: r for r in archive_price_band_metrics(data, {'model': p})
                if r['band_floor'] == 10}
        self.assertEqual(rows['all_runners']['runners'], 2)
        self.assertEqual(rows['positive_net_ev']['runners'], 0)

    def test_bootstrap_lower_ratio_uses_day_clusters(self):
        dates = pd.Series(['2025-07-01', '2025-07-01', '2025-07-02'])
        boot = DayBootstrap(dates)
        values = pd.Series([1., 1., 0.]).to_numpy()
        expected = pd.Series([.5, .5, .5]).to_numpy()
        self.assertEqual(boot.interval(expected > 0, values, expected), [0, 2])
