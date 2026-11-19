import unittest
from monty_single_race_policy import route_single_race,next_bet_type,BET_ORDER

PICK={'meeting':'Newcastle','race':'8','number':'9','horse':'Example'}

class SingleRacePolicyTests(unittest.TestCase):
 def test_v7_priority(self):
  r=route_single_race({'V7':[PICK],'V6':[PICK]})
  self.assertEqual(r.source,'V7');self.assertFalse(r.betting_authorised)
 def test_le_is_race_specific_and_before_v6(self):
  r=route_single_race({'V7_LE':[PICK],'V6':[PICK]})
  self.assertEqual(r.source,'V7_LE');self.assertTrue(r.race_only_lower_expectations)
 def test_v6_fallback(self):
  self.assertEqual(route_single_race({'V6':[PICK]}).source,'V6')
 def test_provisional_last(self):
  r=route_single_race({'FORM_ASSESSMENT':[PICK]})
  self.assertEqual(r.source,'FORM_ASSESSMENT')
  self.assertFalse(r.official_model_output)
 def test_missing_never_invented(self):
  self.assertEqual(route_single_race({'V7':None,'V6':[]}).source,'NO_BET')
 def test_excluded_race_needs_override(self):
  self.assertEqual(route_single_race({'V7':[PICK]},eligible=False).source,'NO_BET')
  self.assertEqual(route_single_race({'V7':[PICK]},eligible=False,override=True).source,'V7')
 def test_duplicate_runner_rejected(self):
  self.assertEqual(route_single_race({'V7':[PICK,PICK]}).source,'NO_BET')
 def test_exotic_order(self):
  self.assertEqual(BET_ORDER,('WIN','QUINELLA_2','TRIFECTA_BOX_3','FIRST_FOUR_4'))
  self.assertEqual(next_bet_type('WIN'),'QUINELLA_2')
  self.assertIsNone(next_bet_type('FIRST_FOUR_4'))
if __name__=='__main__':unittest.main()
