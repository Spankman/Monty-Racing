import json
import subprocess
import sys
import tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from .diagnose import interval,class_group
from .shadow import freeze,record_results

class EvidenceAudit(unittest.TestCase):
    def test_intervals_and_classes(self):
        lo,hi=interval(2,28);self.assertLess(lo,2/28);self.assertGreater(hi,2/28)
        self.assertEqual(class_group('3YO BM64'),'BM <=64');self.assertEqual(class_group('MDN SW'),'Maiden')
    def test_freeze_never_overwrites_and_rejects_late(self):
        rows=[dict(race_id='synthetic',runner_id=str(i),scheduled_start_utc='2030-01-02T00:00:00Z',odds_captured_at_utc='2030-01-01T00:00:00Z',source_url='https://example.test/synthetic',odds=3,v6_probability=.5,v7_probability=.5,market_probability=.5) for i in [1,2]]
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'f.json';now=datetime(2030,1,1,1,tzinfo=timezone.utc)
            original=freeze(rows,p,{'synthetic':True},now)
            with self.assertRaises(FileExistsError):freeze(rows,p,{},now)
            with self.assertRaises(ValueError):freeze(rows,Path(temp)/'late.json',{},datetime(2030,1,3,tzinfo=timezone.utc))
            r=record_results(p,[dict(race_id='synthetic',verified=True,source_url='https://example.test/results',available_at='2030-01-02T01:00:00Z',status='FINAL',winner_runner_id='1',scratched_runner_ids=[])],Path(temp)/'r.json',datetime(2030,1,3,tzinfo=timezone.utc),expected_sha256=original['sha256'])
            self.assertEqual(original['sha256'],r['forecast_sha256'])
            self.assertEqual(r['unresolved'], [])
            pending = record_results(p, [], Path(temp)/'pending.json',
                                     expected_sha256=original['sha256'])
            self.assertEqual(pending['unresolved'], [
                {'race_id': 'synthetic', 'reason': 'No verified official disposition supplied'}])
            self.assertEqual(pending['dispositions'], {})

    def test_result_cli_receipt_and_unchanged_field_comparison(self):
        rows=[dict(race_id='r',runner_id=str(i),country='NZ',
                   scheduled_start_utc='2025-06-02T00:00:00Z',
                   odds_captured_at_utc='2025-06-01T00:00:00Z',
                   source_url='https://example.test/quotes',odds=2,
                   v6_probability=p,v7_probability=p,candidate2_probability=p,
                   market_probability=.5) for i,p in enumerate([.75,.25],1)]
        with tempfile.TemporaryDirectory() as temp:
            p,receipt,results,output=(Path(temp)/name for name in ['f.json','receipt.json','r.json','out.json'])
            now=datetime(2025,6,1,1,tzinfo=timezone.utc)
            with self.assertRaisesRegex(ValueError,'normalized field'):
                freeze([rows[0],{k:v for k,v in rows[1].items() if k!='candidate2_probability'}],p,{},now)
            self.assertFalse(p.exists())
            receipt.write_text(json.dumps(freeze(iter(rows),p,{},now)))
            result=dict(race_id='r',verified=True,source_url='https://example.test/results',
                        available_at='2025-06-02T01:00:00Z',status='FINAL',
                        winner_runner_id='2',scratched_runner_ids=[])
            results.write_text(json.dumps([result]))
            with self.assertRaisesRegex(ValueError,'differs from its receipt'):
                record_results(p,[result],output,expected_sha256='wrong')
            self.assertFalse(output.exists())
            before=p.read_bytes()
            subprocess.run([sys.executable,'-m','v7.shadow','--forecast',str(p),
                            '--receipt',str(receipt),'--results',str(results),
                            '--output',str(output)],check=True,capture_output=True)
            self.assertEqual(p.read_bytes(),before)
            nz=json.loads(output.read_text())['probability_comparison']['by_country']['NZ']
            self.assertEqual(nz['candidate2']['races'],1)
            self.assertEqual(nz['candidate2']['top_pick_strike'],0)
            self.assertAlmostEqual(nz['candidate2']['brier_per_race'],1.125)
            void=record_results(p,[dict(result,winner_runner_id='1',scratched_runner_ids=['2'])],
                                Path(temp)/'void.json', expected_sha256=json.loads(receipt.read_text())['sha256'])
            self.assertEqual(void['probability_comparison']['excluded'],{'scratchings_present':1})
            self.assertEqual(void['probability_comparison']['by_country'],{})

if __name__=='__main__':unittest.main()
