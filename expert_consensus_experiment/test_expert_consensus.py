import unittest
from expert_consensus_experiment.expert_consensus import consensus_features

class ExpertConsensusTests(unittest.TestCase):
    def test_future_vote_excluded_and_missing_not_zero(self):
        rows = [
            dict(race_id="r", runner_id="a", expert_id="one", published_at="2026-11-18T08:00:00+10:00", rank=1),
            dict(race_id="r", runner_id="b", expert_id="two", published_at="2026-11-18T12:00:00+10:00", rank=1),
        ]
        f = consensus_features("r", ["a","b"], rows, "2026-11-18T09:00:00+10:00")
        self.assertEqual(f["a"]["expert_coverage"], 1)
        self.assertEqual(f["a"]["expert_vote_share"], 1)
        self.assertEqual(f["b"]["expert_vote_share"], 0)
        self.assertIsNone(consensus_features("r", ["a"], [], "2026-11-18T09:00:00+10:00")["a"]["expert_vote_share"])
    def test_latest_vote_per_expert(self):
        rows = [dict(race_id="r",runner_id=runner,expert_id="one",published_at=ts,rank=1) for runner,ts in [("a","2026-11-18T07:00:00Z"),("b","2026-11-18T08:00:00Z")]]
        f=consensus_features("r",["a","b"],rows,"2026-11-18T09:00:00Z")
        self.assertEqual(f["a"]["expert_top1_votes"],0)
        self.assertEqual(f["b"]["expert_top1_votes"],1)

if __name__=="__main__": unittest.main()
