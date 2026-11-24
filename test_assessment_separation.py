"""Contract fixtures are simulated; separate live receipts are required."""
from datetime import timedelta
import json
import unittest
from operations.assessment import OutputContractError, feature_evidence, validate_output
from operations.render import render
import monty_operations as ops
import test_monty_operations as fixtures


class AssessmentTests(unittest.TestCase):
    setUp=fixtures.RunTests.setUp
    scorer=fixtures.RunTests.scorer
    run_it=fixtures.RunTests.run_it

    def test_unverified_success_is_not_a_value_based_no_bet(self):
        f=self.run_it()
        self.assertEqual(f['status'],'COMPLETED_ASSESSMENTS')
        for v,classification in [('V6','PROVISIONAL'),('V7','RESEARCH ONLY')]:
            m=f['races'][0]['models'][v]
            self.assertEqual(m['prediction_classification'],classification)
            self.assertEqual(m['betting_decision'],'DATA BLOCKED')
            self.assertTrue(m['model_inference']);self.assertFalse(m['betting_authorised'])
            self.assertEqual(len(m['ranked_runners']),3)
            self.assertAlmostEqual(sum(r['probability'] for r in m['ranked_runners']),1)
            self.assertFalse(m['value_evidence']['calibration_verified'])

    def test_standard_diagnostics_survive_repeated_render_but_not_expiry(self):
        f=self.run_it();view=ops.projection(f,ops.command('RM6',self.day),self.now)
        m=view['races'][0]['result']
        self.assertEqual(m['ordered_selections'],[])
        self.assertTrue(m['diagnostic_assessment']['ordered_selections'])
        for current in [view,ops.refresh_view(view,self.now),ops.refresh_view(ops.refresh_view(view,self.now),self.now)]:
            text=ops.ticket(current,now=self.now)
            self.assertIn('DIAGNOSTIC PROVISIONAL',text)
            self.assertIn('Horse 1',text)
            self.assertIn('DIAGNOSTIC PROVISIONAL',render(current,now=self.now))
        for mode in ['official','provisional','shadow']:
            expired=ops.projection(f,dict(version='V6',view=mode),self.now+timedelta(minutes=6))['races'][0]['result']
            self.assertNotIn('diagnostic_assessment',expired)
            self.assertFalse(expired['ordered_selections']);self.assertNotIn('ranked_runners',expired)

    def test_all_primary_and_single_commands_keep_explicit_ps_intent(self):
        f=self.run_it()
        for name in ['RM6','RM7','RM6PS','RM7PS','RMV6PS','RMV7PS']:
            req=ops.command(name,self.day)
            self.assertEqual(req['provisional_requested'],name.endswith('PS'))
            view=ops.projection(f,req,self.now)
            self.assertEqual(view['races'][0]['result']['status'],'SCORED')
            for suffix in [' Test 1',' Test R1']:
                single=ops.command(name+suffix,self.day)
                self.assertEqual(single['provisional_requested'],name.endswith('PS'))
                self.assertEqual(single['view'],'provisional') # automatic fallback preserved

    def test_execution_failure_cannot_be_reported_as_model_no_bet(self):
        def broken(version,*args):
            if version=='V7':raise RuntimeError('private traceback never public')
            return self.scorer(version,*args)
        f=self.run_it(scorer=broken)
        self.assertEqual(f['races'][0]['models']['V7']['prediction_classification'],'EXECUTION FAILED')
        self.assertEqual(f['races'][0]['models']['V6']['prediction_classification'],'PROVISIONAL')
        self.assertNotIn('private traceback',json.dumps(f))

    def test_actual_contract_failure_has_safe_specific_cause(self):
        def wrong(version,*args):
            rows=self.scorer(version,*args);rows[0]['odds']=999;return rows
        f=self.run_it(scorer=wrong)
        self.assertEqual(f['races'][0]['models']['V6']['no_bet_reasons'],['model_output_price_mismatch'])

    def test_v7_minimum_does_not_block_valid_two_runner_v6(self):
        self.payload['data'][0]['races'][0]['runners'].pop()
        def two(v,*args):
            rows=self.scorer(v,*args)
            for r,p in zip(rows,[.6,.4]):r['probability']=p
            return rows
        f=self.run_it(scorer=two)
        self.assertEqual([v for v,_ in self.calls],['V6'])
        self.assertEqual(f['races'][0]['models']['V6']['status'],'SCORED')
        self.assertEqual(f['races'][0]['models']['V7']['prediction_classification'],'DATA BLOCKED')

    def test_quotes_and_missing_form_are_disclosed_without_expert_penalty(self):
        f=self.run_it()
        evidence=f['races'][0]['models']['V6']['input_evidence']
        self.assertEqual(evidence['model_weight_used'],1)
        self.assertEqual(evidence['expert_weight_used'],0)
        self.assertIn('observed_market_residual',evidence['imputed_active_features'])
        self.assertEqual(evidence['observed_counts']['log_market_probability'],3)
        self.assertEqual(evidence['observed_counts']['barrier'],3)
        self.assertEqual(evidence['observed_counts']['observed_market_residual'],0)
        rows=f['races'][0]['models']['V6']['ranked_runners']
        for r in rows:
            self.assertAlmostEqual(r['numerical_win_edge'],r['probability']*r['odds']-1)
            self.assertAlmostEqual(r['fair_win_odds'],1/r['probability'])
        self.assertAlmostEqual(sum(r['market_probability'] for r in rows),1)


class PriceContractTests(unittest.TestCase):
    def test_identity_and_price_contract_not_weakened(self):
        rows=[dict(number='1',horse='A',odds=3)]
        validate_output(rows,rows)
        for changed,code in [(dict(rows[0],horse='B'),'model_output_identity_mismatch'),
                             (dict(rows[0],odds=3.0000000000000004),'model_output_price_mismatch')]:
            with self.assertRaises(OutputContractError) as e:validate_output([changed],rows)
            self.assertEqual(e.exception.code,code)

class BookmakerEvidenceTests(unittest.TestCase):
    def test_attribution_does_not_change_price_selection(self):
        from krok_adapter import price,named_bookmaker
        for runner,expected in [
            ({'fixed_win':3.1,'best_win':3.2,'best_win_bookmaker':'Sportsbet'},None),
            ({'best_win':3.2,'best_win_bookmaker':'Sportsbet'},'Sportsbet'),
            ({'fixed_win':3.1,'odds':[{'bookmaker':'Sportsbet','win':3.1}]},'Sportsbet'),
            ({'fixed_win':3.1,'odds':[{'bookmaker':'Betfair','win':3.1}]},None),
            ({'fixed_win':3.1,'odds':[{'bookmaker':'Sportsbet','win':3.2}]},None),
            ({'fixed_win':3.1,'odds':[{'bookmaker':'Sportsbet','bookmaker_type':'exchange','win':3.1}]},None),
        ]:
            with self.subTest(runner=runner):
                selected,origin=price(runner)
                self.assertEqual(selected,runner.get('fixed_win',runner.get('best_win')))
                self.assertEqual(named_bookmaker(runner,selected,origin),expected)

class FrozenTraceTests(unittest.TestCase):
    def test_trace_rejects_changed_reported_probability_without_fitting(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from operations.model_audit import trace
        with TemporaryDirectory() as td:
            root=Path(td);engine=root/'v6';(engine/'results').mkdir(parents=True)
            model=dict(input_feature_names=['log_market_probability','barrier'],
              numeric_feature_names=['log_market_probability','barrier','log_market_probability_missing','barrier_missing'],
              imputation_medians=[0,0],mean=[0,0,0,0],scale=[1,1,1,1],selected='linear',
              models={'linear':{'kind':'linear','weights':[0,0,0]}})
            (engine/'results/frozen_model.json').write_text(json.dumps(model))
            directory=root/'out';directory.mkdir()
            (directory/'validated_runners.csv').write_text('number,odds,barrier\n1,2,1\n2,4,2\n3,4,3\n')
            output=directory/'monty_selections.csv'
            output.write_text('number,monty_prob\n1,0.5\n2,0.25\n3,0.25\n')
            actual=trace('V6',directory,root,engine)
            self.assertEqual(actual['1']['feature_log_correction'],0)
            self.assertAlmostEqual(actual['1']['reconstructed_probability'],.5)
            output.write_text('number,monty_prob\n1,0.6\n2,0.2\n3,0.2\n')
            with self.assertRaises(OutputContractError) as e:trace('V6',directory,root,engine)
            self.assertEqual(e.exception.code,'model_component_reconciliation_failed')
