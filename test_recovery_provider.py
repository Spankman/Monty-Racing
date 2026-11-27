"""Offline recovery regressions. Live proof has separate workflow receipts."""
from copy import deepcopy
from datetime import timedelta
from urllib.parse import urlsplit
import unittest
from puntersedge_adapter import Client,ProviderError,fetch_board
import test_puntersedge_adapter as fixtures
Response=fixtures.Response

class RecoveryProviderTests(unittest.TestCase):
    setUp=fixtures.ProviderTests.setUp
    def client(self,board,remaining=1000,events=None,acceptances=None):
        self.calls=[]
        def open(req,timeout):
            path=urlsplit(req.full_url).path;self.calls.append(path)
            if path=='/v1/usage':return Response({'credits_remaining':remaining})
            if path=='/v1/racing/events':return Response(events if events is not None else board)
            if path=='/v1/racing/acceptances':return Response(acceptances)
            return Response(board)
        return Client('synthetic',budget=10,opener=open)
    def run_board(self,board,**kw):
        return fetch_board('2026-11-25','synthetic',clock=lambda:self.now,client=self.client(board,**kw))
    def test_one_bad_race_does_not_discard_good_card(self):
        bad=deepcopy(self.race);bad.update(race_id='bad',race_number=2);bad['runners'][0]['bookmakers']=[]
        p,t=self.run_board([self.race,bad])
        self.assertEqual(p['meta']['eligible_races'],1)
        self.assertEqual(p['meta']['omissions'][0]['race_id'],'bad')
        self.assertEqual(t,self.now)
        self.assertFalse(p['meta']['complete_national_coverage_verified'])
        self.assertEqual(self.calls.count('/v1/racing/next-to-go'),1)
    def test_discovered_missing_race_is_visible(self):
        absent=dict(self.race,race_id='absent',race_number=2)
        p,_=self.run_board([self.race],events=[self.race,absent])
        self.assertEqual(p['meta']['omissions'][0]['race_id'],'absent')
        self.assertIn('absent',p['meta']['omissions'][0]['reason'])
    def test_allowance_failure_prevents_paid_calls(self):
        with self.assertRaisesRegex(ProviderError,'reserve'):self.run_board([self.race],remaining=509)
        self.assertEqual(self.calls,['/v1/usage'])
    def test_stale_quotes_not_retimestamped(self):
        old=deepcopy(self.race)
        for row in old['runners']:row['bookmakers'][0]['last_update']='2026-11-25T07:55:00Z'
        p,_=self.run_board([old]);self.assertEqual(p['data'],[])
        self.assertIn('expired',p['meta']['omissions'][0]['reason'])
    def test_C_does_not_even_query_allowance(self):
        c=self.client([self.race])
        with self.assertRaises(ProviderError):fetch_board('2026-11-25','synthetic',client=c,command='C')
        self.assertEqual(self.calls,[])
    def test_partial_board_does_not_claim_full_pagination(self):
        p,_=self.run_board([None]*200)
        self.assertTrue(p['meta']['board_at_limit'])
        self.assertEqual(len(p['meta']['omissions']),200)
        self.assertFalse(p['meta']['complete_national_coverage_verified'])

    def test_fresh_unchanged_poll_does_not_inherit_another_races_expiry(self):
        from monty_operations import freshness
        older=deepcopy(self.race)
        older.update(race_id='older',race_number=2)
        observed=(self.now-timedelta(seconds=299)).isoformat()
        for row in older['runners']:
            row['bookmakers'][0].update(last_update=observed, refresh_tier='card')
        p,t=self.run_board([self.race,older])
        later=self.now+timedelta(seconds=2)
        assessments=[freshness(dict(captured_at=t.isoformat(), scheduled_start=race['jump_time'],
                                    price_observed_at=race['price_observed_at']), later)
                     for race in p['data'][0]['races']]
        self.assertEqual(t,self.now)
        self.assertEqual(assessments[0],'FRESH AT CHECK TIME')
        self.assertIn('STALE',assessments[1])
        self.assertEqual(p['meta']['tab_clock_counts']['card/cache-unreported-or-fresh/fresh'],1)

    def test_dated_identity_conflict_quarantines_only_the_matching_race(self):
        other=dict(self.race,race_id='other',race_number=2)
        declaration=dict(race_id='fixture',race_number=1,runners=[
            dict(number=1,runner_name='Different Horse',emergency=False,scratched=False)])
        declared_missing=dict(race_id='missing',race_number=3,runners=[])
        acceptances=dict(date='2026-11-25',meetings=[
            dict(venue='Fixture',races=[declaration,declared_missing])])
        p,_=self.run_board([self.race,other],acceptances=acceptances)
        self.assertEqual(p['meta']['eligible_races'],1)
        self.assertEqual(p['meta']['dated_race_count'],2)
        self.assertIn('identities disagree',p['meta']['omissions'][0]['reason'])
        self.assertIn('absent',p['meta']['omissions'][1]['reason'])

    def test_duplicate_board_race_is_quarantined_without_losing_other_races(self):
        second=dict(self.race,race_id='second',race_number=2)
        conflict=dict(self.race,runners=[])
        p,_=self.run_board([self.race,second,conflict])
        self.assertEqual(p['meta']['eligible_races'],1)
        self.assertEqual(p['meta']['duplicate_board_races'],1)
