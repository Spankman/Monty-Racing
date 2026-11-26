import unittest

import numpy as np
import pandas as pd

from operations.audit.historical_blocks import BLOCKS, suitability


class HistoricalBlocksTests(unittest.TestCase):
    def test_same_day_and_future_results_do_not_enter_suitability(self):
        rows = pd.DataFrame(dict(
            date=["2025-01-01", "2025-01-01", "2025-01-02", "2025-01-03"],
            SELECTION_ID=["x"]*4, name_key=["x"]*4,
            DISTANCE=[1200, 1600, 1250, 2500], going=["good","soft","good","firm"],
            y=[1, 0, 1, 0],
        ))
        features = suitability(rows)
        self.assertTrue(np.isnan(features[:2]).all())
        np.testing.assert_allclose(features[2], [.25, np.log(2), .25, np.log(2)])
        rows.loc[2:, "y"] = 0
        np.testing.assert_allclose(suitability(rows)[:3], features[:3])
        self.assertTrue(np.isnan(features[3]).all())

    def test_blocks_are_disjoint(self):
        values = [feature for block in BLOCKS.values() for feature in block]
        self.assertEqual(len(values), len(set(values)))
