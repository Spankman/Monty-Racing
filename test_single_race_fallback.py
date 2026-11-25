"""Controlled offline contracts; no fixture is a live form/model prediction."""
from datetime import timedelta
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import monty_operations as ops
from operations import client,transport
from operations.single_race import handoffs,quote_text
from operations.render import render
import test_monty_operations as original

class FallbackTests(unittest.TestCase):
    setUp=original.RunTests.setUp
    scorer=original.RunTests.scorer
    def single(self,**kwargs):
        opts=dict(payload=self.payload,captured=self.now,request=ops.command('RM6 Test 1',self.day),fixture=True,scorer=self.scorer)
        opts.update(kwargs)
        return ops.execute(self.day,self.root/'single',self.v7,run_id='single',**opts)
    def unattribute(self):
        for r in self.payload['data'][0]['races'][0]['runners']:
            r.update(fixed_win=r['odds'][0]['win'],odds=[])
    def view(self,f,version='V6',**kwargs):return ops.projection(f,dict(version=version,view='provisional'),**kwargs)
    def retrieve(self,f,now=None):
        p=self.root/'single/public';raw=(p/'forecast.json').read_bytes();receipt=json.loads((p/'receipt.json').read_text())
        index=dict(run_id='single',status=f['status'],forecast_path='forecast',receipt_path='receipt',forecast_sha256=ops.sha(p/'forecast.json'))
        with patch.object(transport,'read_bytes',return_value=raw),patch.object(transport,'read',return_value=receipt):
            return client.retrieve(index,100,ops.command('RM6 Test 1',self.day),now or self.now)

    def test_every_single_command_scores_restricted_class_while_daily_filters_it(self):
        from krok_adapter import IncompleteFields
        for name, race_class in [('RM6', 'Maiden'), ('RM7', '2YO'), ('RM6PS', 'Hurdle'), ('RM7PS', 'Steeplechase')]:
            with self.subTest(command=name):
                self.payload['data'][0]['races'][0]['class'] = race_class
                with self.assertRaises(IncompleteFields):
                    ops.normalized_snapshot(self.payload, self.day)
                request = ops.command(name + ' Test 1', self.day)
                f = ops.execute(self.day, self.root / name, self.v7, run_id=name, payload=self.payload,
                                captured=self.now, request=request, fixture=True, scorer=self.scorer)
                result = ops.projection(f, request)['races'][0]['result']
                self.assertEqual(result['status'], 'SCORED')
                self.assertTrue(result['ranked_runners'])
                self.assertEqual(result['official_classification'], 'DATA BLOCKED')

    def test_expired_single_preserves_only_verified_prejump_name_rankings_in_archive(self):
        f = self.single()
        result = self.retrieve(f, now=self.now + timedelta(minutes=6))
        self.assertNotIn('ticket', result)
        archived = result['archived_assessments'][0]
        self.assertEqual(set(archived['rankings'][0]), {'number', 'horse'})
        self.assertIn('HISTORICAL', archived['label'])

    def test_unrelated_duplicate_field_does_not_block_target(self):
        race = self.payload['data'][0]['races'][0]
        self.payload['data'][0]['races'].extend([dict(race, number=2), dict(race, number=2)])
        f = self.single()
        self.assertEqual(f['coverage']['provider_races'], 1)
        self.assertEqual(f['coverage']['scored_both'], 1)
    def test_complete_unattributed_quotes_score_both_provisionally(self):
        self.unattribute();f=self.single()
        for v in ['V6','V7']:
            r=f['races'][0]['models'][v]
            self.assertEqual((r['status'],r['assessment_level'],r['model_inference']),('SCORED','RESEARCH ONLY' if v=='V7' else 'PROVISIONAL',True))
            self.assertEqual(r['recommended_bet_type'],'NO BET');self.assertFalse(r['betting_authorised'])
            self.assertEqual(len(r['ranked_runners']),3);self.assertEqual(r['most_likely']['number'],'1')
            self.assertNotIn('TAB',r['bookmaker'])
        self.assertEqual(self.calls[0][1],self.calls[1][1])
    def test_partial_prices_request_form_without_imputation_or_fake_ranks(self):
        field=self.payload['data'][0]['races'][0]['runners'];field[1]['odds']=[]
        field[0].update(jockey='Actual supplied rider',trainer='Actual supplied trainer',api_key='DO_NOT_EXPORT',history=[{'private':'DO_NOT_EXPORT'}])
        f=self.single();self.assertFalse(self.calls)
        self.assertEqual(f['operational_outcome'], 'ODDS UNAVAILABLE')
        for v in ['V6','V7']:
            r=f['races'][0]['models'][v];self.assertFalse(r['model_inference']);self.assertEqual(r['ordered_selections'],[])
            packet=r['form_assessment_request'];self.assertIn('NOT A MONTY PREDICTION',packet['classification'])
            self.assertIsNone(packet['facts']['known_runners'][1]['odds'])
            self.assertEqual(packet['facts']['known_runners'][0]['jockey'],'Actual supplied rider')
            self.assertNotIn('DO_NOT_EXPORT',json.dumps(packet));self.assertNotIn('probability',json.dumps(packet))
        self.assertEqual(len(self.retrieve(f)['form_assessment_requests']),1)
    def test_no_prices_preserves_known_field_for_independent_research(self):
        for r in self.payload['data'][0]['races'][0]['runners']:r['odds']=[]
        f=self.single();self.assertFalse(self.calls)
        packet=f['races'][0]['models']['V7']['form_assessment_request']
        self.assertEqual(len(packet['facts']['known_runners']),3)
        self.assertTrue(all(r['odds'] is None for r in packet['facts']['known_runners']))
    def test_unknown_scratching_is_not_a_confirmed_active_field(self):
        self.payload['data'][0]['races'][0]['runners'][0].pop('is_scratched')
        f=self.single();self.assertFalse(self.calls)
        self.assertEqual(f['operational_outcome'], 'SCRATCHINGS UNVERIFIED')
        self.assertEqual(f['races'][0]['assessment_facts']['unknown_scratching_count'],1)
        self.assertFalse(f['races'][0]['models']['V6']['model_inference'])
    def test_duplicate_identity_never_scored(self):
        self.payload['data'][0]['races'][0]['runners'][1]['number']=1
        f=self.single();self.assertFalse(self.calls)
        self.assertTrue(f['races'][0]['assessment_facts']['field_identity_ambiguous'])
    def test_v6_two_runner_field_does_not_bypass_v7_minimum(self):
        self.payload['data'][0]['races'][0]['runners'].pop()
        def two(v,*args):
            rows=self.scorer(v,*args)
            for r,p in zip(rows,[.6,.4]):r['probability']=p
            return rows
        f=self.single(scorer=two);a=f['races'][0]['models']
        self.assertEqual(a['V6']['status'],'SCORED');self.assertEqual(a['V7']['status'],'BLOCKED')
        self.assertEqual(a['V7']['assessment_level'],'MODEL RANKINGS UNAVAILABLE')
        self.assertEqual([v for v,_ in self.calls],['V6'])
    def test_mixed_provenance_keeps_original_v7_contract(self):
        r=self.payload['data'][0]['races'][0]['runners'][0];r.update(odds=[],fixed_win=3)
        f=self.single();m=f['races'][0]['models']
        self.assertEqual(m['V6']['status'],'SCORED');self.assertEqual(m['V7']['status'],'BLOCKED')
        self.assertIn('V7_requires_consistent_price_provenance',m['V7']['no_bet_reasons'])
        self.assertFalse(m['V7']['model_inference'])
    def test_model_error_kept_visible_not_other_model_prediction(self):
        def broken(v,*args):
            if v=='V7':raise RuntimeError('DO_NOT_EXPORT')
            return self.scorer(v,*args)
        f=self.single(scorer=broken);m=f['races'][0]['models']
        self.assertEqual(m['V6']['status'],'SCORED');self.assertEqual(m['V7']['status'],'FAILED')
        self.assertEqual(m['V7']['form_assessment_request']['model_status'],'FAILED')
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(f));self.assertEqual(m['V7']['ordered_selections'],[])
    def test_unknown_jump_handoff_survives_without_claiming_fresh_prediction(self):
        self.payload['data'][0]['races'][0]['jump_time']=None
        f=self.single();self.assertFalse(self.calls)
        response=self.retrieve(f)
        self.assertEqual(response['freshness'],'UNVERIFIED');self.assertNotIn('ticket',response)
        self.assertEqual(response['form_assessment_requests'][0]['target']['meeting'],'Test')
    def test_closed_race_not_a_new_prejump_assessment(self):
        self.payload['data'][0]['races'][0]['jump_time']=(self.now-timedelta(minutes=1)).isoformat()
        f=self.single();self.assertFalse(self.calls);v=self.view(f,now=self.now)
        self.assertEqual(handoffs(v),[]);self.assertNotIn('Continue with current',ops.ticket(v,now=self.now))
    def test_provider_closed_status_no_form_handoff(self):
        self.payload['data'][0]['races'][0]['status']='resulted'
        f=self.single();self.assertFalse(self.calls)
        self.assertEqual(handoffs(self.view(f)),[])
    def test_operational_statuses_survive_verified_retrieval(self):
        meeting = self.payload['data'][0]
        race = meeting['races'][0]
        for i, (subject, status, expected) in enumerate([
            (meeting, 'abandoned', 'MEETING ABANDONED'),
            (race, 'abandoned', 'RACE ABANDONED'),
            (race, 'postponed', 'RACE POSTPONED'),
            (race, 'resulted', 'RACE ALREADY JUMPED'),
            (race, 'closed', 'DATA BLOCKED'),
        ]):
            with self.subTest(status=status):
                with patch.dict(subject, status=status):
                    out = self.root / str(i)
                    request = ops.command('RM6 Test 1', self.day)
                    f = ops.execute(self.day, out, self.v7, run_id=str(i), payload=self.payload,
                                    captured=self.now, request=request, fixture=True, scorer=self.scorer)
                public = out / 'public'
                raw = (public / 'forecast.json').read_bytes()
                receipt = json.loads((public / 'receipt.json').read_text())
                index = dict(run_id=str(i), status=f['status'], forecast_path='forecast',
                             receipt_path='receipt', forecast_sha256=ops.sha(public / 'forecast.json'))
                with patch.object(transport, 'read_bytes', return_value=raw), patch.object(transport, 'read', return_value=receipt):
                    response = client.retrieve(index, 100, request, self.now)
                self.assertEqual(response['semantic_outcome'], expected)
                self.assertEqual(response['operational_evidence'], 'KROK PROVIDER ASSERTION ONLY')
                self.assertNotIn('ticket', response)
                self.assertNotIn('form_assessment_requests', response)
        self.assertFalse(self.calls)

    def test_nz_meeting_outside_au_scope_is_not_an_engine_failure(self):
        self.payload['data'][0]['country'] = 'NZ'
        result = self.single(request=ops.command('RM6 Test 1', self.day, 'AU'))
        self.assertEqual(result['operational_outcome'], 'RACE NOT FOUND')
        self.assertEqual(result['operational_reason'], 'meeting_outside_requested_country')
        self.assertFalse(self.calls)

    def test_malformed_field_is_blocked_before_inference(self):
        self.payload['data'][0]['races'][0]['runners'].append(None)
        self.assertEqual(self.single()['operational_outcome'], 'FIELD UNAVAILABLE')
        self.assertFalse(self.calls)

    def test_official_and_expired_views_never_leak_new_rank_fields(self):
        f=self.single()
        for mode,now in [('official',self.now),('provisional',self.now+timedelta(minutes=6))]:
            v=ops.projection(f,dict(version='V6',view=mode),now)
            result=v['races'][0]['result']
            for key in ['ranked_runners','most_likely','value_selection']:self.assertNotIn(key,result)
            self.assertEqual(result['ordered_selections'],[])
    def test_best_probability_and_value_are_separate(self):
        def edge(v,*args):
            rows=self.scorer(v,*args)
            for r,p in zip(rows,[.4,.25,.35]):
                r.update(probability=p,research_category='RUFFY' if r['number']=='3' else 'NO BET')
            return rows
        f=self.single(scorer=edge);r=f['races'][0]['models']['V6']
        self.assertEqual(r['most_likely']['number'],'1');self.assertEqual(r['value_selection']['number'],'3')
        self.assertFalse(r['betting_authorised']);self.assertEqual(r['recommended_bet_type'],'NO BET')
    def test_frozen_integrity_failure_stays_failed_with_fact_free_research_target(self):
        from monty.integrity import ArtifactError
        with patch('monty.integrity.verify_artifacts',side_effect=ArtifactError('private diagnostic')):
            f=self.single()
        self.assertEqual(f['status'],'FAILED');self.assertFalse(self.calls)
        response=self.retrieve(f)
        self.assertEqual(response['request_status'],'FAILED')
        packet=response['form_assessment_requests'][0]
        self.assertEqual(packet['model_status'],'FAILED');self.assertIsNone(packet['facts'])
        self.assertEqual(packet['target']['race'],'1');self.assertNotIn('private diagnostic',json.dumps(response))

    def test_unpriced_independent_row_prints_unknown_without_fake_quote(self):
        f=self.single();v=self.view(f);r=v['races'][0]['result']
        r['ordered_selections'][0]['odds']=None;r['roughies']=[];r['value_selection']=None
        for text in [ops.ticket(v,archived=True),render(v,archived=True)]:
            self.assertIn('ODDS UNAVAILABLE',text);self.assertNotIn('$0.00',text)
        self.assertEqual(quote_text({'odds':float('nan')}),'ODDS UNAVAILABLE')

if __name__=='__main__':unittest.main()
