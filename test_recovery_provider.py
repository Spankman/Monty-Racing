"""Offline recovery regressions. Live proof has separate workflow receipts."""
from copy import deepcopy
from urllib.parse import urlsplit
import unittest
from puntersedge_adapter import Client,ProviderError,fetch_board
import test_puntersedge_adapter as fixtures
Response=fixtures.Response

class RecoveryProviderTests(unittest.TestCase):
    setUp=fixtures.ProviderTests.setUp
    def client(self,board,remaining=1000,events=None):
        self.calls=[]
        def open(req,timeout):
            path=urlsplit(req.full_url).path;self.calls.append(path)
            if path=='/v1/usage':return Response({'credits_remaining':remaining})
            if path=='/v1/racing/events':return Response(events if events is not None else board)
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
