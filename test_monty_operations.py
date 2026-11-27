"""Simulated contracts only; live evidence is recorded separately."""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import monty_operations as ops
from operations.render import render


class CommandTests(unittest.TestCase):
    def test_all_commands_and_single_races(self):
        for cmd,version,mode in [('RM6','V6','official'),('RM7','V7','shadow'),('RM6PS','V6','provisional'),('RM7PS','V7','provisional')]:
            r=ops.command(cmd,'2026-11-23');self.assertEqual((r['version'],r['view']),(version,mode))
        for cmd in ['RM6 Royal Randwick R4','RM7 Te Rapa 12']:
            r=ops.command(cmd);self.assertTrue(r['meeting']);self.assertEqual(r['view'],'provisional')
        self.assertEqual(ops.command('C')['view'],'status')
        for cmd in ['RM8','RM6 x 0','RM6 $(id) 1','RM6 track 51']:
            with self.assertRaises(ValueError):ops.command(cmd)

    def test_shorthand_and_explicit_provisional_single_races(self):
        for text,version in [('Ballina 4','V6'),('Ballina R4','V6'),('RM6PS Ballina 4','V6'),
                             ('RM7PS Ballina 4','V7'),('RMV6PS Ballina 4','V6'),('RMV7PS Ballina R4','V7')]:
            with self.subTest(command=text):
                req=ops.command(text,'2026-11-23','AU')
                self.assertEqual((req['version'],req['view'],req['meeting'],req['race']),(version,'provisional','Ballina','4'))
        self.assertEqual(ops.command('C')['view'],'status')

    def test_shorthand_does_not_accept_unsafe_or_invalid_races(self):
        for text in ['Ballina 0','Ballina 51','Ballina 4; id','RM8 Ballina 4','RM7PS $(id) 4']:
            with self.subTest(command=text),self.assertRaises(ValueError):ops.command(text)

    def test_stale_future_and_closed(self):
        now=ops.utcnow();row=dict(captured_at=now.isoformat(),scheduled_start=(now+timedelta(hours=1)).isoformat())
        self.assertEqual(ops.freshness(row,now),'FRESH AT CHECK TIME')
        self.assertIn('STALE',ops.freshness(row,now+timedelta(minutes=6)))
        self.assertIn('STALE',ops.freshness(row,now+timedelta(seconds=ops.MAX_AGE_SECONDS)))
        self.assertIn('STALE',ops.freshness(row,now-timedelta(seconds=1)))
        row['scheduled_start']=now.isoformat();self.assertIn('CLOSED',ops.freshness(row,now))
        self.assertIn('UNVERIFIED',ops.freshness({},now))

    def test_price_ladder_and_roughies(self):
        for odds,count in [([4,5,6,7],1),([3,4,5,6],2),([3,3,4,5],3),([3,3,3,4],4)]:
            rows=[dict(number=str(i+1),horse='Horse '+str(i),odds=o,probability=p) for i,(o,p) in enumerate(zip(odds,[.4,.3,.2,.1]))]
            r=ops.selection(rows);self.assertEqual(len(r['ordered_selections']),count)
            self.assertEqual(r['recommended_bet_type'],'NO BET')
            self.assertTrue(all(x['bet_type']=='WIN' for x in r['roughies']))


    def test_v7_checks_roughie_thresholds_across_the_whole_field(self):
        runners = [
            dict(number='1', horse='Highest Edge', odds=3.5, probability=.35, value_watch={'number':'1'}),
            dict(number='2', horse='Roughie', odds=6., probability=.19),
            dict(number='3', horse='Too Unlikely', odds=22., probability=.05),
            dict(number='4', horse='No Edge', odds=5., probability=.20),
            dict(number='5', horse='Under Minimum Price', odds=3., probability=.21),
        ]
        result = ops.selection(runners, 'V7')
        self.assertEqual(result['best_chance']['number'], '1')
        self.assertEqual([r['number'] for r in result['roughies']], ['2'])
        self.assertEqual(result['roughies'][0]['bet_type'], 'WIN')
        self.assertEqual(result['official_classification'], 'DATA BLOCKED')
        self.assertFalse(result['betting_authorised'])


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
        f=self.run_it();self.assertEqual(f['status'],'COMPLETED_ASSESSMENTS')
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

    def test_full_day_country_scope_does_not_include_other_jurisdiction(self):
        self.payload['data'][0]['country']='NZ'
        f=self.run_it(request=ops.command('RM6',self.day,'AU'))
        self.assertEqual(f['races'],[]);self.assertFalse(self.calls)

    def test_malformed_nz_races_do_not_block_au_daily(self):
        self.payload['data'].append(dict(self.payload['data'][0], country='NZ', races=None))
        result = self.run_it(request=ops.command('RM6', self.day, 'AU'))
        self.assertEqual(result['status'], 'COMPLETED_ASSESSMENTS')
        self.assertEqual(result['coverage']['jurisdictions_observed'], ['AU'])

    def test_fresh_official_view_renders_diagnostic_roughies_only(self):
        from operations.render import render
        forecast = self.run_it()
        view = ops.projection(forecast, dict(version='V6', view='official'), self.now)
        for show in (ops.ticket, render):
            self.assertIn('RUFFY / VALUE WATCH', show(view, now=self.now))
            self.assertNotIn('RUFFY / VALUE WATCH', show(view, now=self.now+timedelta(minutes=6)))
        self.assertFalse(view['races'][0]['result']['betting_authorised'])

    def test_same_capture_features_and_provisional_price_gate_for_both_scopes(self):
        full=self.run_it()
        single=ops.execute(self.day,self.root/'single',self.v7,run_id='single',payload=self.payload,
                           captured=self.now,request=ops.command('RM6 Test 1',self.day),fixture=True,scorer=self.scorer)
        self.assertEqual(full['races'][0]['shared_model_input_sha256'],single['races'][0]['shared_model_input_sha256'])
        for version in ['V6','V7']:
            self.assertEqual(single['races'][0]['models'][version]['status'],'SCORED')
        for runner in self.payload['data'][0]['races'][0]['runners']:
            runner.update(fixed_win=runner['odds'][0]['win'],odds=[])
        for name,req in [('provisional-full',ops.command('RM6PS',self.day)),('provisional-single',ops.command('RM6 Test 1',self.day)),('shadow-full',ops.command('RM7',self.day))]:
            f=ops.execute(self.day,self.root/name,self.v7,run_id=name,payload=self.payload,captured=self.now,
                          request=req,fixture=True,scorer=self.scorer)
            self.assertTrue(all(r['status']=='SCORED' for r in f['races'][0]['models'].values()))
            self.assertTrue(all(r['official_classification']=='DATA BLOCKED' for r in f['races'][0]['models'].values()))
            for version in ('V6','V7'):
                result=f['races'][0]['models'][version]
                self.assertFalse(result['betting_authorised'])
                self.assertIn('attribution incomplete',result['bookmaker'])
                self.assertIn('named_bookmaker_fixed_win_not_available_for_entire_field',result['no_bet_reasons'])
                self.assertFalse(ops.projection(f,dict(version=version,view='official'))['races'][0]['result']['ordered_selections'])
                self.assertTrue(ops.projection(f,dict(version=version,view='provisional'))['races'][0]['result']['ordered_selections'])

    def test_no_silent_model_fallback(self):
        def broken(v,*args):
            if v=='V7':raise RuntimeError('DO NOT PUBLISH secret')
            return self.scorer(v,*args)
        f=self.run_it(scorer=broken)
        self.assertEqual(f['races'][0]['models']['V7']['status'],'FAILED')
        self.assertEqual(f['races'][0]['models']['V6']['status'],'SCORED')
        self.assertNotIn('secret',json.dumps(f));self.assertEqual(f['status'],'COMPLETED_ASSESSMENTS')

    def test_identity_and_price_changes_rejected(self):
        def bad(v,*args):
            rows=self.scorer(v,*args);rows[0]['odds']=999;return rows
        f=self.run_it(scorer=bad)
        self.assertTrue(all(m['status']=='FAILED' for m in f['races'][0]['models'].values()))

    def test_stale_capture_never_scored(self):
        f=self.run_it(captured=self.now-timedelta(minutes=6))
        self.assertEqual(f['status'],'EXPIRED');self.assertFalse(self.calls)

    def test_single_race_missing_and_country_ambiguity(self):
        f=self.run_it(request=ops.command('RM6 Missing 2',self.day))
        self.assertEqual(f['status'],'DATA_BLOCKED');self.assertFalse(self.calls)
        self.assertEqual(f['operational_outcome'], 'RACE NOT FOUND')

    def test_unknown_country_not_guessed(self):
        self.payload['data'][0]['country']=None
        f=self.run_it();self.assertFalse(f['races']);self.assertFalse(self.calls)

    def test_mixed_price_sources_block_v7_only(self):
        self.payload['data'][0]['races'][0]['runners'][0]['odds']=[]
        self.payload['data'][0]['races'][0]['runners'][0]['fixed_win']=3
        f=self.run_it()
        self.assertEqual([version for version,_ in self.calls],['V6'])
        self.assertEqual(f['races'][0]['models']['V6']['status'],'SCORED')
        v7=f['races'][0]['models']['V7']
        self.assertEqual(v7['status'],'BLOCKED')
        self.assertIn('V7_requires_consistent_price_provenance',v7['no_bet_reasons'])

    def test_daily_missing_complete_market_still_blocks_scoring(self):
        self.payload['data'][0]['races'][0]['runners'][0]['odds']=[]
        f=self.run_it()
        self.assertFalse(self.calls)
        self.assertEqual(f['status'],'DATA_BLOCKED')
        self.assertFalse(f['races'])

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


class SchedulerTests(unittest.TestCase):
    def test_catchup_after_0810_only_without_completed_attempt(self):
        from operations.worker import daily_due
        from datetime import datetime
        self.assertFalse(daily_due(datetime(2026,11,23,8,9),None))
        self.assertTrue(daily_due(datetime(2026,11,23,8,10),None))
        self.assertTrue(daily_due(datetime(2026,11,23,8,20),None))
        self.assertFalse(daily_due(datetime(2026,11,23,8,20),{'status':'FAILED'}))



class IssueDeliveryTests(unittest.TestCase):
    def test_issue_result_survives_results_branch_denial(self):
        from operations import issue_delivery, worker, transport
        from operations.failure import failed
        with TemporaryDirectory() as root:
            out = Path(root) / 'attempt'
            req = ops.command('RM6 Ballina 1', '2026-11-24')
            def run(*args, **kwargs):
                failed(out, '123-1-200', req['date'], 'test_missing_provider')
                return subprocess.CompletedProcess(args, 1, stderr='')
            with (patch.object(issue_delivery, 'enabled', return_value=True),
                  patch.object(issue_delivery, 'report', return_value={'id': 20}) as report,
                  patch.object(worker, 'read', return_value=None),
                  patch.object(worker, 'publish', side_effect=transport.GitHubError(403)),
                  patch.object(worker, 'lifecycle') as lifecycle,
                  patch.object(worker.subprocess, 'run', side_effect=run)):
                result = worker.operate(req, 200, '123-1-200', 'workflow', out)
            lifecycle.assert_not_called()
            self.assertEqual(result['request_status'], 'FAILED')
            self.assertEqual([call.args[1] for call in report.call_args_list], ['running', 'terminal'])
            self.assertIn('test_missing_provider', report.call_args.args[2])
            self.assertIn('Results-branch publication unavailable', report.call_args.args[2])

    def test_retry_does_not_duplicate_issue_result_after_lost_response(self):
        from operations import issue_delivery, transport
        tag = issue_delivery.marker(201, 'terminal')
        confirmed = {'user': {'login': issue_delivery.BOT}, 'body': tag + '\nA result'}
        forged = {'user': {'login': 'example'}, 'body': tag}
        with (patch.object(transport, 'api', side_effect=[[forged], transport.GitHubError(500), [confirmed]]) as api,
              patch.object(transport, 'sleep')):
            self.assertEqual(issue_delivery.send(201, 'terminal', 'A result'), confirmed)
        self.assertEqual(sum(len(call.args) > 1 and call.args[1] == 'POST' for call in api.call_args_list), 1)


class ConnectorClientTests(unittest.TestCase):
    """Simulate GitHub reads and writes. No connectors, providers or inference are called."""

    def setUp(self):
        from operations import client, transport
        self.client = client
        self.transport = transport
        self.day = '2026-11-23'
        self.capture = ops.timestamp(self.day + 'T08:10:00+10:00')
        self.jump = self.capture + timedelta(hours=4)
        self.files = {}
        self.enterContext(patch.object(transport, 'requests', return_value=[]))
        self.enqueue = self.enterContext(patch.object(transport, 'enqueue', return_value=200))
        self.enterContext(patch.object(transport, 'read', side_effect=self.files.get))
        self.enterContext(patch.object(transport, 'read_bytes', side_effect=self.files.get))

    def save(self, index_path, run_id, captured, *, status='COMPLETED_NO_BET'):
        selections = ops.selection([
            dict(number='1', horse='Leading Horse', odds=4, probability=.5),
            dict(number='2', horse='Other Horse', odds=5, probability=.3),
            dict(number='3', horse='Third Horse', odds=6, probability=.2),
        ])
        race = dict(meeting='Ballina', race='1', country='AU', captured_at=captured.isoformat(),
                    scheduled_start=self.jump.isoformat(), models={'V6': selections, 'V7': selections})
        forecast = dict(run_id=run_id, status=status, date=self.day, source_mode='LIVE', provider='PuntersEdge',
                        captured_at=captured.isoformat(), races=[race] if status != 'FAILED' else [],
                        valid_until=(captured + timedelta(minutes=5)).isoformat())
        raw = json.dumps(forecast).encode()
        digest = hashlib.sha256(raw).hexdigest()
        receipt = dict(run_id=run_id, status=status, forecast_sha256=digest)
        self.files[f'{run_id}/forecast.json'] = raw
        self.files[f'{run_id}/receipt.json'] = receipt
        self.files[index_path] = dict(run_id=run_id, status=status, forecast_sha256=digest,
                                      forecast_path=f'{run_id}/forecast.json', receipt_path=f'{run_id}/receipt.json')

    def test_0830_daily_request_uses_new_id_and_rechecks_completed_capture(self):
        at_0830 = self.capture + timedelta(minutes=20)
        daily = f'daily/{self.day}/latest.json'
        self.save(daily, 'previous', self.capture)
        for name in ('RM6', 'RM7'):
            self.enqueue.reset_mock()
            self.assertEqual(self.client.handle(name, now=at_0830)['request_id'], 200)
            self.enqueue.assert_called_once()
        pending = self.client.handle('RM7', request_id=200, now=at_0830)
        self.assertEqual(pending['request_status'], 'QUEUED')
        self.assertIsNone(pending['run_id'])
        key = 'requests/200.json'
        self.files[key] = dict(request_status='RUNNING', run_id='current', workflow_url='workflow')
        running = self.client.handle('RM7', request_id=200, now=at_0830)
        self.assertEqual((running['request_status'], running['workflow_url']), ('RUNNING', 'workflow'))
        self.save(key, 'current', at_0830)
        result = self.client.handle('RM7', request_id=200, now=at_0830 + timedelta(minutes=1))
        self.assertEqual((result['request_status'], result['run_id']), ('COMPLETED', 'current'))
        self.assertEqual(result['capture_age_seconds'], 60)
        self.assertIn('SHADOW SELECTION SLIP', result['ticket'])
        self.assertIn('Leading Horse', result['ticket'])
        self.assertIn('NO BET', result['ticket'])
        expired = self.client.handle('RM7', request_id=200, now=at_0830 + timedelta(minutes=6))
        self.assertEqual(expired['freshness'], 'EXPIRED')
        self.assertNotIn('ticket', expired)
        self.enqueue.assert_called_once()

    def test_c_follows_latest_or_explicit_request_and_never_submits(self):
        self.save(f'daily/{self.day}/latest.json', 'daily', self.capture)
        self.save('requests/201.json', 'failed', self.capture, status='FAILED')
        self.files['requests/202.json'] = dict(request_status='RUNNING', run_id='current',
                                               workflow_url='workflow')
        entries = [(202, ops.command('RM6', self.day)), (201, ops.command('RM7', self.day))]
        with patch.object(self.transport, 'requests', return_value=iter(entries)):
            status = self.client.handle('C', now=self.capture)
        self.assertEqual((status['request_id'], status['request_status']), (202, 'RUNNING'))
        failed = self.client.handle('C', request_id=201, now=self.capture)
        self.assertEqual((failed['request_status'], failed['semantic_outcome']), ('FAILED', 'FAILED'))
        self.assertIsNotNone(failed['receipt'])
        self.assertEqual(failed['captured_at'], self.capture.isoformat())
        self.assertEqual(failed['capture_age_seconds'], 0)
        self.assertIsNotNone(failed['valid_until'])
        self.assertNotIn('ticket', failed)
        self.enqueue.assert_not_called()

    def test_every_selection_command_retrieves_its_view(self):
        self.save('requests/200.json', 'completed', self.capture)
        for name, expected in [('RM6', 'official'), ('RM7', 'shadow'), ('RM6PS', 'provisional'),
                               ('RM7PS', 'provisional'), ('RM6 Ballina 1', 'provisional'),
                               ('RM7 Ballina 1', 'provisional')]:
            with self.subTest(name=name):
                response = self.client.handle(name, request_id=200, now=self.capture)
                self.assertEqual(response['view']['view'], expected)
                self.assertEqual(len(response['view']['races']), 1)
                self.assertEqual('Leading Horse' in response['ticket'], expected != 'official')
        self.enqueue.assert_not_called()

    def test_failed_request_never_falls_back_and_cannot_requeue(self):
        self.save(f'daily/{self.day}/latest.json', 'daily', self.capture)
        self.save('requests/200.json', 'failed', self.capture, status='FAILED')
        status = self.client.handle('RM6', request_id=200, now=self.capture)
        self.assertEqual(status['semantic_outcome'], 'FAILED')
        self.assertNotIn('view', status)
        self.enqueue.assert_not_called()

    def test_workflow_ending_without_publication_is_explicit(self):
        self.files['requests/200.json'] = dict(request_status='RUNNING', run_id='123-1-200',
                                             workflow_url='workflow')
        with patch.object(self.transport, 'api', return_value={'status': 'completed', 'conclusion': 'failure'}):
            response = self.client.handle('RM6', request_id=200, now=self.capture)
        self.assertEqual(response['request_status'], 'FAILED')
        self.assertEqual(response['workflow_conclusion'], 'failure')
        self.assertEqual(response['semantic_outcome'], 'WORKFLOW_ENDED_WITHOUT_PUBLICATION')
        self.assertNotIn('ticket', response)
        self.enqueue.assert_not_called()

    def test_wait_reads_the_same_issue_through_publication(self):
        self.save('requests/200.json', 'done', self.capture)
        saved = self.files['requests/200.json']
        request = ops.command('RM7PS', self.day)
        states = iter([None, {'request_status': 'RUNNING', 'run_id': '123-1-200'}, saved])
        with (patch.object(self.transport, 'read', side_effect=lambda path: next(states)
                           if path == 'requests/200.json' else self.files.get(path)) as read,
              patch.object(self.client, 'utcnow', return_value=self.capture),
              patch.object(self.client, 'sleep')):
            result = self.client.wait_for_request(200, request)
        self.assertEqual(result['request_status'], 'COMPLETED')
        self.assertEqual(result['view']['version'], 'V7')
        self.assertEqual(sum(call.args == ('requests/200.json',) for call in read.call_args_list), 3)
        self.enqueue.assert_not_called()

    def test_wait_reports_unacknowledged_issue_and_hands_off_exact_race(self):
        request = ops.command('RM6PS Ballina 1', self.day)
        result = self.client.wait_for_request(200, request, timeout=0)
        self.assertEqual(result['delivery_status'], 'WORKER_ACKNOWLEDGEMENT_TIMEOUT')
        self.assertEqual(result['form_assessment_requests'][0]['target']['meeting'], 'Ballina')
        self.assertEqual(result['request_status'], 'QUEUED')
        self.enqueue.assert_not_called()

    def test_published_failure_without_receipt_still_requests_form(self):
        self.files['requests/200.json'] = dict(status='FAILED', blockers=['publication_failed'])
        result = self.client.handle('RM7PS Ballina 1', request_id=200, now=self.capture)
        self.assertEqual(result['form_assessment_requests'][0]['reasons'], ['publication_failed'])
        self.enqueue.assert_not_called()

    def test_c_reports_aged_unacknowledged_issue_without_submit(self):
        issue = dict(state='open', title='Monty command: RM6 Ballina 1', user={'login': 'Spankman'},
                     body=json.dumps({'date': self.day}), created_at=self.capture.isoformat())
        with patch.object(self.transport, 'api', return_value=issue) as api:
            result = self.client.handle('C', request_id=200, now=self.capture + timedelta(minutes=3))
        self.assertEqual(result['delivery_status'], 'WORKER_ACKNOWLEDGEMENT_TIMEOUT')
        self.assertEqual(result['request_status'], 'QUEUED')
        api.assert_called_once_with('issues/200', optional=True)
        self.enqueue.assert_not_called()

    def test_c_reports_aged_running_index_without_changing_worker_state(self):
        self.files['requests/200.json'] = dict(request_status='RUNNING', run_id='123-1-200',
                                             updated_at=self.capture.isoformat(), workflow_url='workflow')
        with patch.object(self.transport, 'api', return_value={'status': 'in_progress'}):
            result = self.client.handle('C', request_id=200, now=self.capture + timedelta(minutes=3))
        self.assertEqual(result['delivery_status'], 'RESULT_PUBLICATION_TIMEOUT')
        self.assertEqual(result['request_status'], 'RUNNING')
        self.enqueue.assert_not_called()

    def test_corrupt_receipt_prevents_display(self):
        self.save('requests/200.json', 'saved', self.capture)
        self.files['saved/receipt.json']['forecast_sha256'] = 'tampered'
        result = self.client.handle('RM7', request_id=200, now=self.capture)
        self.assertEqual(result['semantic_outcome'], 'INTEGRITY_CHECK_FAILED')
        self.assertNotIn('ticket', result)

    def test_render_rechecks_old_saved_view_without_mutating_it(self):
        self.save('requests/200.json', 'saved', self.capture)
        view = self.client.handle('RM7', request_id=200, now=self.capture)['view']
        original = json.dumps(view)
        later = self.capture + timedelta(minutes=20)
        for content in (ops.ticket(view, now=later), render(view, now=later)):
            self.assertIn('STALE', content)
            self.assertNotIn('Leading Horse', content)
        self.assertEqual(json.dumps(view), original)


class WorkerFailureTests(unittest.TestCase):
    def test_queue_persists_request_id_and_workflow_url_before_inference(self):
        import os
        from operations import worker
        req = ops.command('RM6', '2026-11-23')
        records = []

        def run(req, number, run_id, url, out):
            self.assertEqual(records[0]['request_status'], 'QUEUED')
            self.assertEqual(records[0]['request_id'], number)
            self.assertEqual(records[0]['workflow_url'], url)
            self.assertEqual(records[0]['run_id'], run_id)
            return records[0]

        with (patch.dict(os.environ, dict(OPERATIONS_MODE='queue', OPERATIONS_ISSUE='200', GITHUB_RUN_ID='123')),
              patch.object(worker, 'request_for_issue', return_value=req),
              patch.object(worker, 'requests', return_value=[(200, req)]),
              patch.object(worker, 'read', return_value=None),
              patch.object(worker, 'record_request', side_effect=records.append),
              patch.object(worker, 'operate', side_effect=run) as operate,
              patch('builtins.print')):
            worker.main()
        operate.assert_called_once()

    def test_timeout_and_launch_failure_produce_immutable_failure_envelope(self):
        import subprocess
        from operations import worker
        day = '2026-11-23'
        for error, reason in [(subprocess.TimeoutExpired('runner', 1000), 'runner_timeout'),
                              (OSError('private diagnostic'), 'runner_launch_failed')]:
            with self.subTest(reason=reason), TemporaryDirectory() as directory:
                out = Path(directory) / 'run'
                with (patch.object(worker, 'lifecycle') as lifecycle,
                      patch.object(worker.subprocess, 'run', side_effect=error),
                      patch.object(worker, 'publish') as publish):
                    worker.operate(ops.command('RM6', day), 200, 'run', 'workflow', out)
                    lifecycle.assert_called_once_with(ops.command('RM6', day), 200, 'run', 'workflow', 'RUNNING')
                    publish.assert_called_once()
                forecast = json.loads((out / 'public/forecast.json').read_text())
                self.assertEqual(forecast['status'], 'FAILED')
                self.assertEqual(forecast['blockers'], [reason])

    def test_publication_failure_exposes_terminal_failure_without_old_output(self):
        from operations import worker
        day = '2026-11-23'
        req = ops.command('RM6', day)
        with TemporaryDirectory() as directory:
            out = Path(directory) / 'run'
            with (patch.object(worker, 'lifecycle') as lifecycle,
                  patch.object(worker.subprocess, 'run', side_effect=OSError),
                  patch.object(worker, 'read', return_value={'run_id': 'old', 'receipt_path': 'old'}),
                  patch.object(worker, 'publish', side_effect=RuntimeError('private diagnostic'))):
                with self.assertRaisesRegex(RuntimeError, '^publication_failed$'):
                    worker.operate(req, 200, 'new', 'workflow', out)
            lifecycle.assert_called_with(req, 200, 'new', 'workflow', 'FAILED', 'publication_failed')


class StageTimingTests(unittest.TestCase):
    def test_reports_elapsed_time_even_when_the_operation_fails(self):
        from operations import timing
        with (patch.object(timing, 'monotonic', side_effect=[3.0, 4.25]),
              patch.object(timing, 'emit') as emit):
            with self.assertRaisesRegex(ValueError, 'private'):
                with timing.timed('provider_fetch', 'run'):
                    raise ValueError('private')
        emit.assert_called_once_with('provider_fetch', 1.25, 'error', 'run')

    def test_parent_only_forwards_valid_timing_fields(self):
        from operations import timing
        lines = b'''private stderr
MONTY_TIMING {"stage":"provider_fetch","elapsed_seconds":1.2,"outcome":"ok","run_id":"ignore","secret":"discard"}
MONTY_TIMING {"stage":"secret","elapsed_seconds":1,"outcome":"ok"}
MONTY_TIMING {"stage":"provider_fetch","elapsed_seconds":NaN,"outcome":"ok"}
MONTY_TIMING {"stage":"provider_fetch","elapsed_seconds":true,"outcome":"ok"}
MONTY_TIMING not-json
'''
        with patch.object(timing, 'emit') as emit:
            timing.forward_runner_timings(lines, 'parent')
        emit.assert_called_once_with('provider_fetch', 1.2, 'ok', 'parent')


if __name__ == '__main__':
    unittest.main()
