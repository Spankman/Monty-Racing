import csv, hashlib, json, tempfile, unittest
from pathlib import Path
from research_prediction_ledger import stage

class PredictionLedgerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  p=Path(self.tmp.name);self.s=p/'scores.csv';self.m=p/'manifest.json';self.out=p/'ledger.csv'
  with self.s.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['meeting','race','number','horse','odds','market_prob','research_prob','status'])
   w.writeheader();w.writerow({'meeting':'A','race':'1','number':'2','horse':'Example','odds':'3','market_prob':'.3','research_prob':'.3','status':'UNAPPROVED RESEARCH — NO BET'})
  self.m.write_text(json.dumps({'schema':'monty-research-evidence-v1','files_sha256':{'scores.csv':hashlib.sha256(self.s.read_bytes()).hexdigest()},'pre_off_proven':False}))
 def test_create_only_and_no_bet(self):
  r=stage(self.s,self.m,self.out);self.assertEqual(r['records'],1)
  with self.out.open() as f:row=next(csv.DictReader(f))
  self.assertEqual(row['results_status'],'NOT_RECONCILED')
  self.assertEqual(row['pre_off_proven'],'false')
  with self.assertRaises(FileExistsError):stage(self.s,self.m,self.out)
 def test_tampered_scores_rejected(self):
  self.s.write_text(self.s.read_text()+'tamper')
  with self.assertRaises(ValueError):stage(self.s,self.m,self.out)
 def test_duplicate_runner_rejected(self):
  with self.s.open('a') as f:f.write('A,1,2,Example,3,.3,.3,UNAPPROVED RESEARCH — NO BET\n')
  self.m.write_text(json.dumps({'schema':'monty-research-evidence-v1','files_sha256':{'scores.csv':hashlib.sha256(self.s.read_bytes()).hexdigest()},'pre_off_proven':False}))
  with self.assertRaises(ValueError):stage(self.s,self.m,self.out)
if __name__=='__main__':unittest.main()
