import unittest
from expert_consensus_experiment.expert_consensus import consensus_features

CUTOFF = "2026-11-18T09:00:00+10:00"
def tip(expert, runner, rank, at="2026-11-18T08:00:00+10:00"):
    return dict(race_id="r", runner_id=runner, expert_id=expert, published_at=at, rank=rank)

class TestConsensus(unittest.TestCase):
    def test_ranked_shortlists(self):
        rows=[tip("one","a",1),tip("one","b",2),tip("two","b",1)]
        f=consensus_features("r",["a","b","c"],rows,CUTOFF)
        self.assertEqual(f["a"]["expert_top1_votes"],1)
        self.assertEqual(f["b"]["expert_top3_votes"],2)
        self.assertEqual(f["b"]["expert_top1_share"],0.5)
        self.assertEqual(f["c"]["expert_top1_votes"],0)
    def test_future_and_missing(self):
        f=consensus_features("r",["a"],[tip("one","a",1,"2026-11-18T12:00:00+10:00")],CUTOFF)
        self.assertIsNone(f["a"]["expert_top1_share"])
        self.assertTrue(f["a"]["expert_data_missing"])
    def test_latest_snapshot(self):
        rows=[tip("one","a",1,"2026-11-18T07:00:00+10:00"),
              tip("one","b",1,"2026-11-18T08:00:00+10:00")]
        f=consensus_features("r",["a","b"],rows,CUTOFF)
        self.assertEqual(f["a"]["expert_top1_votes"],0)
        self.assertEqual(f["b"]["expert_top1_votes"],1)
    def test_weight(self):
        f=consensus_features("r",["a","b"],[tip("one","a",1),tip("two","b",1)],CUTOFF,{"one":3,"two":1})
        self.assertEqual(f["a"]["expert_weighted_top1_share"],0.75)
    def test_duplicate_rank_rejected(self):
        with self.assertRaises(ValueError):
            consensus_features("r",["a","b"],[tip("one","a",1),tip("one","b",1)],CUTOFF)

if __name__ == "__main__":
    unittest.main()
