import unittest

import pandas as pd

from v7.holdout import paired_report


class TestHoldout(unittest.TestCase):
    def test_uses_same_field_and_excludes_restricted_and_late_prices(self):
        rows = []
        for race in ("verified", "maiden", "late"):
            for runner, odds, market in (("a", 2.0, 0.6), ("b", 3.0, 0.4)):
                rows.append(dict(
                    country="AU", race_id=race, runner_id=runner, odds=odds,
                    market=market, v6=market, candidate1=market, candidate2=market,
                    classification="Maiden" if race == "maiden" else "BM65",
                    class_verified=True, going="Soft 6", date="2030-01-02",
                    decision_at="2030-01-02T02:00:00Z", start_at="2030-01-02T03:00:00Z",
                    quote_captured_at="2030-01-02T01:00:00Z" if race != "late"
                    else "2030-01-02T02:30:00Z",
                    result_at="2030-01-02T04:00:00Z", field_verified=True,
                    features_verified_asof=True, field_unchanged=True, result_verified=True,
                    quote_type="bookmaker_fixed_win", bookmaker="ExampleBook",
                    winner=int(runner == "a"),
                ))
        report = paired_report(pd.DataFrame(rows), start="2030-01-01", end="2030-01-05",
                               locked_at="2029-12-15T12:00:00Z", quote_type="bookmaker_fixed_win")
        au = report["by_country"]["AU"]["models"]
        self.assertEqual({m["races"] for m in au.values()}, {1})
        self.assertEqual(au["candidate2"]["units"], 1)
        self.assertEqual({r["race_id"] for r in report["excluded"]}, {"maiden", "late"})
