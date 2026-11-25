"""Checks for the offline academic benchmark helpers."""
import unittest

import numpy as np
import pandas as pd

from operations.audit.fundamental_study import FEATURES, design, fit_logits, harville_place, prior_roles
from operations.audit.roughies_240 import softmax


class FundamentalStudyTests(unittest.TestCase):
    def test_race_logit_improves_on_uniform_for_known_direction(self):
        x = np.tile([[-1.0], [1.0]], (12, 1))
        y = (x[:, 0] == 1)
        race = np.repeat(np.arange(12), 2)
        w = fit_logits(x, y, race, penalty=.01)
        p = softmax(x@w, race)
        self.assertTrue((p[y] > .9).all())
        np.testing.assert_allclose(p[::2]+p[1::2], 1)

    def test_design_frozen_when_future_rows_change(self):
        train = np.array([True, True, False])
        row = np.array([[1, np.nan], [3, 8], [1e8, -1e8]])
        before = design(row, train)
        row[2] = 0
        np.testing.assert_allclose(before[train], design(row, train)[train])

    def test_harville_reconciles_place_count_and_missing_labels(self):
        p = np.array([.45, .25, .18, .12] * 3)
        v = harville_place(p, np.repeat(np.arange(3), 4), np.repeat([2, 3, 0], 4))
        np.testing.assert_allclose([v[:4].sum(), v[4:8].sum()], [2, 3])
        self.assertTrue(np.isnan(v[8:]).all())

    def test_prior_roles_excludes_same_day_and_current_market(self):
        rows = pd.DataFrame({
            "date": ["2025-01-01"]*4 + ["2025-01-02"]*2,
            "WIN_MARKET_ID": ["r1", "r1", "r2", "r2", "r3", "r3"],
            "SELECTION_ID": ["a", "b", "c", "d", "a", "b"],
            "name_key": ["a", "b", "c", "d", "a", "b"],
            "BEST_AVAIL_BACK_AT_SCHEDULED_OFF": [8., 2., 2., 9., 5., 2.],
            "jockey": ["J"]*6, "trainer": ["T"]*6, "y": [1, 0, 0, 1, 1, 0],
        })
        raw = np.ones((len(rows), len(FEATURES)))
        before = prior_roles(rows, raw)
        self.assertTrue(np.isnan(before[:4]).all())
        np.testing.assert_array_equal(before[4:, :2], [[1, 0], [0, 1]])
        rows.loc[4:, "BEST_AVAIL_BACK_AT_SCHEDULED_OFF"] = [1.1, 70]
        rows.loc[4:, "y"] = [0, 1]
        np.testing.assert_allclose(prior_roles(rows, raw), before)
