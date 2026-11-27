import json,tempfile,unittest,subprocess
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
from operations.trial.program import preregister,validate_plan,windows,digest,seal,protocol
from operations.trial.run import exact_target,reconcile_authority
from operations.trial import control

class Trial(unittest.TestCase):
    def card(self,venue='Rockhampton',race=4,jump='2026-11-26T03:00:00Z'):
        return dict(race_id=venue+str(race),venue=venue,race_number=race,start_time=jump,country='AU',category='horse',race_class='BM64 Handicap')
    def test_geography_and_before_first_observation(self):
        at=datetime(2026,11,25,20,tzinfo=timezone.utc)
        plan=preregister([self.card(),self.card('Hawkesbury',3,'2026-11-26T03:05:00Z'),self.card('Geraldton',5,'2026-11-26T04:10:00Z')],'2026-11-26',at)
        self.assertEqual(len(plan['races']),3);self.assertEqual(plan['status'],'PREREGISTERED')
        self.assertEqual({r['state'] for r in plan['races']},{'QLD','NSW','WA'})
        self.assertEqual(len(windows(plan)),12);self.assertLess(at,windows(plan)[0][0])
    def test_no_outcome_or_odds_selection(self):
        at=datetime(2026,11,25,20,tzinfo=timezone.utc)
        r=self.card();a=preregister([r],'2026-11-26',at)
        r.update(runners=[dict(win_price=900,model_rank=1)],winner=99)
        self.assertEqual(preregister([r],'2026-11-26',at),a)
    def test_no_late_or_unknown_or_maiden_entries(self):
        at=datetime(2026,11,26,2,tzinfo=timezone.utc)
        r=self.card();self.assertEqual(preregister([r],'2026-11-26',at)['races'],[])
        r=self.card('Unknown');self.assertEqual(preregister([r],'2026-11-26',at-timedelta(hours=4))['races'],[])
        r=self.card();r['race_class']='Maiden';self.assertEqual(preregister([r],'2026-11-26',at-timedelta(hours=4))['races'],[])
    def test_tamper_and_duplicate_rejected(self):
        plan=preregister([self.card()],'2026-11-26',datetime(2026,11,25,20,tzinfo=timezone.utc))
        plan['races'][0]['race_number']=7
        with self.assertRaises(ValueError):validate_plan(plan)
        plan=preregister([self.card()],'2026-11-26',datetime(2026,11,25,20,tzinfo=timezone.utc));plan['races']*=2
        plan.pop('plan_sha256');plan['plan_sha256']=digest(plan)
        with self.assertRaises(ValueError):validate_plan(plan)
    def test_rescheduled_race_rejected(self):
        race=self.card();self.assertEqual(exact_target([race],race),race)
        changed=dict(race,start_time='2026-11-26T03:01:00Z')
        with self.assertRaises(Exception):exact_target([changed],race)
    def test_duplicate_launch_is_read_only(self):
        with patch.object(control,'current',return_value={'request_id':'already'}),patch.object(control,'atomic') as mutate:
            self.assertEqual(control.launch('2026-11-26','capture')['status'],'ALREADY_LAUNCHED');mutate.assert_not_called()
    def test_readonly_C_cannot_launch(self):
        with self.assertRaises(ValueError):control.launch('2026-11-26','C')
    def test_authenticated_encryption_and_no_plaintext_archive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);folder=p/'private';folder.mkdir();(folder/'sample').write_text('private licensed payload')
            subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-subj','/CN=test','-keyout',str(p/'key'),'-out',str(p/'cert'),'-days','1'],capture_output=True,check=True)
            import operations.trial.program as program
            with patch.object(program,'HERE',p):
                (p/'recipient-public.pem').write_bytes((p/'cert').read_bytes());seal(folder,p/'sealed.cms')
            self.assertFalse((p/'sealed.cms.plaintext.zip').exists());self.assertNotIn(b'private licensed payload',(p/'sealed.cms').read_bytes())
            decrypted=subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-in',str(p/'sealed.cms'),'-inkey',str(p/'key')],capture_output=True,check=True).stdout
            import io,zipfile
            self.assertEqual(zipfile.ZipFile(io.BytesIO(decrypted)).read('sample'),b'private licensed payload')
    def test_no_name_only_authority_match(self):
        evidence=dict(verified=True,facts=dict(distance_m=1200,runners=[dict(number='1',horse='A',scratched=False)]))
        target=dict(distance_m=1200,runners=[dict(number=2,name='A')])
        self.assertFalse(reconcile_authority(evidence,target))
    def test_trial_finite_budget_and_original_freshness(self):
        import monty_operations as ops
        self.assertEqual(ops.MAX_AGE_SECONDS,300);p=protocol();self.assertEqual(len(p['dates']),6)
        self.assertLessEqual(sum(p[k] for k in ('daily_plan_credit_cap','daily_capture_credit_cap','daily_results_credit_cap'))*6,400)
        self.assertEqual(p['capture_minutes'],[60,15,5,2])
    def test_late_capture_never_calls_provider_or_inference(self):
        import operations.trial.run as runner
        at=datetime(2026,11,25,20,tzinfo=timezone.utc)
        plan=preregister([self.card()],'2026-11-26',at)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'plan.json';path.write_text(json.dumps(plan))
            with patch.object(runner,'ROOT',root/'output'),patch.object(runner,'now',return_value=windows(plan)[0][0]+timedelta(seconds=31)),patch.object(runner,'Client') as client,patch.dict('os.environ',{'GITHUB_RUN_ID':'offline-test','GITHUB_SHA':'fixture'}):
                outcome=runner.point('2026-11-26',0,path)
            self.assertEqual(outcome['status'],'MISSED_WINDOW');client.assert_not_called()
    def test_market_incompleteness_and_underround_are_not_value(self):
        from operations.trial.run import market_summaries
        at=datetime(2026,11,26,2,tzinfo=timezone.utc)
        values={('1','a','tab'):dict(price=4,clocks=dict(observation_at=at.isoformat()))}
        audit=market_summaries(values,[['1','a'],['2','b']],at,'PUNTERSEDGE')['tab']
        self.assertIsNone(audit['book_percentage']);self.assertIn('incomplete_active_price_vector',audit['warnings'])
        self.assertNotIn('market_only_baseline',audit)
        values[('2','b','tab')]=dict(price=4,clocks=dict(observation_at=at.isoformat()))
        audit=market_summaries(values,[['1','a'],['2','b']],at,'PUNTERSEDGE')['tab']
        self.assertEqual(audit['book_percentage'],50);self.assertEqual(audit['underround_percentage_points'],50)
        self.assertFalse(audit['actionable_value_allowed'])
    def test_history_never_activates_future_or_same_day_rows(self):
        from operations.trial.run import history_inventory
        form=dict(form_as_at='2026-11-26T10:00:00Z',runners=[dict(runs=[dict(date='2026-11-25'),dict(date='2026-11-26'),dict(date='unknown')])])
        out=history_inventory(form,datetime(2026,11,26,2,tzinfo=timezone.utc))
        self.assertEqual(out['candidate_strictly_prior_day_rows'],1);self.assertEqual(out['excluded_same_day_future_or_invalid_rows'],2)
        self.assertTrue(out['declared_form_as_at_after_capture']);self.assertFalse(out['feature_activation'])
    def test_network_failure_is_not_missing_launch(self):
        with patch.object(control,'api',side_effect=RuntimeError('transport')):
            with self.assertRaises(RuntimeError):control.current('missing')
    def test_recovery_rejects_tampered_or_unsafe_archive(self):
        from operations.trial.recover import safe_zip,recover
        import io,zipfile,hashlib
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr('../escape','bad')
        with self.assertRaises(ValueError):safe_zip(raw.getvalue())
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'artifact.zip';path.write_bytes(raw.getvalue())
            with self.assertRaises(ValueError):recover(path,'0'*64,Path(d)/'key',Path(d)/'out')
            self.assertFalse((Path(d)/'out').exists())
    def test_declared_missing_runner_is_reported(self):
        from operations.trial.run import acceptance_inventory
        target=dict(race_id='registered',venue='Rockhampton',race_number=2,start_time='2026-11-26T04:20:00Z',runners=[dict(number=1,name='A')],scratchings=[])
        declaration=dict(date='2026-11-26',as_of='2026-11-26T03:00:00Z',meetings=[dict(venue='Rockhampton',races=[dict(race_id='registered',race_number=2,runners=[dict(number=1,runner_name='A',scratched=False),dict(number=2,runner_name='B',scratched=False)])])])
        audit=acceptance_inventory(declaration,target,datetime(2026,11,26,3,20,tzinfo=timezone.utc))
        self.assertFalse(audit['reconciled']);self.assertEqual(audit['missing_live_declarations'],1);self.assertFalse(audit['independent'])
if __name__=='__main__':unittest.main()
