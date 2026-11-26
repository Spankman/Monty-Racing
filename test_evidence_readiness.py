"""Offline acquisition, crash and delivery contracts. No provider calls."""
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
import unittest,json,subprocess
from operations.evidence.store import Recorder,encoded,sha
from operations.evidence.interrupted import reconcile,recover_checkpoint
from operations.puntersedge_capture import Acquisition
from puntersedge_adapter import Client,ProviderError
import test_puntersedge_adapter as fixtures

class Readiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t=TemporaryDirectory();cls.cert=Path(cls.t.name)/'cert';cls.key=Path(cls.t.name)/'key'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-subj','/CN=synthetic-readiness','-keyout',str(cls.key),'-out',str(cls.cert),'-days','1'],check=True,capture_output=True)
    @classmethod
    def tearDownClass(cls):cls.t.cleanup()
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.at=datetime.now(timezone.utc)
        self.policy=dict(schema='monty.evidence-policy.v1',enabled=True,retention_days=1,max_bundle_bytes=1000000,sources={'PuntersEdge':dict(private_retention_permitted=True,permission_reference='Synthetic transport only',review_expires_at=(self.at+timedelta(days=2)).isoformat())})
    def recorder(self):return Recorder(self.root/'run','synthetic','PuntersEdge',self.policy,self.cert,clock=lambda:self.at)
    def race(self):
        f=fixtures.ProviderTests();f.setUp();return f.race
    def test_original_bytes_canonical_and_no_duplicate_requests(self):
        race=self.race();calls=[]
        def opener(*a,**k):calls.append(1);return fixtures.Response([race])
        client=Client('synthetic-key',opener=opener);r=self.recorder();source=Acquisition(client,day='2026-11-25',venue='Fixture',race_id='fixture')
        payload=source(r);r.snapshot(payload)
        self.assertEqual(len(calls),1);self.assertEqual(r.raw_count,1);self.assertEqual(json.loads((r.root/'raw-0000.json').read_text()),[race])
        self.assertEqual(payload['data'][0]['races'][0]['runners'][0]['odds'][0]['bookmaker'],'TAB')
        self.assertEqual(payload['data'][0]['races'][0]['runners'][0]['odds'][0]['captured_at'],race['runners'][0]['bookmakers'][0]['last_update'])
        with self.assertRaises(ProviderError):source(r)
        self.assertEqual(len(calls),1);self.assertIsNone(client.observer)
    def test_wrong_race_no_substitution_and_original_response_survives(self):
        r=self.recorder();client=Client('fixture',opener=lambda *a,**k:fixtures.Response([self.race()]))
        source=Acquisition(client,day='2026-11-25',venue='Fixture',race_id='not-present')
        with self.assertRaises(ProviderError):source(r)
        self.assertEqual(r.raw_count,1);self.assertEqual(reconcile(self.root)[0]['status'],'INTERRUPTED_INCOMPLETE_EVIDENCE')
    def test_disallowed_retention_keeps_no_original_bytes(self):
        self.policy['sources']['PuntersEdge']['private_retention_permitted']=False;r=self.recorder()
        source=Acquisition(Client('fixture',opener=lambda *a,**k:fixtures.Response([self.race()])),day='2026-11-25',venue='Fixture',race_id='fixture');source(r)
        self.assertFalse(r.enabled);self.assertFalse(r.root.exists());self.assertEqual(r.raw_count,0)
    def test_C_wrapper_never_acquires(self):
        from operations.puntersedge_capture import execute
        with self.assertRaises(ProviderError):execute(None,'2026-11-26',self.root/'run','unused',run_id='x',venue='Fixture',race_id='x',request={'command':'C'})
    def test_interrupt_recovery_is_bound_and_never_a_forecast(self):
        r=self.recorder();r.snapshot({'data':[]});r.checkpoint('provider_captured')
        result=reconcile(self.root)[0];self.assertEqual(result['status'],'INTERRUPTED_INCOMPLETE_EVIDENCE');self.assertFalse(result['selections_available']);self.assertFalse((self.root/'run/private').exists())
        receipt=self.root/'run/evidence-recovery.json';anchor=sha(receipt.read_bytes());base=self.root/'run/evidence-checkpoints'
        recovered=recover_checkpoint(base/'0000.cms',base/'0000.json',receipt,anchor,self.key,self.root/'recovered')
        self.assertEqual(recovered['status'],'INTERRUPTED_EVIDENCE_ONLY');self.assertFalse(recovered['selections_available'])
        before=receipt.read_bytes();self.assertEqual(reconcile(self.root)[0],result);self.assertEqual(receipt.read_bytes(),before)
        with self.assertRaises(ValueError):recover_checkpoint(base/'0000.cms',base/'0000.json',receipt,'0'*64,self.key,self.root/'bad')
    def test_interruption_without_checkpoint_is_honest_and_cleanup_runs(self):
        r=self.recorder();r.snapshot({'data':[]});result=reconcile(self.root)[0]
        self.assertEqual(result['status'],'INTERRUPTED_NO_RECOVERABLE_CHECKPOINT');self.assertFalse((self.root/'run/private').exists())
    def test_changed_checkpoint_not_claimed_recoverable(self):
        r=self.recorder();r.snapshot({'data':[]});r.checkpoint('provider_captured');p=self.root/'run/evidence-checkpoints/0000.cms';p.write_bytes(b'changed')
        self.assertEqual(reconcile(self.root)[0]['status'],'INTERRUPTED_NO_RECOVERABLE_CHECKPOINT')
    def test_checkpoint_failure_does_not_fail_inference_or_retry_provider(self):
        r=self.recorder();r.snapshot({'data':[]})
        with patch('operations.evidence.store.subprocess.run',side_effect=OSError('synthetic disk/crypto failure')):r.checkpoint('provider_captured')
        self.assertEqual(r.checkpoint_errors,['checkpoint_capture_failed']);index=r.seal(dict(run_id='synthetic',races=[]));self.assertEqual(index['status'],'SEALED_INCOMPLETE') # live original bytes absent
    def test_completed_receipt_preserved_by_reconciliation(self):
        r=self.recorder();r.snapshot({'data':[]});r.checkpoint('provider_captured');public=self.root/'run/public';public.mkdir();forecast=encoded({'synthetic':True});(public/'forecast.json').write_bytes(forecast)
        receipt=encoded(dict(run_id='synthetic',forecast_sha256=sha(forecast)));(public/'receipt.json').write_bytes(receipt)
        self.assertEqual(reconcile(self.root)[0]['status'],'COMPLETED_RECEIPT_PRESENT');self.assertEqual((public/'receipt.json').read_bytes(),receipt)
    def test_metadata_delivery_not_scope_missing_or_manual_prediction(self):
        from operations.client import retrieve
        import monty_operations as ops
        forecast=dict(run_id='x',status='COMPLETED_ASSESSMENTS',models={'V6':{'status':'SCORED'}},races=[],source_mode='LIVE',captured_at=self.at.isoformat(),valid_until=(self.at+timedelta(seconds=300)).isoformat(),delivery_visibility='PRIVATE_EVIDENCE_ONLY',privacy_notice='Synthetic privacy limitation')
        raw=encoded(forecast);receipt=dict(run_id='x',status=forecast['status'],forecast_sha256=sha(raw));index=dict(run_id='x',request_status='COMPLETED',status=forecast['status'],forecast_path='f',receipt_path='r',forecast_sha256=sha(raw))
        with patch('operations.client.transport.read_bytes',return_value=raw),patch('operations.client.transport.read',return_value=receipt):
            result=retrieve(index,1,ops.command('RM6 Fixture 1'),self.at)
        self.assertEqual(result['semantic_outcome'],'PRIVATE_DELIVERY_BLOCKED');self.assertEqual(result['model_execution_outcome'],'COMPLETED_ASSESSMENTS');self.assertNotIn('form_assessment_requests',result);self.assertNotIn('ticket',result)
    def test_expired_checkpoint_refused(self):
        r=self.recorder();r.snapshot({'data':[]});r.checkpoint('provider_captured');reconcile(self.root);base=self.root/'run/evidence-checkpoints';receipt=self.root/'run/evidence-recovery.json'
        with self.assertRaises(ValueError):recover_checkpoint(base/'0000.cms',base/'0000.json',receipt,sha(receipt.read_bytes()),self.key,self.root/'expired',clock=self.at+timedelta(days=2))

    def test_intent_collision_fails_closed_without_overwriting(self):
        first=self.recorder();before=(self.root/'run/evidence-intent.json').read_bytes();second=self.recorder()
        self.assertTrue(first.enabled);self.assertFalse(second.enabled)
        self.assertEqual((self.root/'run/evidence-intent.json').read_bytes(),before)

    def test_issue_delivery_explains_private_rights_blocker(self):
        from operations.issue_delivery import result_body
        import monty_operations as ops
        forecast=dict(schema=ops.SCHEMA,run_id='x',date='2026-11-26',status='COMPLETED_ASSESSMENTS',models={'V6':dict(status='SCORED',scored_races=1)},races=[],blockers=[],source_mode='LIVE',delivery_visibility='PRIVATE_EVIDENCE_ONLY',privacy_notice='Private access required')
        index=dict(request_status='COMPLETED',workflow_url='https://github.com/example',receipt_sha256='a'*64)
        text=result_body(ops.command('RM6 Fixture 1'),forecast,dict(forecast_sha256='b'*64),index)
        self.assertIn('PRIVATE DELIVERY BLOCKED',text);self.assertNotIn('No current Monty model selections',text)

if __name__=='__main__':unittest.main()
