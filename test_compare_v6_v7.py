import tempfile, unittest
from pathlib import Path
import pandas as pd
from compare_v6_v7 import compare

class CompareTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.a=Path(self.tmp.name)/'v6.csv';self.b=Path(self.tmp.name)/'v7.csv'
  self.rows=[{'meeting':'Albury','race':'7','number':'8','horse':'Example A','selection':'BEST','captured_at':'2026-11-19T09:00:00+10:00'}]
  pd.DataFrame(self.rows).to_csv(self.a,index=False);pd.DataFrame(self.rows).to_csv(self.b,index=False)
 def test_same(self):
  self.assertEqual(compare(self.a,self.b).comparison.iloc[0],'SAME')
 def test_different(self):
  rows=[dict(self.rows[0],number='7',horse='Example B')]
  pd.DataFrame(rows).to_csv(self.b,index=False)
  self.assertEqual(compare(self.a,self.b).comparison.iloc[0],'DIFFERENT')
 def test_missing_v6_fails(self):
  self.a.unlink()
  with self.assertRaises(FileNotFoundError):compare(self.a,self.b)
 def test_naive_timestamp_fails(self):
  rows=[dict(self.rows[0],captured_at='2026-11-19T09:00:00')]
  pd.DataFrame(rows).to_csv(self.b,index=False)
  with self.assertRaises(ValueError):compare(self.a,self.b)
if __name__=='__main__':unittest.main()
