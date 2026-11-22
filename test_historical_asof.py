import unittest
from historical_asof import join_asof

CUT = "2026-11-22T04:00:00+00:00"
BASE = dict(runner_id="horse-123", feature="observed_win_rate", value=0.25,
            observed_at="2026-11-20T01:00:00+00:00",
            available_at="2026-11-20T02:00:00+00:00", source="licensed-history")


class AsOfJoinTests(unittest.TestCase):
    def join(self, history, runners=None):
        return join_asof(runners or [{"runner_id": "horse-123"}], history,
                         cutoff_utc=CUT, feature_names=["observed_win_rate"])

    def test_valid_prior_history(self):
        self.assertEqual(self.join([BASE])[0]["observed_win_rate"], 0.25)

    def test_post_cutoff_release_blocked(self):
        row = dict(BASE, available_at="2026-11-22T05:00:00+00:00")
        self.assertNotIn("observed_win_rate", self.join([row])[0])

    def test_observation_at_cutoff_blocked(self):
        row = dict(BASE, observed_at=CUT, available_at=CUT)
        self.assertNotIn("observed_win_rate", self.join([row])[0])

    def test_missing_identity_not_joined(self):
        self.assertNotIn("observed_win_rate", self.join([BASE], [{}])[0])

    def test_ambiguous_tie_not_joined(self):
        self.assertNotIn("observed_win_rate", self.join([BASE, dict(BASE, value=0.9)])[0])

    def test_invalid_values_not_joined(self):
        self.assertNotIn("observed_win_rate", self.join([dict(BASE, value=float("nan"))])[0])

    def test_newest_prior_release_selected(self):
        older = dict(BASE, value=0.1, observed_at="2026-11-19T01:00:00+00:00",
                     available_at="2026-11-19T02:00:00+00:00")
        self.assertEqual(self.join([older, BASE])[0]["observed_win_rate"], 0.25)


if __name__ == "__main__":
    unittest.main()
