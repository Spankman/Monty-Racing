import tempfile,unittest
from pathlib import Path
import pandas as pd
from expert_tip_ingest import prepare
from monty_expert_performance import evaluate
class ExpertPipelineTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.scores=self.root/'scores.csv';self.tips=self.root/'tips.csv';self.out=self.root/'out.csv';self.results=self.root/'results.csv'
  pd.DataFrame([dict(meeting='M',race='1',number='2',horse='Test',research_prob=1.0)]).to_csv(self.scores,index=False)
  self.tip=dict(meeting='M',race='1',number='2',horse='Test',source='Real Author',source_url='https://example.org/tip',captured_at='2026-11-19T10:00:00+10:00',race_off_at='2026-11-19T11:00:00+10:00',odds=3.0)
  pd.DataFrame([dict(meeting='M',race='1',number='2',won=1)]).to_csv(self.results,index=False)
 def test_valid_preoff(self):
  pd.DataFrame([self.tip]).to_csv(self.tips,index=False)
  self.assertEqual(prepare(self.scores,self.tips,self.out),1)
  self.assertEqual(evaluate(self.tips,self.results,min_bets=1)['experts'][0]['flat_win_roi'],2.0)
 def test_post_off_rejected(self):
  tip={**self.tip,'captured_at':'2026-11-19T12:00:00+10:00'}
  pd.DataFrame([tip]).to_csv(self.tips,index=False)
  with self.assertRaises(ValueError):prepare(self.scores,self.tips,self.out)
  with self.assertRaises(ValueError):evaluate(self.tips,self.results)
 def test_naive_time_rejected(self):
  tip={**self.tip,'captured_at':'2026-11-19T10:00:00'}
  pd.DataFrame([tip]).to_csv(self.tips,index=False)
  with self.assertRaises(ValueError):prepare(self.scores,self.tips,self.out)
 def test_missing_result_rejected(self):
  pd.DataFrame([self.tip]).to_csv(self.tips,index=False)
  pd.DataFrame([dict(meeting='M',race='1',number='3',won=1)]).to_csv(self.results,index=False)
  with self.assertRaises(ValueError):evaluate(self.tips,self.results)
if __name__=='__main__':unittest.main()
