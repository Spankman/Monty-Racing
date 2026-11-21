import unittest
from expert_consensus_experiment.provisional_overlay import overlay

class OverlayTests(unittest.TestCase):
    def test_join_and_exclusions(self):
        races=[{"race_id":"Sandown|2","runners":[{"runner_number":"2","runner_name":"Royal Maximus","win_probability":0.4}]},
               {"race_id":"Belmont|4","runners":[{"runner_number":"1","runner_name":"Rok 'N' Rom","win_probability":0.36}]}]
        observations={"date":"2026-11-18","selections":[
            {"meeting":"Sandown","race":2,"number":2,"source":"Editor A"},
            {"meeting":"Belmont Park","race":4,"number":1,"source":"Editor B"},
            {"meeting":"Belmont","race":4,"number":1,"source":"Editor B"}]}
        meta={"races":[{"meeting":"Sandown-Lakeside","race":2,"is_maiden":True,
                        "is_two_year_old":False,"is_hurdle":False},
                       {"meeting":"Belmont Park","race":4,"is_maiden":False,
                        "is_two_year_old":False,"is_hurdle":False}]}
        result=overlay(races,observations,meta)
        self.assertEqual(result["races"][0]["betting_eligibility"]["status"],"NO_BET")
        self.assertEqual(result["races"][1]["betting_eligibility"]["status"],"ELIGIBLE")
        self.assertEqual(result["races"][1]["runners"][0]["expert_mentions"],1)
        self.assertIsNone(result["races"][1]["runners"][0]["v7_win_probability"])\n        self.assertEqual(result["races"][1]["runners"][0]["verified_independent_sources"],[])
    def test_unknown_classification_flagged(self):
        r=overlay([{"race_id":"Gawler|6","runners":[{"runner_number":"2"}]}],
                  {"date":"2026-11-18","selections":[]})
        self.assertEqual(r["races"][0]["betting_eligibility"]["status"],"UNVERIFIED_OVERRIDE")

    def test_duplicate_normalized_race_rejected(self):\n        races=[{"race_id":"Belmont|4","runners":[{"runner_number":"1"}]},\n               {"race_id":"Belmont Park|4","runners":[{"runner_number":"2"}]}]\n        with self.assertRaises(ValueError):\n            overlay(races,{"date":"2026-11-18","selections":[]})\n    def test_duplicate_runner_rejected(self):\n        races=[{"race_id":"Gawler|6","runners":[{"runner_number":"2"},{"runner_number":"2"}]}]\n        with self.assertRaises(ValueError):\n            overlay(races,{"date":"2026-11-18","selections":[]})\n\nif __name__=="__main__":
    unittest.main()
