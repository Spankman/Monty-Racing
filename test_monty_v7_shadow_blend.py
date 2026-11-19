import tempfile, unittest
from pathlib import Path
import pandas as pd
from monty_v7_shadow_blend import blend

class V7BlendTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=Path(self.tmp.name)/'scores.csv';self.e=Path(self.tmp.name)/'experts.csv'
  pd.DataFrame([
   {'meeting':'A','race':'1','number':'1','research_prob':.6,'feature_coverage':.9},
   {'meeting':'A','race':'1','number':'2','research_prob':.4,'feature_coverage':.9}
  ]).to_csv(self.s,index=False)
 def test_no_experts_keeps_model(self):
  x=blend(self.s);self.assertAlmostEqual(x.v7_shadow_prob.iloc[0],.6)
  self.assertTrue((x.expert_weight_used==0).all())
 def test_documented_experts(self):
  pd.DataFrame([{'meeting':'A','race':'1','number':'2','expert_score':1,'source':'tipster','author':'Named Analyst','captured_at':'2026-11-19T00:00:00+10:00','race_off_at':'2026-11-19T12:00:00+10:00'}]).to_csv(self.e,index=False)
  x=blend(self.s,self.e);self.assertAlmostEqual(x.v7_shadow_prob.iloc[0],.54)
  self.assertAlmostEqual(x.v7_shadow_prob.sum(),1)
 def test_missing_author_disables_expert_weight(self):
  pd.DataFrame([{'meeting':'A','race':'1','number':'2','expert_score':1,'source':'tipster','captured_at':'2026-11-19T00:00:00+10:00','race_off_at':'2026-11-19T12:00:00+10:00'}]).to_csv(self.e,index=False)
  x=blend(self.s,self.e)
  self.assertTrue((x.expert_weight_used==0).all())
 def test_syndicated_author_counts_once(self):
  rows=[{'meeting':'A','race':'1','number':'2','expert_score':1,'source':site,'author':'Same Analyst','captured_at':'2026-11-19T00:00:00+10:00','race_off_at':'2026-11-19T12:00:00+10:00'} for site in ('Site A','Site B')]
  pd.DataFrame(rows).to_csv(self.e,index=False)
  x=blend(self.s,self.e)
  self.assertAlmostEqual(x.v7_shadow_prob.iloc[0],.54)
 def test_low_coverage_disables_experts(self):
  pd.DataFrame([{'meeting':'A','race':'1','number':'2','expert_score':1,'source':'tipster','author':'Named Analyst','captured_at':'2026-11-19T00:00:00+10:00','race_off_at':'2026-11-19T12:00:00+10:00'}]).to_csv(self.e,index=False)
  x=blend(self.s,self.e,min_coverage=.95);self.assertTrue((x.expert_weight_used==0).all())
 def test_post_off_expert_fails(self):
  pd.DataFrame([{'meeting':'A','race':'1','number':'2','expert_score':1,'source':'tipster','author':'Named Analyst','captured_at':'2026-11-19T13:00:00+10:00','race_off_at':'2026-11-19T12:00:00+10:00'}]).to_csv(self.e,index=False)
  with self.assertRaises(ValueError):blend(self.s,self.e)
 def test_timezone_naive_fails(self):
  pd.DataFrame([{'meeting':'A','race':'1','number':'2','expert_score':1,'source':'tipster','author':'Named Analyst','captured_at':'2026-11-19T01:00:00','race_off_at':'2026-11-19T12:00:00+10:00'}]).to_csv(self.e,index=False)
  with self.assertRaises(ValueError):blend(self.s,self.e)
 def test_unnormalized_model_fails(self):
  d=pd.read_csv(self.s);d.loc[0,'research_prob']=.7;d.to_csv(self.s,index=False)
  with self.assertRaises(ValueError):blend(self.s)
 def test_unknown_horse_fails(self):
  pd.DataFrame([{'meeting':'A','race':'1','number':'3','expert_score':1,'source':'tipster','author':'Named Analyst','captured_at':'2026-11-19T00:00:00+10:00','race_off_at':'2026-11-19T12:00:00+10:00'}]).to_csv(self.e,index=False)
  with self.assertRaises(ValueError):blend(self.s,self.e)
if __name__=='__main__':unittest.main()
