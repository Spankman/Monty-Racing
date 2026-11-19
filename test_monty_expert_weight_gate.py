import json,tempfile,unittest
from pathlib import Path
from monty_expert_weight_gate import gate

class ExpertWeightGateTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)/'history.json'
  self.comp=Path(self.temp.name)/'comparison.json'
 def test_no_comparison_is_zero(self):
  self.path.write_text(json.dumps({'experts':[{'source':'Example','races':1000}]}))
  self.assertEqual(gate(self.path)['expert_weight'],0)
 def test_small_sample_is_zero(self):
  self.path.write_text(json.dumps({'experts':[{'source':'Example','races':5}]}))
  self.comp.write_text(json.dumps({'chronological_holdout_verified':True,'holdout_races':500,'same_races_same_odds':True,'provenance_verified':True}))
  self.assertEqual(gate(self.path,self.comp)['expert_weight'],0)
 def test_validated_comparison_only_eligible_not_activated(self):
  self.path.write_text(json.dumps({'experts':[{'source':'Example','races':150}]}))
  self.comp.write_text(json.dumps({'chronological_holdout_verified':True,'holdout_races':150,'same_races_same_odds':True,'provenance_verified':True}))
  result=gate(self.path,self.comp)
  self.assertEqual(result['expert_weight'],0)
  self.assertTrue(result['eligible_for_manual_review'])
if __name__=='__main__':unittest.main()
