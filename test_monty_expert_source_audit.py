import tempfile,unittest
from pathlib import Path
import pandas as pd
from monty_expert_source_audit import summarize

class SourceAuditTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/'sources.csv'
  self.row={'source':'Publisher A','source_url':'https://example.org/tips','status':'located','attempted_at':'2026-11-19T12:00:00+10:00','details':'Article found, pre-race capture not established'}
 def test_located_not_verified(self):
  pd.DataFrame([self.row]).to_csv(self.path,index=False)
  report=summarize(self.path)
  self.assertEqual(report['status_counts']['located'],1)
  self.assertNotIn('verified',report['status_counts'])
 def test_invalid_status(self):
  pd.DataFrame([{**self.row,'status':'guessed'}]).to_csv(self.path,index=False)
  with self.assertRaises(ValueError):summarize(self.path)
 def test_missing_timezone(self):
  pd.DataFrame([{**self.row,'attempted_at':'2026-11-19T12:00:00'}]).to_csv(self.path,index=False)
  with self.assertRaises(ValueError):summarize(self.path)
if __name__=='__main__':unittest.main()
