"""Simulated contracts only; live evidence is recorded separately."""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import monty_operations as ops
from operations.render import render


class CommandTests(unittest.TestCase):
    def test_all_commands_and_single_races(self):
        for cmd,version,mode in [('RM6','V6','official'),('RM7','V7','official'),('RM6PS','V6','provisional'),('RM7PS','V7','provisional')]:
            r=ops.command(cmd,'2026-11-23');self.assertEqual((r['version'],r['view']),(version,mode))
        for cmd in ['RM6 Royal Randwick R4','RM7 Te Rapa 12']:
            r=ops.command(cmd);self.assertTrue(r['meeting']);self.assertEqual(r['view'],'provisional')
        self.assertEqual(ops.command('C')['view'],'status')
        for cmd in ['RM8','RM6 x 0','RM6 $(id) 1','RM6PS track 2','RM6 track 51']:
            with self.assertRaises(ValueError):ops.command(cmd)

    def test_stale_future_and_closed(self):
        now=ops.utcnow();row=dict(captured_at=now.isoformat(),scheduled_start=(now+timedelta(hours=1)).isoformat())
        self.assertEqual(ops.freshness(row,now),'FRESH AT CHECK TIME')
        self.assertIn('STALE',ops.freshness(row,now+timedelta(minutes=6)))
        self.assertIn('STALE',ops.freshness(row,now-timedelta(seconds=1)))
        row['scheduled_start']=now.isoformat();self.assertIn('CLOSED',ops.freshness(row,now))
        self.assertIn('UNVERIFIED',ops.freshness({},now))

    def test_price_ladder_and_roughies(self):
        for odds,count in [([4,5,6,7],1),([3,4,5,6],2),([3,3,4,5],3),([3,3,3,4],4)]:
            rows=[dict(number=str(i+1),horse='Horse '+str(i),odds=o,probability=p) for i,(o,p) in enumerate(zip(odds,[.4,.3,.2,.1]))]
            r=ops.selection(rows);self.assertEqual(len(r['ordered_selections']),count)
            self.assertEqual(r['recommended_bet_type'],'NO BET')
            self.assertTrue(all(x['bet_type']=='WIN' for x in r['roughies']))


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.v7=self.root/'engine';(self.v7/'v7/artifacts').mkdir(parents=True)
        model=self.v7/'v7/artifacts/fold_3_model.json';model.write_text('{}')
        self.digest=ops.sha(model)
        self.now=ops.utcnow();self.day=self.now.astimezone(ops.TZ).date().isoformat()
        self.payload=dict(success=True,data=[dict(venue='Test',country='AU',date=self.day,type='T',races=[dict(number=1,name='Benchmark 60',status='open',jump_time=(self.now+timedelta(hours=1)).isoformat(),distance=1200,track_condition='Good 4',runners=[dict(number=i,name='Horse '+str(i),is_scratched=False,barrier=i,odds=[dict(bookmaker='TAB',win=o)]) for i,o in [(1,3),(2,4),(3,6)]])])],meta={})
        self.patches=[patch('monty.integrity.verify_artifacts',return_value=55),patch.object(ops,'V7_MODEL_SHA',self.digest),patch.object(ops.subprocess,'check_output',return_value=ops.V7_COMMIT)]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.calls=[]

    def scorer(self,version,path,meta,directory,v7_root):
        self.calls.append((version,path.read_bytes()))
        d=json.loads(path.read_text())
        return [dict(number=r['number'],horse=r['horse'],odds=r['odds'],probability=p) for r,p in zip(d['runners'],[.5,.3,.2])]

    def run_it(self,**kw):
        params=dict(payload=self.payload,captured=self.now,fixture=True,scorer=self.scorer)
        params.update(kw)
        return ops.execute(self.day,self.root/'output',self.v7,run_id='test',**params)

    def test_shared_snapshot_official_provisional_and_integrity(self):
        f=self.run_it();self.assertEqual(f['status'],'COMPLETED_NO_BET')
        self.assertEqual([c[0] for c in self.calls],['V6','V7']);self.assertEqual(self.calls[0][1],self.calls[1][1])
        p=self.root/'output/public';receipt=json.loads((p/'receipt.json').read_text())
        self.assertEqual(receipt['forecast_sha256'],ops.sha(p/'forecast.json'))
        official=ops.projection(f,dict(version='V6',view='official'));provisional=ops.projection(f,dict(version='V7',view='provisional'))
        self.assertEqual(official['races'][0]['result']['ordered_selections'],[])
        self.assertTrue(provisional['races'][0]['result']['ordered_selections'])
        self.assertFalse(provisional['races'][0]['result']['betting_authorised'])
        self.assertIn('STALE',ops.projection(f,dict(version='V7',view='provisional'),self.now+timedelta(minutes=6))['races'][0]['result']['freshness_at_retrieval'])
        self.assertEqual(f['source_mode'],'SIMULATED FIXTURE')
        with self.assertRaises(FileExistsError):self.run_it()

    def test_no_silent_model_fallback(self):
        def broken(v,*args):
            if v=='V7':raise RuntimeError('DO NOT PUBLISH secret')
            return self.scorer(v,*args)
        f=self.run_it(scorer=broken)
        self.assertEqual(f['races'][0]['models']['V7']['status'],'FAILED')
        self.assertEqual(f['races'][0]['models']['V6']['status'],'SCORED')
        self.assertNotIn('secret',json.dumps(f));self.assertEqual(f['status'],'PARTIAL_OR_BLOCKED')

    def test_identity_and_price_changes_rejected(self):
        def bad(v,*args):
            rows=self.scorer(v,*args);rows[0]['odds']=999;return rows
        f=self.run_it(scorer=bad)
        self.assertTrue(all(m['status']=='FAILED' for m in f['races'][0]['models'].values()))

    def test_stale_capture_never_scored(self):
        f=self.run_it(captured=self.now-timedelta(minutes=6))
        self.assertEqual(f['status'],'FAILED');self.assertFalse(self.calls)

    def test_single_race_missing_and_country_ambiguity(self):
        f=self.run_it(request=ops.command('RM6 Missing 2',self.day))
        self.assertEqual(f['status'],'FAILED');self.assertFalse(self.calls)

    def test_unknown_country_not_guessed(self):
        self.payload['data'][0]['country']=None
        f=self.run_it();self.assertFalse(f['races']);self.assertFalse(self.calls)

    def test_no_named_price_blocks_both(self):
        self.payload['data'][0]['races'][0]['runners'][0]['odds']=[]
        self.payload['data'][0]['races'][0]['runners'][0]['fixed_win']=3
        f=self.run_it();self.assertFalse(self.calls)
        self.assertEqual(f['races'][0]['models']['V6']['status'],'BLOCKED')

    def test_render_escapes_names_and_has_copyable_ticket(self):
        f=self.run_it();v=ops.projection(f,dict(version='V7',view='provisional'))
        v['races'][0]['result']['ordered_selections'][0]['horse']='<script>alert(1)</script>'
        page=render(v)
        self.assertIn('&lt;script&gt;',page);self.assertNotIn('<script>',page)
        self.assertIn('text-align:right',page);self.assertIn('<textarea readonly',page)
        self.assertIn('IN MONTY WE TRUST',page)


class TransportTests(unittest.TestCase):
    def test_owner_queue_only_and_strict_parameters(self):
        from operations import transport
        issues=[dict(number=n,title='Monty command: RM6PS',body=body,
                     user=dict(login=user),created_at='2026-11-22T22:00:00Z')
                for n,user,body in [(1,'Stranger','{}'),(2,'Spankman','{"shell":"oops"}'),(3,'Spankman','{"date":"2026-11-23"}')]]
        with patch.object(transport,'api',return_value=issues),patch.object(transport,'read',return_value=None):
            queue=list(transport.requests())
        self.assertEqual([n for n,_ in queue],[3])

    def test_raw_inputs_never_accepted_for_publication(self):
        from operations import transport
        with TemporaryDirectory() as d:
            (Path(d)/'provider_response.json').write_text('{"private":"do not publish"}')
            with patch.object(transport,'api',return_value={'ref':'exists'}):
                with self.assertRaisesRegex(ValueError,'Unapproved public file'):
                    transport.publish(d,'123','2026-11-23')

    def test_failure_envelope_does_not_reuse_old_forecast(self):
        from operations.failure import failed
        with TemporaryDirectory() as d:
            failed(d,'failure-run','2026-11-23','runner_startup_failed')
            p=Path(d)/'public';f=json.loads((p/'forecast.json').read_text());r=json.loads((p/'receipt.json').read_text())
            self.assertEqual(f['status'],'FAILED');self.assertEqual(f['races'],[])
            self.assertEqual(r['forecast_sha256'],ops.sha(p/'forecast.json'))


if __name__=='__main__':unittest.main()
