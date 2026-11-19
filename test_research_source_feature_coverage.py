import json,tempfile,unittest
from pathlib import Path
from research_source_feature_coverage import audit

class SourceCoverageTests(unittest.TestCase):
 def test_numeric_coverage_and_missing_are_separate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=p/'model.json';s=p/'krok.json'
   m.write_text(json.dumps({'input_feature_names':['barrier','age','missing']}))
   s.write_text(json.dumps({'runners':[{'meeting':'A','race':'1','number':'1','horse':'One','barrier':2,'age':None},{'meeting':'A','race':'1','number':'2','horse':'Two','barrier':4,'age':3}]}))
   result=audit(m,{'krok':s})['sources']['krok']
   self.assertEqual(result['observed_counts'],{'barrier':2,'age':1,'missing':0})
   self.assertEqual(result['mean_input_coverage'],.5)
 def test_duplicate_identity_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=p/'model.json';s=p/'source.json'
   m.write_text(json.dumps({'input_feature_names':['age']}))
   row={'meeting':'A','race':'1','number':'1','horse':'One','age':3}
   s.write_text(json.dumps({'runners':[row,row]}))
   with self.assertRaises(ValueError):audit(m,{'krok':s})
 def test_cross_provider_identity_mismatch_blocks_comparison(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=p/'model.json';a=p/'a.json';b=p/'b.json'
   m.write_text(json.dumps({'input_feature_names':['age']}))
   a.write_text(json.dumps({'runners':[{'meeting':'A','race':'1','number':'1','horse':'One','age':3}]}))
   b.write_text(json.dumps({'runners':[{'meeting':'A','race':'1','number':'2','horse':'Two','age':4}]}))
   result=audit(m,{'formfav':a,'krok':b})
   self.assertEqual(result['comparison_status'],'BLOCKED_UNMATCHED_RUNNER_FIELDS')
   self.assertEqual(result['runner_identity_parity']['comparisons']['krok']['missing_from_source'],1)
 def test_cross_provider_identity_match(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=p/'model.json';a=p/'a.json';b=p/'b.json'
   m.write_text(json.dumps({'input_feature_names':['age']}))
   row={'meeting':'A','race':'1','number':'1','horse':'One','age':3}
   for f in (a,b):f.write_text(json.dumps({'runners':[row]}))
   result=audit(m,{'formfav':a,'krok':b})
   self.assertTrue(result['runner_identity_parity']['all_sources_match'])
 def test_empty_source_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=p/'model.json';s=p/'source.json'
   m.write_text(json.dumps({'input_feature_names':['age']}))
   s.write_text(json.dumps({'runners':[]}))
   with self.assertRaises(ValueError):audit(m,{'formfav':s})
if __name__=='__main__':unittest.main()
