import unittest
from expert_consensus_experiment.dynamic_blend import dynamic_expert_blend,rank_dynamic

def runners(a,b):
    return [{"number":"1","v6_win_probability":0.6,"verified_independent_sources":a},
            {"number":"2","v6_win_probability":0.4,"verified_independent_sources":b}]

class DynamicTests(unittest.TestCase):
    def test_unknown_independence_is_zero(self):
        self.assertEqual(dynamic_expert_blend(runners([],[]))["blend"],0)
    def test_single_voice_is_zero(self):
        self.assertEqual(dynamic_expert_blend(runners(["A"],[]))["blend"],0)
    def test_two_unanimous_votes_small_weight(self):
        self.assertAlmostEqual(dynamic_expert_blend(runners(["A","B"],[]))["blend"],0.08)
    def test_five_unanimous_votes_reach_cap(self):
        self.assertAlmostEqual(dynamic_expert_blend(runners(["A","B","C","D","E"],[]))["blend"],0.20)
    def test_split_votes_no_influence(self):
        self.assertEqual(dynamic_expert_blend(runners(["A"],["B"]))["blend"],0)
    def test_duplicate_source_rejected(self):
        with self.assertRaises(ValueError):
            dynamic_expert_blend(runners(["A"],["A"]))
    def test_no_bet_preserved(self):
        overlay={"races":[{"meeting":"Sandown","race":2,
            "betting_eligibility":{"status":"NO_BET"},
            "runners":runners(["A","B"],[])}]}
        self.assertEqual(rank_dynamic(overlay)["races"][0]["betting_recommendation"],"NO_BET")

if __name__=="__main__":
    unittest.main()
