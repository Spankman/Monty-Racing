from datetime import timedelta
from pathlib import Path
import json,unittest
from unittest.mock import patch
import monty_operations as ops
import test_monty_operations as fixtures
from operations import prospective
from operations.public_sources import sportsbet

class IntegrationTests(unittest.TestCase):
    setUp=fixtures.RunTests.setUp
    run_it=fixtures.RunTests.run_it
    scorer=fixtures.RunTests.scorer
    def test_requested_v6_success_does_not_depend_on_v7(self):
        self.payload['data'][0]['races'][0]['runners'].pop()
        def two(v,*args):
            rows=self.scorer(v,*args)
            for r,p in zip(rows,[.6,.4]):r['probability']=p
            return rows
        f=self.run_it(scorer=two)
        self.assertEqual(f['status'],'COMPLETED_ASSESSMENTS')
        self.assertEqual(f['models']['V7']['blocked_races'],1)
        self.assertEqual(f['models']['V6']['failed_races'],0)
    def test_completed_probabilities_preserved_if_capture_expires_during_inference(self):
        def expire(v,*args):
            rows=self.scorer(v,*args)
            self.clock.return_value=self.now+timedelta(minutes=5)
            return rows
        with patch.object(ops,'utcnow',return_value=self.now) as self.clock:
            f=self.run_it(scorer=expire)
        m=f['races'][0]['models']['V6']
        self.assertEqual(f['status'],'EXPIRED');self.assertEqual(m['status'],'SCORED')
        self.assertTrue(m['ranked_runners']);self.assertEqual(m['betting_decision'],'EXPIRED')
        self.assertFalse(ops.projection(f,ops.command('RM6',self.day),self.now+timedelta(minutes=5))['races'][0]['result']['ordered_selections'])
        self.assertEqual([v for v,_ in self.calls],['V6'])
    def test_prejump_freeze_is_immutable_and_unverified_data_never_settles(self):
        f=self.run_it();p=self.root/'prospective.json'
        record=prospective.freeze(f,f['races'][0],{},p,self.now)
        self.assertFalse(record['cohort_admitted'])
        with self.assertRaises(FileExistsError):prospective.freeze(f,f['races'][0],{},p,self.now)
        with self.assertRaises(ValueError):prospective.settle(p,{},self.root/'settlement.json',self.now)
    def test_fixture_verified_cohort_metrics_and_official_result_guard(self):
        f=self.run_it();p=self.root/'verified.json';r=f['races'][0]
        prospective.freeze(f,r,dict(race_verified=True,fixed_win_verified=True,emergency_status_verified=True,sources=[dict(source_url=url,observed_at=self.now.isoformat(),sha256='a'*64,status='CAPTURED',http_status=200) for url in ['https://www.racingqueensland.com.au/fixture-only','https://www.sportsbet.com.au/fixture-only']]),p,self.now)
        result=dict(official=True,status='FINAL',date=f['date'],meeting=r['meeting'],race=r['race'],country=r['country'],
            active_runners={x['number']:x['horse'] for x in r['models']['V6']['ranked_runners']},winners=['1'],late_field_change=False,
            source_url='https://www.racingqueensland.com.au/fixture-only',source_sha256='a'*64,
            observed_at=(self.now+timedelta(hours=2)).isoformat())
        done=prospective.settle(p,result,self.root/'settled.json',self.now+timedelta(hours=2))
        self.assertTrue(done['metrics']['V6']['top_pick_won']);self.assertGreater(done['metrics']['V6']['log_loss'],0)
        with self.assertRaises(ValueError):prospective.settle(p,dict(result,official=False),self.root/'invalid.json',self.now+timedelta(hours=2))
        with self.assertRaises(ValueError):prospective.settle(p,dict(result,late_field_change=True),self.root/'invalid.json',self.now+timedelta(hours=2))

class PrimaryBookTests(unittest.TestCase):
    def state(self):
        from datetime import datetime,timezone
        ms=datetime(2026,11,25,4,48,tzinfo=timezone.utc).timestamp()*1000
        return {'entities':{'sportsbook':{'competitions':{'1':{'name':'Ipswich'}},'events':{'99':{'id':99,'competitionId':1,'raceNumber':4,'startTime':{'milliseconds':ms},'status':'ACTIVE','primaryMarketId':3,'distance':'2150','trackStatus':'Soft (5)'}},'markets':{'3':{'id':3,'name':'Win or Place','active':True,'displayed':True,'outcomeIds':[4,5]}},'outcomes':{'4':{'id':4,'marketId':3,'name':'Fixture','active':True,'runnerNumber':1,'winPrice':{'num':6,'den':4}},'5':{'id':5,'marketId':3,'name':'Withdrawal','active':False,'runnerNumber':2}}}}}
    def parse(self,d):
        return sportsbet(('<script>window.__PRELOADED_STATE__ = '+json.dumps(d)+';</script>').encode(),'https://www.sportsbet.com.au/horse-racing/australia-nz/ipswich/race-4-99','2026-11-25','Ipswich',4)
    def test_primary_fixed_win_market_not_exotic_or_tips(self):
        d=self.state();d['entities']['sportsbook']['events']['99']['tippedSelections']=[5]
        r=self.parse(d);self.assertEqual(r['runners'][0]['fixed_win'],'2.5');self.assertTrue(r['runners'][1]['scratched'])
        self.assertEqual(r['condition'],'Soft 5')
        d['entities']['sportsbook']['markets']['3']['name']='Quinella'
        with self.assertRaises(ValueError):self.parse(d)
    def test_mismatched_date_market_and_duplicate_identity_fail_closed(self):
        d=self.state();d['entities']['sportsbook']['events']['99']['raceNumber']=5
        with self.assertRaises(ValueError):self.parse(d)
        d=self.state();d['entities']['sportsbook']['outcomes']['5']['runnerNumber']=1
        with self.assertRaises(ValueError):self.parse(d)

class PairTests(unittest.TestCase):
    setUp=fixtures.RunTests.setUp
    run_it=fixtures.RunTests.run_it
    scorer=fixtures.RunTests.scorer
    def test_pair_deduplicates_identical_races_but_not_conflicting_captures(self):
        from copy import deepcopy
        from operations.tickets import paired
        f=self.run_it();f['races'].append(deepcopy(f['races'][0]))
        result=paired(f,self.now)
        self.assertEqual(len(result['tickets']),2);self.assertFalse(result['image_generated'])
        self.assertEqual(result['tickets'][0]['text'].count('Test R1'),1)
        self.assertIn('RESEARCH ONLY',result['tickets'][1]['text'])
        f['races'][1]['captured_at']=(self.now-timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):paired(f,self.now)
