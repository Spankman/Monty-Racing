"""Synthetic offline contracts; these are not live predictions or acceptance."""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import unittest
import monty_operations as ops
from operations.market_integrity import analyze,attach as market_attach
from operations.ruffies import audit,attach,text
from operations.delivery import compact

class Ruffies(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,26,1,tzinfo=timezone.utc)
        self.race=dict(meeting='Synthetic Track',race='1',captured_at=self.now.isoformat(),scheduled_start=(self.now+timedelta(minutes=10)).isoformat(),data_completeness=dict(active_runners=4))
        rows=[dict(number=str(i),horse='TEST RUNNER '+str(i),odds=o,probability=p,bookmaker='TAB',quote_timestamps=[self.now.isoformat()],quote_time_basis='KROK_PROVIDER_OBSERVATION_NOT_BOOKMAKER_UPDATE') for i,(o,p) in enumerate([(2,.45),(3,.3),(5,.11),(10,.14)],1)]
        self.model=ops.selection(rows,'V6');self.model.update(status='SCORED',model_version='V6',no_bet_reasons=['independent_verification_missing'],input_evidence=dict(historical_form_verified=False,active_features=43,fully_observed_active_features=12))
        market=analyze(rows,expected_active=4,captured_at=self.race['captured_at'],now=self.now,context=dict(active_identities=[[r['number'],r['horse']] for r in rows]))
        market_attach(self.model,market)
    def test_valid_research_survives_missing_independent_verification(self):
        section=audit(self.race,self.model,'V6',self.now);r=section['rows'][0]
        self.assertEqual(section['research_candidates'],1);self.assertEqual(r['status'],'PROVISIONAL RESEARCH')
        self.assertFalse(r['betting_authorised']);self.assertGreater(r['predictive_advantage'],0)
        self.assertAlmostEqual(r['numerical_expected_value'],r['market_normalisation_edge']+r['model_edge_contribution'])
    def test_v7_unchanged_floor(self):
        model=deepcopy(self.model);rows=model['ranked_runners'];target=next(r for r in rows if r['number']=='4');target['odds']=30;target['probability']=.05;rows[0]['probability']+=.09
        section=audit(self.race,model,'V7',self.now)
        r=next(r for r in section['rows'] if r['number']=='4')
        self.assertFalse(r['research_candidate']);self.assertIn('existing_V7_probability_floor_6pct',r['reasons'])
    def test_underround_normalisation_does_not_become_model_value(self):
        m=deepcopy(self.model);rows=m['ranked_runners']
        for row in rows:row['odds']*=2
        total=sum(1/r['odds'] for r in rows)
        for row in rows:row['probability']=(1/row['odds'])/total
        section=audit(self.race,m,'V6',self.now)
        self.assertEqual(section['research_candidates'],0)
        for r in section['rows']:
            self.assertIn('underround_requires_independent_verification',r['reasons'])
            self.assertFalse(r['betting_authorised'])
    def test_missing_full_archive_not_reconstructed_from_ticket(self):
        m=deepcopy(self.model);m.pop('ranked_runners')
        section=audit(self.race,m,'V6',self.now)
        self.assertFalse(section['complete_scored_field']);self.assertIn('cannot be reconstructed',section['none_reason'])
        self.assertTrue(all(r['normalised_market_probability'] is None for r in section['rows']))
    def test_missing_quote_clock_is_not_capture_time(self):
        m=deepcopy(self.model)
        for r in m['ranked_runners']:r.pop('quote_timestamps')
        r=audit(self.race,m,'V6',self.now)['rows'][0]
        self.assertIsNone(r['price_observed_at']);self.assertIsNone(r['price_valid_until']);self.assertFalse(r['research_candidate'])
    def test_mixed_book_and_stale_offer_block(self):
        m=deepcopy(self.model);m['ranked_runners'][0]['bookmaker']='Sportsbet'
        self.assertEqual(audit(self.race,m,'V6',self.now)['research_candidates'],0)
        m=deepcopy(self.model)
        for r in m['ranked_runners']:r['quote_timestamps']=[(self.now-timedelta(seconds=300)).isoformat()]
        r=audit(self.race,m,'V6',self.now)['rows'][0]
        self.assertFalse(r['display_watch']);self.assertIn('expired_offer_or_race_closed',r['reasons'])
    def test_compact_retrieval_preserves_verified_calculations_and_expires(self):
        attach(self.race,self.model,'V6',self.now)
        view=dict(version='V6',view='provisional',date='2026-11-26',races=[dict(self.race,result=self.model)])
        c=compact(view);refreshed=ops.refresh_view(c,self.now+timedelta(seconds=30))
        self.assertEqual(refreshed['races'][0]['result']['ruffies_to_watch']['research_candidates'],1)
        self.assertIn('RUFFIES TO WATCH',ops.ticket(c,now=self.now))
        expired=ops.ticket(c,now=self.now+timedelta(seconds=300))
        self.assertNotIn('model 14.000%',expired);self.assertIn('EXPIRED',expired)
    def test_standard_and_provisional_render_same_research_with_no_duplicate_watch(self):
        for mode in ('official','provisional'):
            result=ops.current_result(self.race,self.model,mode,self.now)
            view=dict(version='V6',view=mode,date='2026-11-26',races=[dict(self.race,result=result)])
            t=ops.ticket(view,now=self.now)
            self.assertEqual(t.count('RUFFY / VALUE WATCH'),1);self.assertIn('RUFFIES TO WATCH',t)
            from operations.render import render
            h=render(view,now=self.now);self.assertIn('RUFFIES TO WATCH',h);self.assertIn('Official approval: NOT APPROVED',h)
    def test_saved_forecast_not_mutated_and_no_floor_relaxation(self):
        before=deepcopy(self.model);audit(self.race,self.model,'V6',self.now);self.assertEqual(before,self.model)
        self.assertEqual(ops.MAX_AGE_SECONDS,300);self.assertEqual(ops.command('C'),{'command':'C','view':'status'})
    def test_unknown_ranked_runner_does_not_get_an_invented_identity(self):
        m=dict(status='BLOCKED',no_bet_reasons=['missing_input'])
        section=audit(self.race,m,'V7',self.now)
        self.assertEqual(section['rows'],[]);self.assertEqual(section['unknown_unpreserved_runners'],4)

    def test_archive_audit_accounts_for_missing_without_naming_them(self):
        from operations.audit.roughies_240 import archived
        m=dict(status='SCORED',ordered_selections=[dict(number='1',horse='SYNTHETIC',odds=2,probability=.5)],roughies=[])
        f=dict(run_id='offline',captured_at=self.race['captured_at'],valid_until=self.race['scheduled_start'],coverage=dict(provider_races=1,provider_skips=[]),races=[dict(self.race,models={'V6':m,'V7':deepcopy(m)})])
        summary,rows,contrast=archived(f,1.06)
        self.assertEqual(summary['models']['V6']['missing_scored_runners'],3)
        self.assertEqual(summary['models']['V6']['saved_longshots'],0);self.assertEqual(len(rows),2)
        self.assertTrue(all(r['market_probability'] is None for r in rows))
    def test_sensitivity_is_not_expert_blending_or_refitting(self):
        import numpy as np
        from operations.audit.roughies_240 import sensitivities
        market=np.array([.8,.2]);p=np.array([.75,.25]);before=p.copy()
        arms=sensitivities({'market':market,'v6':p,'v7':p},['a','a'],1.06)
        np.testing.assert_array_equal(p,before)
        np.testing.assert_allclose(arms['v6_research_form_scale_0'],market)
        self.assertTrue(all(abs(v.sum()-1)<1e-12 for v in arms.values()))
    def test_missing_place_labels_not_invented_and_roi_stress(self):
        import numpy as np,pandas as pd
        from operations.audit.roughies_240 import metric,DayBootstrap,BANDS
        d=pd.DataFrame(dict(date=['2026-06-01']*2,WIN_MARKET_ID=['a','b'],BEST_AVAIL_BACK_AT_SCHEDULED_OFF=[10,20],market_probability=[.1,.05],y=[1,0]))
        result=metric(d,np.array([.1,.05]),np.ones(2,bool),DayBootstrap(d.date))
        self.assertIsNone(result['place_strike']);self.assertEqual(result['quote_roi_no_fee'],4)
        self.assertEqual(result['roi_if_top3_winner_payouts_removed'],-1)
        self.assertEqual(BANDS[:3],((10,20),(20,40),(40,60)))
    def test_all_four_commands_and_ps_aliases_retain_research_section(self):
        v7=deepcopy(self.model);v7['model_version']='V7'
        f=dict(run_id='offline',date='2026-11-26',status='COMPLETED_ASSESSMENTS',races=[dict(self.race,country='AU',market_integrity=self.model['market_integrity'],models={'V6':self.model,'V7':v7})])
        for command in ['RM6','RM7','RM6PS','RM7PS','RMV6PS','RMV7PS']:
            req=ops.command(command,'2026-11-26');view=ops.projection(f,req,self.now)
            view=compact(view)
            section=ops.refresh_view(view,self.now)['races'][0]['result']['ruffies_to_watch']
            self.assertEqual(section['research_candidates'],1,command)
            self.assertEqual(section['rows'][0]['model_version'],req['version'])
            self.assertIn('RUFFIES TO WATCH',ops.ticket(view,now=self.now))
            self.assertFalse(section['rows'][0]['betting_authorised'])
    def test_missing_capture_time_blocks_instead_of_inventing_expiry(self):
        race=dict(self.race,captured_at=None)
        row=audit(race,self.model,'V6',self.now)['rows'][0]
        self.assertIsNone(row['capture_valid_until']);self.assertFalse(row['research_candidate'])
        self.assertIn('capture_or_jump_timing_unavailable',row['reasons'])
    def test_no_qualifying_candidate_is_explicit_and_preserves_genuine_no_bet(self):
        model=deepcopy(self.model);model['betting_decision']='NO BET'
        for row in model['ranked_runners']:
            if row['number']=='4':row['odds']=6
        before=deepcopy(model);section=audit(self.race,model,'V6',self.now)
        self.assertEqual(section['research_candidates'],0);self.assertTrue(section['none_reason'])
        self.assertEqual(model,before);self.assertEqual(model['betting_decision'],'NO BET')
    def test_future_capture_and_offer_cannot_be_research_candidates(self):
        race=dict(self.race,captured_at=(self.now+timedelta(seconds=1)).isoformat())
        row=audit(race,self.model,'V6',self.now)['rows'][0]
        self.assertFalse(row['research_candidate']);self.assertIn('future_capture_timestamp',row['reasons'])
        model=deepcopy(self.model)
        for r in model['ranked_runners']:r['quote_timestamps']=[(self.now+timedelta(seconds=1)).isoformat()]
        row=audit(self.race,model,'V6',self.now)['rows'][0]
        self.assertFalse(row['research_candidate']);self.assertIn('future_offer_timestamp',row['reasons'])
    def test_recent_price_change_is_not_a_provider_observation(self):
        model=deepcopy(self.model)
        for row in model['ranked_runners']:row['quote_time_basis']='OFFER_REPORTED_TIME_UNVERIFIED'
        row=audit(self.race,model,'V6',self.now)['rows'][0]
        self.assertFalse(row['research_candidate']);self.assertIsNone(row['price_observed_at'])
        self.assertIn('offer_observation_basis_unverified',row['reasons'])
if __name__=='__main__':unittest.main()
