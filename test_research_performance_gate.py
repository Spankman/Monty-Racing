import json,tempfile,unittest
from pathlib import Path
from research_performance_gate import report,BET_TYPES

class ResearchPerformanceGateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  p=Path(self.tmp.name);self.source=p/'reconciliation.json';self.output=p/'gate.json'
  self.payload={'schema':'monty-research-results-v1','pre_off_proven':False,
   'result_independently_verified':False,'records':[{'bet_settlement':'NOT_APPLICABLE_RESEARCH_ONLY'}]}
  self.source.write_text(json.dumps(self.payload))
 def test_all_three_bet_types_blocked(self):
  result=report(self.source,self.output)
  self.assertEqual(set(result['performance']),set(BET_TYPES))
  for v in result['performance'].values():
   self.assertIsNone(v['roi']);self.assertIsNone(v['profit']);self.assertIsNone(v['returns'])
  self.assertTrue(result['no_bet'])
  with self.assertRaises(FileExistsError):report(self.source,self.output)
 def test_settlement_data_rejected(self):
  self.payload['records'][0]['bet_settlement']='WIN'
  self.source.write_text(json.dumps(self.payload))
  with self.assertRaises(ValueError):report(self.source,self.output)
 def test_unexpected_proof_state_rejected(self):
  self.payload['pre_off_proven']=True
  self.source.write_text(json.dumps(self.payload))
  with self.assertRaises(ValueError):report(self.source,self.output)
if __name__=='__main__':unittest.main()
