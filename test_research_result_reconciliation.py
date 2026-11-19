import csv,json,tempfile,unittest
from pathlib import Path
from research_result_reconciliation import reconcile

class ResearchReconciliationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  p=Path(self.tmp.name);self.l=p/'ledger.csv';self.r=p/'results.csv';self.o=p/'joined.json'
  with self.l.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['record_id','meeting','race','number','horse','status','pre_off_proven'])
   w.writeheader();w.writerow({'record_id':'abc','meeting':'Narrogin','race':'2','number':'4','horse':'Example','status':'UNAPPROVED RESEARCH — NO BET','pre_off_proven':'false'})
  self.write_result('Example')
 def write_result(self,horse):
  with self.r.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['meeting','race','number','horse','finish_position','result_source','result_captured_utc'])
   w.writeheader();w.writerow({'meeting':'Narrogin','race':'2','number':'4','horse':horse,'finish_position':'1','result_source':'supplied-unverified','result_captured_utc':'2026-11-19T08:00:00Z'})
 def test_reconciles_without_betting_claims_or_rewriting(self):
  original=self.l.read_bytes();out=reconcile(self.l,self.r,self.o)
  self.assertEqual(out['records'],1);self.assertEqual(self.l.read_bytes(),original)
  report=json.loads(self.o.read_text());self.assertFalse(report['result_independently_verified'])
  self.assertEqual(report['records'][0]['bet_settlement'],'NOT_APPLICABLE_RESEARCH_ONLY')
  with self.assertRaises(FileExistsError):reconcile(self.l,self.r,self.o)
 def test_mismatched_horse_rejected(self):
  self.write_result('Wrong Horse')
  with self.assertRaises(ValueError):reconcile(self.l,self.r,self.o)
 def test_missing_results_rejected(self):
  self.r.write_text('meeting,race,number,horse,finish_position,result_source,result_captured_utc\n')
  with self.assertRaises(ValueError):reconcile(self.l,self.r,self.o)
 def test_timezone_required(self):
  self.r.write_text(self.r.read_text().replace('2026-11-19T08:00:00Z','2026-11-19T08:00:00'))
  with self.assertRaises(ValueError):reconcile(self.l,self.r,self.o)
 def test_no_winner_rejected(self):
  self.r.write_text(self.r.read_text().replace(',1,supplied-unverified',',2,supplied-unverified'))
  with self.assertRaises(ValueError):reconcile(self.l,self.r,self.o)
if __name__=='__main__':unittest.main()
