"""Synthetic engineering fixtures; never live provider acceptance."""
from datetime import datetime,timezone,timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,subprocess,unittest
from operations.evidence.store import Recorder,encoded,sha,no_secrets,declaration_audit
from operations.evidence.verify import open_bundle,expired_bundles

class Retention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=TemporaryDirectory();cls.certroot=Path(cls.tmp.name)
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-subj','/CN=offline-test','-keyout',str(cls.certroot/'key'),'-out',str(cls.certroot/'cert'),'-days','1'],capture_output=True,check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.tmpcase=TemporaryDirectory();self.root=Path(self.tmpcase.name);self.addCleanup(self.tmpcase.cleanup)
        self.at=datetime(2026,11,26,1,tzinfo=timezone.utc)
        self.policy=dict(schema='monty.evidence-policy.v1',enabled=True,retention_days=2,max_bundle_bytes=10000000,sources={'SIMULATED FIXTURE':dict(private_retention_permitted=True,permission_reference='Synthetic test, no provider data',review_expires_at='2027-01-01T00:00:00Z')})
    def recorder(self,source='SIMULATED FIXTURE'):
        return Recorder(self.root/'run','test-run',source,self.policy,self.certroot/'cert',clock=lambda:self.at)
    def seal(self,raw=True):
        r=self.recorder();payload=dict(success=True,data=[]);r.snapshot(payload)
        if raw:r.raw(encoded(payload),'/api/v1/racing/meetings')
        prediction=dict(run_id='test-run',races=[],provider_snapshot_sha256=sha(encoded(payload)))
        index=r.seal(prediction);forecast=dict(prediction,evidence=index);fb=encoded(forecast)
        receipt=dict(run_id='test-run',forecast_sha256=sha(fb),evidence=index)
        (self.root/'forecast.json').write_bytes(fb);(self.root/'receipt.json').write_bytes(encoded(receipt))
        return r,index,sha(encoded(receipt))
    def open(self,anchor,output=None):
        return open_bundle(self.root/'run/evidence-sealed/evidence.cms',self.certroot/'key',self.root/'receipt.json',self.root/'forecast.json',anchor,output or self.root/'recovered',clock=self.at)
    def test_roundtrip_integrity_and_append_only(self):
        r,index,anchor=self.seal();self.assertTrue(index['complete']);result=self.open(anchor);self.assertGreater(result['verified_files'],0)
        cipher=self.root/'run/evidence-sealed/evidence.cms';before=cipher.read_bytes();self.assertEqual(r.seal(dict(run_id='test-run',races=[]))['status'],'RETENTION_FAILED');self.assertEqual(cipher.read_bytes(),before)
        self.assertFalse(any(self.root.rglob('plain.zip')))
    def test_bad_receipt_cipher_forecast_or_key_rejected(self):
        r,index,anchor=self.seal()
        with self.assertRaises(ValueError):self.open('0'*64)
        path=self.root/'forecast.json';old=path.read_bytes();path.write_bytes(old+b' ')
        with self.assertRaises(ValueError):self.open(anchor)
        path.write_bytes(old);cipher=self.root/'run/evidence-sealed/evidence.cms';cipher.write_bytes(cipher.read_bytes()[:-1]+b'x')
        with self.assertRaises(ValueError):self.open(anchor)
    def test_missing_licence_no_plaintext_or_archive(self):
        r=self.recorder('Krok');r.snapshot({'data':['private']});self.assertFalse(r.enabled);self.assertEqual(r.seal({})['status'],'POLICY_OR_KEY_CONFIGURATION_BLOCKED');self.assertFalse((self.root/'run/private').exists())
    def test_expired_policy_and_bad_retention_block(self):
        self.policy['retention_days']=90;self.assertFalse(self.recorder().enabled)
        self.policy['retention_days']=2;self.policy['sources']['SIMULATED FIXTURE']['review_expires_at']='2020-01-01T00:00:00Z';self.assertFalse(self.recorder().enabled)
    def test_credentials_never_persisted_and_incomplete_is_explicit(self):
        r=self.recorder();r.raw(encoded({'api_key':'SYNTHETIC_SECRET_NOT_REAL'}),'/api/v1/racing/meetings');r.snapshot({'data':[]})
        index=r.seal(dict(run_id='x',races=[]));self.assertFalse(index['complete']);self.assertEqual(index['status'],'SEALED_INCOMPLETE')
        self.assertFalse(any('SYNTHETIC_SECRET_NOT_REAL' in p.read_text(errors='ignore') for p in (self.root/'run/private').rglob('*') if p.is_file()))
    def test_non_inference_account_responses_not_retained(self):
        r=self.recorder();r.raw(encoded({'email':'private@example.invalid'}),'/v1/usage');self.assertEqual(r.raw_count,0);self.assertFalse(r.root.exists())
    def test_missing_http_for_live_data_does_not_claim_complete(self):
        self.policy['sources']['Krok']=dict(self.policy['sources']['SIMULATED FIXTURE']);r=self.recorder('Krok');r.snapshot({'data':[]})
        index=r.seal(dict(run_id='x',races=[]));self.assertFalse(index['complete']);self.assertIn('original_http_bytes_not_supplied',index['errors'])
    def test_scored_without_feature_audit_is_incomplete(self):
        r=self.recorder();r.snapshot({'data':[]});index=r.seal(dict(run_id='x',races=[dict(meeting='Test',race='1',captured_at=self.at.isoformat(),models={'V6':dict(status='SCORED')})]));self.assertFalse(index['complete'])
    def test_retention_expiry_and_dry_run_purge(self):
        r,index,anchor=self.seal();future=self.at+timedelta(days=3)
        with self.assertRaises(ValueError):open_bundle(self.root/'run/evidence-sealed/evidence.cms',self.certroot/'key',self.root/'receipt.json',self.root/'forecast.json',anchor,self.root/'expired',clock=future)
        self.assertEqual(len(expired_bundles(self.root,future)),1);self.assertTrue((self.root/'run/evidence-sealed/evidence.cms').exists())
        expired_bundles(self.root,future,apply=True);self.assertFalse((self.root/'run/evidence-sealed/evidence.cms').exists());self.assertTrue((self.root/'receipt.json').exists())
    def test_declared_scratched_and_unscored_not_invented_predictions(self):
        source=dict(data=[dict(venue='T',races=[dict(number=1,runners=[dict(number=7,name='Synthetic SCR',is_scratched=True)])])])
        a=declaration_audit(source,{'races':[]});self.assertEqual(len(a['declared']),1);self.assertTrue(a['declared'][0]['source_scratched']);self.assertIsNone(a['declared'][0]['models']['V6']['probability'])
    def test_unknown_ruffie_states_are_distinct(self):
        from operations.ruffies import audit
        race=dict(meeting='T',race='1',captured_at=self.at.isoformat(),scheduled_start=(self.at+timedelta(minutes=20)).isoformat(),data_completeness={'active_runners':2})
        self.assertEqual(audit(race,{'status':'BLOCKED'},'V6',self.at)['assessment_state'],'INSUFFICIENT DATA TO ASSESS RUFFIES')
        from test_ruffies import Ruffies
        f=Ruffies();f.setUp();m=f.model
        self.assertEqual(audit(f.race,m,'V6',f.now)['assessment_state'],'RESEARCH RUFFIES IDENTIFIED — NOT APPROVED')
        for row in m['ranked_runners']:row['bookmaker']=None
        self.assertEqual(audit(f.race,m,'V6',f.now)['assessment_state'],'UNVERIFIED OR ANOMALOUS MARKET CONDITIONS')
    def test_failed_observer_does_not_retry_or_spend_more(self):
        from puntersedge_adapter import Client
        class Response:
            headers={};status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'{"data":[]}'
        calls=[]
        def opener(*args,**kwargs):calls.append(1);return Response()
        def failed(*args):raise OSError('synthetic disk failure')
        c=Client(key='SYNTHETIC_TEST_KEY',opener=opener,observer=failed);c.get('/v1/racing/events');self.assertEqual(len(calls),1);self.assertEqual(c.reserved,1);self.assertEqual(c.observer_errors,['raw_observer_failed'])

    def test_restricted_live_rows_never_enter_public_delivery(self):
        from operations.evidence.store import public_result
        r=self.recorder('Krok')
        prediction=dict(run_id='x',source_mode='LIVE',status='COMPLETED_ASSESSMENTS',models={'V6':{'status':'SCORED'}},races=[dict(horse='RESTRICTED SYNTHETIC',odds=99)])
        public=public_result(prediction,{'status':'NOT_CONFIGURED'},r)
        self.assertNotIn('RESTRICTED SYNTHETIC',str(public));self.assertEqual(public['races'],[])
        self.assertEqual(public['status'],'COMPLETED_ASSESSMENTS');self.assertIn('not a predictive NO BET',public['privacy_notice'])
    def test_private_permission_does_not_grant_public_display(self):
        from operations.evidence.store import public_result
        self.policy['sources']['Krok']=dict(self.policy['sources']['SIMULATED FIXTURE']);r=self.recorder('Krok')
        p=dict(source_mode='LIVE',races=[{'private':'price'}]);self.assertEqual(public_result(p,{},r)['races'],[])
        self.policy['sources']['Krok'].update(public_derived_forecasts_permitted=True,public_display_permission_reference='Synthetic fixture permission only')
        r=Recorder(self.root/'separate-permitted-run','test-run-2','Krok',self.policy,self.certroot/'cert',clock=lambda:self.at);self.assertEqual(public_result(p,{},r)['races'],p['races'])
    def test_all_four_ruffie_reporting_states(self):
        from operations.ruffies import audit
        from test_ruffies import Ruffies
        f=Ruffies();f.setUp();m=f.model
        for row in m['ranked_runners']:row['odds']=2
        self.assertEqual(audit(f.race,m,'V6',f.now)['assessment_state'],'NO RUFFIES IDENTIFIED')
        f.setUp();m=f.model;row=next(r for r in m['ranked_runners'] if r['number']=='4');row.update(odds=30,probability=.05);m['ranked_runners'][0]['probability']+=.09
        self.assertEqual(audit(f.race,m,'V7',f.now)['assessment_state'],'RUFFIES IDENTIFIED BUT EXCLUDED')
    def test_replay_checks_frozen_weights_preprocessing_and_probabilities(self):
        import io,numpy as np
        from operations.evidence.verify import replay_arrays
        model=dict(input_feature_names=['foo'],numeric_feature_names=['foo','foo_missing'],imputation_medians=[0],mean=[0,0],scale=[1,1],selected='linear',models={'linear':{'weights':[1,0]}})
        raw_model=encoded(model);terms=np.array([[0.,0.],[1.,0.]]);weights=np.array([1.,0.]);scores=np.array([0.,1.]);prob=np.exp(scores);prob/=prob.sum()
        def make(bad=False):
            b=io.BytesIO();np.savez(b,transformed_terms=terms,term_weights=weights,term_contributions=terms*weights,feature_correction=scores,market_probability=np.array([.5,.5]),temperature=np.array(1),reported_probability=prob,fully_cancelled_terms=np.array([False,True]),feature_names=np.array(['foo']),term_names=np.array(['foo','foo_missing']),original_values=np.array([[0.],[1.]]),observed=np.ones((2,1),bool),missing_indicators=np.zeros((2,1),bool),imputed_values=np.array([[0.],[99. if bad else 1.]]));return b.getvalue()
        self.assertLess(replay_arrays(make(),raw_model,'V6',sha(raw_model))['maximum_probability_difference'],1e-12)
        with self.assertRaises(ValueError):replay_arrays(make(True),raw_model,'V6',sha(raw_model))
        with self.assertRaises(ValueError):replay_arrays(make(),raw_model,'V6','0'*64)
    def test_known_environment_credential_and_zip_traversal_rejected(self):
        from operations.evidence.verify import safe_archive
        import io,zipfile
        with patch.dict('os.environ',{'KROK_API_KEY':'SYNTHETIC_TEST_CREDENTIAL_LONG_VALUE'}):
            with self.assertRaises(ValueError):no_secrets({'unusual':'SYNTHETIC_TEST_CREDENTIAL_LONG_VALUE'})
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('../escape','bad')
        with self.assertRaises(ValueError):safe_archive(b.getvalue())
if __name__=='__main__':unittest.main()
