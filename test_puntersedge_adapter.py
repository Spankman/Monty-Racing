"""Synthetic transport/data contracts; live receipts are separate evidence."""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from io import BytesIO
from urllib.error import HTTPError
from tempfile import TemporaryDirectory
from pathlib import Path
import json,unittest

from puntersedge_adapter import Client,ProviderError,canonical_race,safe_usage
from operations.market_integrity import quote_evidence,analyze
import krok_adapter


class Response(BytesIO):
    status=200
    def __init__(self,value):super().__init__(json.dumps(value).encode());self.headers={'X-Credits-Cost':'2'}


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,25,8,tzinfo=timezone.utc)
        self.race=dict(race_id='fixture',country='AU',category='horse',venue='Fixture',race_number=1,
            start_time=(self.now+timedelta(hours=1)).isoformat(),race_name='Benchmark 60',distance_m=1200,
            track_condition='Good 4',scratchings=[dict(number=4,name='Withdrawn')],
            runners=[dict(number=i,name='Fixture '+str(i),barrier=i,weight=56,
                bookmakers=[dict(key='tab',win_price=p,last_update=self.now.isoformat(),age_basis='poll')]) for i,p in [(1,3.),(2,4.),(3,6.)]])

    def test_auth_header_only_and_safe_usage_output(self):
        captured=[]
        def open(req,timeout):captured.append(req);return Response({'plan':'free'})
        c=Client('synthetic-key-not-real',opener=open)
        c.get('/v1/usage');self.assertEqual(captured[0].get_header('X-api-key'),'synthetic-key-not-real')
        self.assertNotIn('synthetic-key-not-real',captured[0].full_url)
        self.assertNotIn('synthetic-key-not-real',json.dumps(c.usage)+json.dumps(c.responses))
        self.assertEqual(safe_usage(dict(plan='free',email='private',upgrade='private',credits_limit=1500)),{'plan':'free','credits_limit':1500})

    def test_no_billing_or_key_routes_and_C_never_calls(self):
        calls=[];c=Client('fixture',opener=lambda *a,**k:calls.append(a))
        for route in ('/v1/account','/v1/keys/reveal','/v1/billing/upgrade-link'):
            with self.assertRaises(ProviderError):c.get(route)
        with self.assertRaises(ProviderError):c.get('/v1/racing/events',command='C')
        self.assertFalse(calls)

    def test_bounded_retry_and_no_retry_of_forbidden_or_quota(self):
        calls=[];sleeps=[]
        def open(req,timeout):
            calls.append(req)
            if len(calls)==1:raise HTTPError(req.full_url,429,'private error',{'Retry-After':'1'},None)
            return Response([])
        c=Client('fixture',opener=open,sleeper=sleeps.append);c.get('/v1/racing/events')
        self.assertEqual(len(calls),2);self.assertEqual(sleeps,[1.])
        for status in (401,402,403,302):
            calls.clear()
            def fail(req,timeout):calls.append(req);raise HTTPError(req.full_url,status,'private error',{},None)
            with self.assertRaisesRegex(ProviderError,str(status)):Client('fixture',opener=fail).get('/v1/racing/events')
            self.assertEqual(len(calls),1)

    def test_budget_prevents_extra_requests(self):
        c=Client('fixture',budget=0,opener=lambda *a,**k:self.fail('Network must not run'))
        with self.assertRaisesRegex(ProviderError,'budget'):c.get('/v1/racing/events')
        c=Client('fixture',budget=2,opener=lambda *a,**k:Response([]))
        c.get('/v1/racing/next-to-go',{'num_races':20});self.assertEqual(c.reserved,2)
        with self.assertRaisesRegex(ProviderError,'budget'):c.get('/v1/racing/next-to-go',{'num_races':20})

    def test_single_book_fields_keep_existing_features_and_scratchings(self):
        p=canonical_race(self.race,day='2026-11-25')
        snapshot,_=krok_adapter.normalize(p,'2026-11-25')
        self.assertEqual(len(snapshot['runners']),3)
        self.assertEqual(snapshot['runners'][0]['odds'],3.)
        self.assertEqual(snapshot['runners'][0]['outside_barrier'],0)
        self.assertAlmostEqual(snapshot['runners'][0]['barrier_x_distance'],.4)
        self.assertEqual(snapshot['runners'][0]['going_good'],1.)
        self.assertEqual(len(p['data'][0]['races'][0]['runners']),4)
        q=quote_evidence(p['data'][0]['races'][0]['runners'][0])
        self.assertEqual(q['quote_timestamps'],[self.now.isoformat()]);self.assertIn('PUNTERSEDGE',q['quote_time_basis'])
        self.assertFalse(p['meta']['independent_verification']);self.assertFalse(p['meta']['historical_features_joined'])

    def test_push_or_price_change_time_is_never_a_poll_observation(self):
        for basis in ('push_receipt','price_change',None):
            r=deepcopy(self.race);r['runners'][0]['bookmakers'][0]['age_basis']=basis
            p=canonical_race(r,day='2026-11-25');q=quote_evidence(p['data'][0]['races'][0]['runners'][0])
            self.assertEqual(q['quote_timestamps'],[])

    def test_no_mixed_books_or_partial_field_substitution(self):
        for mutation in ('missing','duplicate','foreign','date','scratching','closed','inplay'):
            r=deepcopy(self.race)
            if mutation=='missing':r['runners'][0]['bookmakers'][0]['key']='sportsbet'
            if mutation=='duplicate':r['runners'].append(deepcopy(r['runners'][0]))
            if mutation=='foreign':r['country']=None
            if mutation=='date':r['start_time']='2026-11-24T09:00:00Z'
            if mutation=='scratching':r['scratchings'][0]['number']=1
            if mutation=='closed':r['status']='abandoned'
            if mutation=='inplay':r['inplay_at']=self.now.isoformat()
            with self.subTest(mutation=mutation),self.assertRaises(ProviderError):canonical_race(r,day='2026-11-25')

    def test_stale_poll_stays_quarantined_without_changing_model_input(self):
        r=deepcopy(self.race)
        for runner in r['runners']:runner['bookmakers'][0]['last_update']=(self.now-timedelta(seconds=300)).isoformat()
        p=canonical_race(r,day='2026-11-25');quotes=[quote_evidence(x) for x in p['data'][0]['races'][0]['runners'] if not x['is_scratched']]
        audit=analyze(quotes,expected_active=3,captured_at=self.now.isoformat(),now=self.now)
        self.assertIn('stale_price',audit['warnings']);self.assertFalse(audit['actionable_value_allowed'])

    def test_acceptance_conflicts_do_not_become_verified_fields(self):
        acceptance=[dict(number=r['number'],name=r['name'],scratched=False) for r in self.race['runners']]+[dict(number=4,name='Withdrawn',scratched=True)]
        canonical_race(self.race,day='2026-11-25',acceptance=acceptance)
        acceptance[-1]['scratched']=False
        with self.assertRaisesRegex(ProviderError,'Acceptance'):canonical_race(self.race,day='2026-11-25',acceptance=acceptance)

    def test_partial_results_null_field_is_not_an_execution_failure_or_full_result(self):
        from operations.audit.puntersedge_probe import result_inventory
        result=result_inventory([dict(status='partial',runners=None),dict(status='final',runners=[{'number':1}])])
        self.assertEqual(result['full_runner_rows'],1);self.assertEqual(result['unavailable_runner_lists'],1)
        self.assertFalse(result['independent_official_settlement'])

    def test_cross_provider_book_aliases_and_observation_clocks_are_explicit(self):
        from operations.audit.puntersedge_probe import observe,compare
        pe=dict(runners=[dict(number=1,name='Fixture',bookmakers=[dict(key='pointsbetau',win_price=3.,age_basis='poll',last_update='2026-11-25T08:00:00Z')])])
        krok=dict(runners=[dict(number=1,name='Fixture',is_scratched=False,odds=[dict(bookmaker='PointsBet',win=3.,captured_at='2026-11-25T08:00:00+00:00')])])
        a,_,_=observe(pe,'PuntersEdge');b,_,_=observe(krok,'Krok');result=compare(a,b,self.now)
        self.assertEqual(result['exact_runner_name_number_book_matches'],1)
        self.assertEqual(result['exact_observation_time_matches'],1)
        self.assertFalse(result['independence_established'])


if __name__=='__main__':unittest.main()
