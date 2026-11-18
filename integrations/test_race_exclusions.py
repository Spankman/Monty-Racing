"""Regression tests for Monty universal betting exclusions."""
import unittest
from integrations.race_exclusions import betting_eligibility

class Exclusions(unittest.TestCase):
    def test_maiden(self):
        self.assertEqual(betting_eligibility({"race_name":"Maiden Plate"})["status"],"NO_BET")
    def test_two_year_old(self):
        self.assertEqual(betting_eligibility({"race_name":"2YO Handicap"})["status"],"NO_BET")
    def test_hurdle(self):
        self.assertEqual(betting_eligibility({"race_name":"Open Hurdle"})["status"],"NO_BET")
    def test_explicit_override(self):
        self.assertEqual(betting_eligibility({"race_name":"Maiden Plate"},True)["status"],"OVERRIDE_ALLOWED")
    def test_unknown_is_unverified(self):
        self.assertEqual(betting_eligibility({"race_name":"Race 4"})["status"],"CLASSIFICATION_UNVERIFIED")
    def test_partial_metadata_cannot_mark_eligible(self):\n        self.assertEqual(betting_eligibility({"is_maiden":False})["status"],"CLASSIFICATION_UNVERIFIED")\n    def test_known_nonexcluded(self):
        self.assertEqual(betting_eligibility({"is_maiden":False,"is_two_year_old":False,"is_hurdle":False})["status"],"ELIGIBLE")

if __name__=="__main__":
    unittest.main()
