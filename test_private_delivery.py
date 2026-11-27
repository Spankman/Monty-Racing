"""Synthetic private transport contracts, not live acceptance."""
from datetime import datetime,timedelta,timezone
import json,unittest
from unittest.mock import patch
from monty_operations import selection
from operations.private_delivery import bundle,publish,PrivateDeliveryError,sha,Sink

class PrivateDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,27,3,tzinfo=timezone.utc)
        rows=[dict(number=str(n),horse='Synthetic '+str(n),odds=float(n+3),probability=p,bookmaker='TAB') for n,p in [(1,.5),(2,.3),(3,.2)]]
        model=dict(selection(rows,'V6'),status='SCORED',no_bet_reasons=['historical evidence missing'],betting_decision='DATA BLOCKED',prediction_classification='PROVISIONAL',model_version='V6',score_trace={'private_raw_feature':'MUST_NOT_PUBLISH'})
        self.f=dict(schema='fixture',date='2026-11-27',run_id='fixture-1',provider='PuntersEdge',source_mode='LIVE',status='COMPLETED_ASSESSMENTS',models={},blockers=[],captured_at=self.now.isoformat(),valid_until=(self.now+timedelta(seconds=300)).isoformat(),
            races=[dict(meeting='Synthetic',race='1',country='AU',captured_at=self.now.isoformat(),scheduled_start=(self.now+timedelta(hours=1)).isoformat(),models={'V6':model,'V7':dict(model,model_version='V7',prediction_classification='RESEARCH ONLY')})])
    def test_private_bundle_receipt_binds_exact_views_and_excludes_raw_features(self):
        self.f['races'][0]['models']['V6']['ranked_runners'][0]['score_trace']={'raw_feature':'MUST_NOT_PUBLISH_ROW'}
        files,index=bundle(self.f,self.now)
        receipt=json.loads(files[index['receipt_path']])
        self.assertEqual(sha(files[index['receipt_path']]),index['receipt_sha256'])
        for name,digest in receipt['files'].items():self.assertEqual(sha(files['runs/2026-11-27/fixture-1/'+name]),digest)
        self.assertNotIn('MUST_NOT_PUBLISH',files[index['forecast_path']].decode())
        self.assertIn('PROVISIONAL',files[index['tickets']['v6-provisional.txt']].decode())
    def test_expired_bundle_never_renders_current_runner_prices(self):
        files,index=bundle(self.f,self.now+timedelta(seconds=301))
        self.assertNotIn('Synthetic 1',files[index['tickets']['v6-provisional.txt']].decode())
        self.assertNotIn('Synthetic 1',files[index['tickets']['combined-assessments.txt']].decode())
    def test_retried_identical_publish_does_not_rewrite(self):
        files,index=bundle(self.f,self.now)
        sink=unittest.mock.Mock();sink.read.return_value=files[index['receipt_path']]
        self.assertEqual(publish(self.f,sink=sink,now=self.now+timedelta(seconds=1)),index);sink.commit.assert_not_called()
        sink.read.return_value=b'conflicting'
        with self.assertRaisesRegex(PrivateDeliveryError,'conflict'):publish(self.f,sink=sink,now=self.now)
    def test_public_sink_rejected_before_any_mutation(self):
        sink=Sink('synthetic-not-secret')
        with patch.object(sink,'api',return_value={'private':False}) as api:
            with self.assertRaisesRegex(PrivateDeliveryError,'private_repository'):sink.commit({'x':b'fixture'})
        self.assertEqual(api.call_count,1)
    def test_foreign_source_rejected(self):
        with self.assertRaises(PrivateDeliveryError):bundle(dict(self.f,provider='Krok'),self.now)
    def test_combined_does_not_duplicate_same_engine_race(self):
        from operations.combined import combined_ticket
        view=combined_ticket(self.f,self.now)
        self.assertEqual(len(view['races']),1)
        numbers=[r['number'] for r in view['races'][0]['result']['ordered_selections']+view['races'][0]['result']['roughies']]
        self.assertEqual(len(numbers),len(set(numbers)))

import test_monty_operations as fixtures
class PrivateClientTests(unittest.TestCase):
    setUp=fixtures.ConnectorClientTests.setUp
    save=fixtures.ConnectorClientTests.save
    def make_private(self):
        import hashlib
        self.save('requests/200.json','private',self.capture)
        f=json.loads(self.files['private/forecast.json']);f['races']=[]
        f.update(delivery_visibility='PRIVATE_RESULTS_AVAILABLE',private_delivery=dict(repository='Spankman/Monty-Private-Archive',ref='monty-operational-private-results',receipt_path='private/receipt.json',receipt_sha256='a'*64,
            race_validity=[dict(meeting='Ballina',race='1',country='AU',captured_at=(self.capture-timedelta(seconds=240)).isoformat(),valid_until=(self.capture+timedelta(seconds=60)).isoformat())]))
        raw=json.dumps(f).encode();digest=hashlib.sha256(raw).hexdigest()
        self.files['private/forecast.json']=raw;self.files['private/receipt.json']['forecast_sha256']=digest
        self.files['requests/200.json']['forecast_sha256']=digest
    def test_C_reads_private_pointer_without_starting_anything(self):
        self.make_private()
        result=self.client.handle('C',request_id=200,now=self.capture+timedelta(seconds=30))
        self.assertEqual(result['delivery_status'],'PRIVATE_RESULTS_AVAILABLE')
        self.assertEqual(result['fresh_race_assessments'],1);self.enqueue.assert_not_called()
        self.assertNotIn('ticket',result)
    def test_offer_expiry_wins_over_recent_acquisition(self):
        self.make_private()
        result=self.client.handle('C',request_id=200,now=self.capture+timedelta(seconds=61))
        self.assertEqual(result['delivery_status'],'PRIVATE_RESULTS_EXPIRED')
        self.assertFalse(result['selections_available']);self.enqueue.assert_not_called()
