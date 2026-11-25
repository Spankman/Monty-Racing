"""Offline arithmetic and archived incident regression; no simulated live claim."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import csv,json,math
from pathlib import Path
import unittest

import monty_operations as ops
from operations.market_integrity import analyze,attribute,attach,archived_race,quote_evidence,refresh
from operations.delivery import compact
from operations.render import render


class MarketTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,25,5,tzinfo=timezone.utc)
        self.rows=[dict(number='1',horse='A',odds=2.,probability=5/6,bookmaker='TAB',quote_timestamps=[self.now.isoformat()]),
                   dict(number='2',horse='B',odds=10.,probability=1/6,bookmaker='TAB',quote_timestamps=[self.now.isoformat()])]
        self.context=dict(active_identities=[['1','A'],['2','B']],declared_count=2,observed_declared_count=2)

    def audit(self,rows=None,**kwargs):
        return analyze(self.rows if rows is None else rows,expected_active=kwargs.pop('expected_active',2),
            captured_at=self.now.isoformat(),now=self.now,context=kwargs.pop('context',self.context),**kwargs)

    def test_underround_decomposition_is_not_predictive_value(self):
        audit=self.audit();self.assertAlmostEqual(audit['book_percentage'],60)
        self.assertAlmostEqual(audit['overround_percentage_points'],-40)
        self.assertAlmostEqual(audit['underround_percentage_points'],40)
        self.assertIn('underround_requires_independent_verification',audit['warnings'])
        for row in attribute(self.rows,audit):
            self.assertAlmostEqual(row['model_probability_uplift'],0)
            self.assertAlmostEqual(row['model_edge_contribution'],0)
            self.assertAlmostEqual(row['market_only_numerical_edge'],2/3)
            self.assertFalse(row['actionable_value'])

    def test_overround_even_and_incomplete_book(self):
        rows=deepcopy(self.rows);rows[1]['odds']=1.5
        audit=self.audit(rows);self.assertAlmostEqual(audit['book_percentage'],116.6666666667)
        self.assertEqual(audit['underround_percentage_points'],0)
        rows[1]['odds']=2.;self.assertEqual(self.audit(rows)['book_percentage'],100)
        audit=self.audit(self.rows[:1]);self.assertIsNone(audit['book_percentage'])
        self.assertIsNone(attribute(self.rows[:1],audit)[0]['market_probability'])
        self.assertAlmostEqual(audit['observed_book_lower_bound_pct'],50)
        context=dict(self.context,declared_count=3)
        self.assertIsNone(self.audit(context=context)['book_percentage'])
        rows=deepcopy(self.rows);rows[1]['number']='1'
        self.assertIn('duplicate_runner_identity',self.audit(rows)['warnings'])

    def test_quote_ages_and_bookmakers_fail_closed(self):
        for change,flag in [({'bookmaker':'Sportsbet'},'mixed_bookmakers'),
                            ({'bookmaker':None},'bookmaker_unverified'),
                            ({'quote_timestamps':[]},'quote_timestamp_unavailable'),
                            ({'quote_timestamps':['2026-11-25T05:00:00']},'invalid_quote_timestamp'),
                            ({'quote_timestamps':[(self.now-timedelta(seconds=300)).isoformat()]},'stale_price'),
                            ({'quote_timestamps':[(self.now+timedelta(seconds=1)).isoformat()]},'future_quote_timestamp'),
                            ({'quote_timestamps':[(self.now-timedelta(seconds=1)).isoformat()]},'inconsistent_quote_timestamps')]:
            with self.subTest(flag=flag):
                rows=deepcopy(self.rows);rows[1].update(change);audit=self.audit(rows)
                self.assertIn(flag,audit['warnings']);self.assertFalse(audit['actionable_value_allowed'])
        self.assertIn('stale_price',refresh(self.audit(),self.now+timedelta(seconds=300))['warnings'])

    def test_quote_time_binds_first_selected_offer_not_other_quote_or_capture(self):
        r=dict(number=1,name='A',odds=[dict(bookmaker='TAB',win=2),dict(bookmaker='TAB',win=2,quoted_at=self.now.isoformat())])
        self.assertEqual(quote_evidence(r)['quote_timestamps'],[])
        r['odds'][0]['updated_at']=self.now.isoformat()
        self.assertEqual(quote_evidence(r)['quote_timestamps'],[self.now.isoformat()])
        r=dict(number=1,name='A',fixed_win=4,best_win=5,best_win_quoted_at=self.now.isoformat())
        self.assertEqual(quote_evidence(r)['quote_timestamps'],[])

    def test_positive_model_contribution_is_separate_and_never_approval(self):
        rows=deepcopy(self.rows);rows[1]['probability']+=.01;rows[0]['probability']-=.01
        audit=self.audit(rows);attributed=attribute(rows,audit)
        for row in attributed:
            self.assertAlmostEqual(row['probability']*row['odds']-1,
                row['market_only_numerical_edge']+row['model_edge_contribution'])
        self.assertGreater(attributed[1]['model_edge_contribution'],0)
        model=ops.selection(rows,'V6');original=deepcopy(model['roughies']);attach(model,audit)
        self.assertEqual([r['number'] for r in original],[r['number'] for r in model['roughies']])
        self.assertFalse(model['betting_authorised']);self.assertEqual(model['recommended_bet_type'],'NO BET')


class IncidentTests(unittest.TestCase):
    def setUp(self):
        self.forecast=json.loads(Path('testdata/market_integrity_2026-11-25.json').read_text())
        self.now=ops.timestamp(self.forecast['captured_at'])+timedelta(seconds=30)

    def test_exact_archived_books_and_model_edges_match_independent_work_audit(self):
        with open('operations/audit/roughie_evidence/runner_comparison.csv') as handle:comparisons=list(csv.DictReader(handle))
        for race in self.forecast['races']:
            marked=archived_race(race,race['captured_at'],self.now)
            audit=marked['market_integrity']
            book=95.92415945710076 if race['meeting']=='Geelong' else 72.74642159661809
            self.assertAlmostEqual(audit['book_percentage'],book,places=3)
            self.assertEqual(audit['status'],'QUARANTINED')
            for version,model in marked['models'].items():
                self.assertTrue(model['market_baseline']['complete'])
                baseline=model['market_integrity']['market_only_baseline']
                self.assertEqual(len(baseline),race['data_completeness']['active_runners'])
                self.assertAlmostEqual(sum(r['probability'] for r in baseline),1)
                for row in model['roughies']:
                    source=next(r for r in comparisons if r['meeting']==race['meeting'] and r['race']==str(race['race']) and r['number']==str(row['number']))
                    self.assertAlmostEqual(row['model_probability_uplift']*100,float(source[version+'_uplift_pp']))
                    self.assertFalse(row['actionable_value'])

    def test_all_four_views_preserve_watches_warnings_and_expiry_in_text_html_compact(self):
        frozen=deepcopy(self.forecast)
        for command,version in [('RM6','V6'),('RM7','V7'),('RM6PS','V6'),('RM7PS','V7')]:
            view=ops.projection(self.forecast,ops.command(command,'2026-11-25'),self.now)
            expected=sum(len(r['models'][version]['roughies']) for r in self.forecast['races'])
            for candidate in [view,compact(view),ops.refresh_view(view,self.now)]:
                text=ops.ticket(candidate,now=self.now);html=render(candidate,now=self.now)
                self.assertEqual(text.count('RUFFY / VALUE WATCH'),expected)
                self.assertIn('MARKET QUARANTINED',text);self.assertIn('underround_requires_independent_verification',html)
                self.assertIn('NO BET',text)
                self.assertNotIn('RUFFY / VALUE WATCH',ops.ticket(candidate,now=self.now+timedelta(minutes=5)))
        self.assertEqual(self.forecast,frozen)

    def test_missing_archive_price_never_gets_normalized_or_invented(self):
        race=deepcopy(self.forecast['races'][0]);race['data_completeness']['active_runners']+=1
        audit=archived_race(race,race['captured_at'],self.now)['market_integrity']
        self.assertFalse(audit['complete_price_vector']);self.assertIsNone(audit['market_only_numerical_edge'])


if __name__=='__main__':unittest.main()
