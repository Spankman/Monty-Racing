import datetime, hashlib, json, tempfile, unittest
from pathlib import Path
from research_evidence_manifest import build

class ResearchEvidenceManifestTests(unittest.TestCase):
 def test_manifest_links_bytes_and_disclaims_preoff_proof(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);s=p/'snapshot.json';scores=p/'scores.csv';audit=p/'audit.json';out=p/'evidence.json'
   s.write_text(json.dumps({'date':'2026-11-19','races':[{'meeting':'A','race':'1'}]}))
   scores.write_text('meeting,race\nA,1\n');audit.write_text('{}')
   result=build(s,scores,audit,out,now=datetime.datetime(2026,11,19,tzinfo=datetime.timezone.utc),commit='a'*40,run_id='123')
   self.assertEqual(result['files_sha256']['scores.csv'],hashlib.sha256(scores.read_bytes()).hexdigest())
   self.assertFalse(result['pre_off_proven'])
   self.assertFalse(result['durably_immutable'])
   self.assertEqual(json.loads(out.read_text())['workflow_run_id'],'123')
 def test_missing_races_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);s=p/'snapshot.json';scores=p/'scores.csv';audit=p/'audit.json'
   s.write_text(json.dumps({'races':[]}));scores.write_text('x');audit.write_text('{}')
   with self.assertRaises(ValueError):build(s,scores,audit,p/'evidence.json',commit='a'*40)
if __name__=='__main__':unittest.main()
