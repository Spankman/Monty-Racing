import csv, datetime, json, tempfile, unittest
from pathlib import Path
from research_evidence_manifest import build
from research_prediction_ledger import stage
from research_evidence_verify import verify

class EvidenceVerifyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  p=Path(self.tmp.name);self.s=p/'snapshot.json';self.c=p/'scores.csv';self.a=p/'scores.audit.json'
  self.m=p/'evidence.json';self.l=p/'ledger.csv'
  self.s.write_text(json.dumps({'date':'2026-11-19','races':[{'meeting':'A','race':'1'}]}))
  with self.c.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['meeting','race','number','horse','odds','market_prob','research_prob','status'])
   w.writeheader();w.writerow({'meeting':'A','race':'1','number':'2','horse':'Example','odds':'3','market_prob':'.3','research_prob':'.3','status':'UNAPPROVED RESEARCH — NO BET'})
  self.a.write_text('{}')
  build(self.s,self.c,self.a,self.m,now=datetime.datetime(2026,11,19,tzinfo=datetime.timezone.utc),commit='a'*40)
  stage(self.c,self.m,self.l)
 def test_valid_bundle(self):
  self.assertEqual(verify(self.m,self.l)['verified_rows'],1)
 def test_tampered_snapshot(self):
  self.s.write_text('tampered')
  with self.assertRaises(ValueError):verify(self.m,self.l)
 def test_tampered_ledger(self):
  self.l.write_text(self.l.read_text().replace('NOT_RECONCILED','RESULTED'))
  with self.assertRaises(ValueError):verify(self.m,self.l)
 def test_tampered_manifest(self):
  self.m.write_text(self.m.read_text()+' ')
  with self.assertRaises(ValueError):verify(self.m,self.l)
if __name__=='__main__':unittest.main()
