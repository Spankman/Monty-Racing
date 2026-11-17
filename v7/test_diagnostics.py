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
            r=record_results(p,[dict(race_id='synthetic',verified=True,source_url='https://example.test/results',available_at='2030-01-02T01:00:00Z',status='FINAL',winner_runner_id='1')],Path(temp)/'r.json',datetime(2030,1,3,tzinfo=timezone.utc))
            self.assertEqual(original['sha256'],r['forecast_sha256'])

if __name__=='__main__':unittest.main()
