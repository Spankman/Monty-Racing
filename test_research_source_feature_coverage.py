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
 def test_empty_source_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=p/'model.json';s=p/'source.json'
   m.write_text(json.dumps({'input_feature_names':['age']}))
   s.write_text(json.dumps({'runners':[]}))
   with self.assertRaises(ValueError):audit(m,{'formfav':s})
if __name__=='__main__':unittest.main()
