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

    def test_prepopulated_feature_requires_the_same_evidence(self):
        runner = {"runner_id": "horse-123", "observed_win_rate": 1.0}
        self.assertNotIn("observed_win_rate", self.join([], [runner])[0])
        self.assertEqual(self.join([BASE], [runner])[0]["observed_win_rate"], 0.25)

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

    def test_missing_malformed_or_equal_release_never_leaks(self):
        rows = [
            dict(BASE, available_at=CUT),
            dict(BASE, available_at="unknown"),
            dict(BASE, observed_at="2026-11-21T01:00:00+00:00"),
            dict(BASE, source=5),
        ]
        self.assertNotIn("observed_win_rate", self.join(rows)[0])

    def test_equal_release_with_differing_observations_is_ambiguous(self):
        row = dict(BASE, observed_at="2026-11-19T01:00:00+00:00", value=0.9)
        self.assertNotIn("observed_win_rate", self.join([BASE, row])[0])

    def test_namespaced_identity_and_provenance(self):
        runner = {"runner_id": "horse-123", "country": "NZ", "namespace": "registry"}
        valid = dict(BASE, **runner)
        wrong = dict(valid, country="AU", value=0.8)
        provenance = []
        result = join_asof([runner], [BASE, wrong, valid], cutoff_utc=CUT,
                           feature_names=["observed_win_rate"], provenance=provenance)
        self.assertEqual(result[0]["observed_win_rate"], 0.25)
        self.assertEqual(provenance, [{k: v for k, v in valid.items() if k != "value"}])
        self.assertEqual(self.join([dict(BASE, runner_id="")], [{"runner_id": ""}]),
                         [{"runner_id": ""}])


if __name__ == "__main__":
    unittest.main()
