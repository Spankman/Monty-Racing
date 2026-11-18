import unittest
from expert_consensus_experiment.provisional_rank import provisional_rank

def fixture(counts=(0,0),status="ELIGIBLE"):
    return {"races":[{"meeting":"Belmont","race":4,
            "betting_eligibility":{"status":status},
            "runners":[{"number":"1","v6_win_probability":0.6,"expert_mentions":counts[0]},
                       {"number":"2","v6_win_probability":0.4,"expert_mentions":counts[1]}]}]}

class ProvisionalRankTests(unittest.TestCase):
    def test_no_experts_keeps_v6_order_and_scores(self):
        rows=provisional_rank(fixture())["races"][0]["runners"]
        self.assertEqual([r["number"] for r in rows],["1","2"])
        self.assertEqual([r["provisional_rank_score"] for r in rows],[0.6,0.4])
        self.assertEqual(rows[0]["expert_blend_used"],0)
    def test_expert_influence_is_declared_not_probability(self):
        rows=provisional_rank(fixture((0,2)))["races"][0]["runners"]
        self.assertAlmostEqual(rows[0]["provisional_rank_score"],0.54)
        self.assertFalse(rows[0]["rank_score_is_probability"])
    def test_confirmed_exclusion_is_no_bet(self):
        self.assertEqual(provisional_rank(fixture((1,0),"NO_BET"))["races"][0]["betting_recommendation"],"NO_BET")
    def test_invalid_weight_rejected(self):
        with self.assertRaises(ValueError):
            provisional_rank(fixture(),1.1)

if __name__=="__main__":
    unittest.main()
