"""Offline regression tests; live connector evidence is recorded separately."""
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError,URLError

import monty_operations as ops
from operations import client,transport,worker
import test_monty_operations as original


class SimplifiedClientTests(unittest.TestCase):
    setUp=original.ConnectorClientTests.setUp
    save=original.ConnectorClientTests.save
    def test_provisional_aliases(self):
        for alias,canonical in [('RMV6PS','RM6PS'),('RMV7PS','RM7PS')]:
            self.assertEqual(ops.command(alias,self.day),ops.command(canonical,self.day))
    def test_fresh_matching_request_reused_across_models_and_ps(self):
        self.save('requests/201.json','shared',self.capture)
        with patch.object(transport,'requests',return_value=[(201,ops.command('RM6',self.day))]):
            for cmd in ['RM6','RM7','RM6PS','RM7PS','RMV6PS','RMV7PS']:
                response=client.handle(cmd,now=self.capture)
                self.assertEqual(response['request_id'],201);self.assertIn('ticket',response)
        self.enqueue.assert_not_called()
    def test_pending_matching_request_does_not_duplicate(self):
        with patch.object(transport,'requests',return_value=[(201,ops.command('RM6',self.day))]):
            response=client.handle('RM7PS',now=self.capture)
        self.assertEqual((response['request_id'],response['request_status']),(201,'QUEUED'))
        self.enqueue.assert_not_called()
    def test_expired_matching_request_queues_new_capture(self):
        self.save('requests/201.json','expired',self.capture)
        with patch.object(transport,'requests',return_value=[(201,ops.command('RM6',self.day))]):
            result=client.handle('RM7',now=self.capture+ops.timedelta(minutes=6))
        self.assertEqual(result['request_id'],200);self.enqueue.assert_called_once()
    def test_legacy_blocked_single_refreshes_under_new_hierarchy(self):
        self.save('requests/201.json','legacy',self.capture,status='PARTIAL_OR_BLOCKED')
        f=json.loads(self.files['legacy/forecast.json'])
        for result in f['races'][0]['models'].values():result.update(status='BLOCKED',ordered_selections=[])
        raw=json.dumps(f).encode();self.files['legacy/forecast.json']=raw
        from hashlib import sha256
        digest=sha256(raw).hexdigest();self.files['legacy/receipt.json']['forecast_sha256']=digest
        self.files['requests/201.json']['forecast_sha256']=digest
        with patch.object(transport,'requests',return_value=[(201,ops.command('RM6 Ballina 1',self.day))]):
            result=client.handle('RM7 Ballina 1',now=self.capture)
        self.assertEqual(result['request_id'],200);self.enqueue.assert_called_once()

    def test_single_race_and_country_are_not_daily_cache(self):
        self.save('requests/201.json','unrelated',self.capture)
        with patch.object(transport,'requests',return_value=[(201,ops.command('RM6',self.day,'NZ'))]):
            result=client.handle('RM7 Ballina 1',country='AU',now=self.capture)
        self.assertEqual(result['request_id'],200);self.enqueue.assert_called_once()
    def test_c_returns_completed_view_using_recorded_command(self):
        self.save('requests/201.json','complete',self.capture)
        self.files['requests/201.json']['request']=ops.command('RM7PS',self.day)
        result=client.handle('C',request_id=201,now=self.capture)
        self.assertEqual(result['view']['version'],'V7');self.assertIn('Leading Horse',result['ticket'])
        self.enqueue.assert_not_called()
    def test_c_latest_uses_issue_scope_without_inference(self):
        self.save('requests/201.json','complete',self.capture)
        with patch.object(transport,'requests',return_value=[(201,ops.command('RM6PS',self.day))]):
            result=client.handle('C',now=self.capture)
        self.assertEqual(result['view']['view'],'provisional');self.enqueue.assert_not_called()
    def test_c_retrieves_older_index_without_embedded_request(self):
        self.save('requests/201.json','complete',self.capture)
        with patch.object(transport,'requests',return_value=[(201,ops.command('RM7PS',self.day))]):
            result=client.handle('C',request_id=201,now=self.capture)
        self.assertEqual(result['view']['version'],'V7');self.enqueue.assert_not_called()
    def test_no_empty_ticket_for_wrong_track(self):
        self.save('requests/201.json','complete',self.capture)
        result=client.handle('RM7 Missing 5',request_id=201,now=self.capture)
        self.assertEqual(result['semantic_outcome'],'REQUEST_SCOPE_NOT_PRESENT');self.assertNotIn('ticket',result)


class AtomicPublicationTests(unittest.TestCase):
    def test_forecast_and_terminal_index_are_one_nonforce_commit(self):
        from operations.failure import failed
        calls=[]
        def api(endpoint,method='GET',body=None,optional=False):
            calls.append((endpoint,method,body))
            if endpoint=='git/ref/heads/'+transport.BRANCH:return {'object':{'sha':'parent'}}
            if endpoint=='git/commits/parent':return {'tree':{'sha':'base'}}
            if endpoint=='git/trees':return {'sha':'tree'}
            if endpoint=='git/commits':return {'sha':'commit'}
            return None
        with TemporaryDirectory() as d:
            failed(d,'unit-run','2026-11-23','controlled_test_failure')
            with patch.object(transport,'ensure_results_branch'),patch.object(transport,'api',side_effect=api):
                result=transport.publish(Path(d)/'public','unit-run','2026-11-23',200,'workflow',request=ops.command('RM6','2026-11-23'))
        tree=next(body for endpoint,method,body in calls if endpoint=='git/trees')
        paths={entry['path'] for entry in tree['tree']}
        self.assertIn('requests/200.json',paths);self.assertIn('runs/2026-11-23/unit-run/forecast.json',paths)
        self.assertIn('runs/2026-11-23/unit-run/receipt.json',paths)
        self.assertEqual(calls[-1],('git/refs/heads/'+transport.BRANCH,'PATCH',{'sha':'commit','force':False}))
        self.assertFalse(any(method=='PUT' for _,method,_ in calls));self.assertEqual(result['request_status'],'FAILED')
    def test_tampered_receipt_rejected_before_github(self):
        from operations.failure import failed
        with TemporaryDirectory() as d:
            failed(d,'unit-run','2026-11-23','controlled_test_failure')
            (Path(d)/'public/forecast.json').write_text('{}')
            with patch.object(transport,'api') as api:
                with self.assertRaises(ValueError):transport.publish(Path(d)/'public','unit-run','2026-11-23')
                api.assert_not_called()
    def test_existing_immutable_directory_is_never_replaced(self):
        from operations.failure import failed
        with TemporaryDirectory() as d:
            failed(d,'unit-run','2026-11-23','controlled_test_failure')
            with patch.object(transport,'ensure_results_branch'),patch.object(transport,'api',side_effect=[{'object':{'sha':'parent'}},{}]) as api:
                with self.assertRaisesRegex(ValueError,'Immutable'):transport.publish(Path(d)/'public','unit-run','2026-11-23')
            self.assertFalse(any(c.args[1:] for c in api.call_args_list))


class QueueRecoveryTests(unittest.TestCase):
    def test_event_worker_drains_other_pending_issues(self):
        req=ops.command('RM6','2026-11-23')
        order = []
        def backlog():
            order.append('scan')
            return [(123, req), (200, req), (201, req)]
        def operate(req, number, *args):
            order.append(number)
            return {}
        with (patch.dict(os.environ,dict(OPERATIONS_MODE='queue',OPERATIONS_ISSUE='200',GITHUB_RUN_ID='123')),
              patch.object(worker,'request_for_issue',return_value=req),
              patch.object(worker,'requests',side_effect=backlog),
              patch.object(worker,'read',return_value=None),patch.object(worker,'record_request'),
              patch.object(worker,'operate',side_effect=operate),patch('builtins.print')):
            worker.main()
        self.assertEqual(order,[200,'scan',123,201])

    def test_same_batch_model_commands_share_one_completed_execution(self):
        req=ops.command('RM6','2026-11-23');other=ops.command('RM7PS','2026-11-23')
        result=dict(request_status='COMPLETED',request_id=200,run_id='shared',forecast_path='shared/forecast.json')
        with (patch.dict(os.environ,dict(OPERATIONS_MODE='queue',OPERATIONS_ISSUE='200',GITHUB_RUN_ID='123')),
              patch.object(worker,'request_for_issue',return_value=req),
              patch.object(worker,'requests',return_value=[(200,req),(201,other)]),
              patch.object(worker,'read',return_value=None),patch.object(worker,'record_request') as record,
              patch.object(client,'retrieve',return_value={'source_mode':'LIVE','provider':'PuntersEdge','view':{}}),
              patch.object(worker,'operate',return_value=result) as operate,patch('builtins.print')):
            worker.main()
        operate.assert_called_once()
        reused=record.call_args.args[0]
        self.assertEqual(reused['request_id'],201);self.assertEqual(reused['reused_from_request'],200)
        self.assertEqual(reused['request']['command'],'RM7PS');self.assertEqual(reused['forecast_path'],'shared/forecast.json')


    def test_direct_lookup_failure_keeps_queue_discovery(self):
        from datetime import datetime
        req = ops.command('RM6', '2026-11-23')
        with (patch.object(worker, 'request_for_issue', side_effect=RuntimeError('transport failed')),
              patch.object(worker, 'requests', return_value=[(200, req)])):
            self.assertEqual(list(worker.work_items('queue', '200', datetime(2026, 11, 23), '1-1')),
                             [(200, req)])

    def test_terminal_event_does_not_rerun_and_still_drains_backlog(self):
        req = ops.command('RM6', '2026-11-23')
        with (patch.dict(os.environ, dict(OPERATIONS_MODE='queue', OPERATIONS_ISSUE='200', GITHUB_RUN_ID='123')),
              patch.object(worker, 'request_for_issue', return_value=req),
              patch.object(worker, 'requests', return_value=[(201, req)]),
              patch.object(worker, 'read', side_effect=[{'request_status':'COMPLETED'}, None]),
              patch.object(worker, 'record_request'),
              patch.object(worker, 'operate', return_value={}) as operate, patch('builtins.print')):
            worker.main()
        self.assertEqual([call.args[1] for call in operate.call_args_list], [201])

    def test_scheduled_worker_preserves_daily_catch_up_before_backlog(self):
        from datetime import datetime
        req = ops.command('RM6', '2026-11-23')
        with (patch.object(worker, 'read', return_value=None),
              patch.object(worker, 'requests', return_value=[(200, req)])):
            self.assertEqual(list(worker.work_items('queue', '', datetime(2026,11,23,8,15), '1-1')),
                             [(None, req), (200, req)])

    def test_direct_issue_reads_still_require_owner_and_strict_body(self):
        issue = dict(state='open', title='Monty command: RM6', user={'login':'Spankman'},
                     body='{}', created_at='2026-11-22T23:00:00Z')
        with patch.object(transport, 'api', return_value=issue) as api:
            self.assertEqual(transport.request_for_issue(200)['date'], '2026-11-23')
            api.assert_called_once_with('issues/200', optional=True)
        for change in ({'user':{'login':'someone'}}, {'body':'{"other":1}'}, {'state':'closed'}):
            with patch.object(transport, 'api', return_value=dict(issue, **change)):
                self.assertIsNone(transport.request_for_issue(200))


class ProviderRetryTests(unittest.TestCase):
    def test_transient_http_recovers_without_alternate_source(self):
        import krok_adapter as adapter
        with patch.object(adapter.urllib.request,'urlopen',side_effect=[HTTPError('https://example',503,'private',{},None),BytesIO(b'{}')]) as call,patch.object(adapter.time,'sleep') as sleep:
            self.assertEqual(adapter._fetch_body(object(),time.monotonic()+60),b'{}')
            self.assertEqual(call.call_count,2);sleep.assert_called_once_with(.5)
    def test_authentication_failure_not_retried(self):
        import krok_adapter as adapter
        with patch.object(adapter.urllib.request,'urlopen',side_effect=HTTPError('https://example',401,'private',{},None)) as call:
            with self.assertRaises(HTTPError):adapter._fetch_body(object(),time.monotonic()+60)
            self.assertEqual(call.call_count,1)
    def test_retry_after_not_shortened(self):
        import krok_adapter as adapter
        with patch.object(adapter.urllib.request,'urlopen',side_effect=HTTPError('https://example',429,'private',{'Retry-After':'90'},None)) as call,patch.object(adapter.time,'sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'retry exceeds'):adapter._fetch_body(object(),time.monotonic()+60)
            sleep.assert_not_called();self.assertEqual(call.call_count,1)
    def test_network_attempts_are_bounded(self):
        import krok_adapter as adapter
        with patch.object(adapter.urllib.request,'urlopen',side_effect=URLError('private')) as call,patch.object(adapter.time,'sleep'):
            with self.assertRaises(URLError):adapter._fetch_body(object(),time.monotonic()+60)
            self.assertEqual(call.call_count,3)

if __name__=='__main__':unittest.main()
