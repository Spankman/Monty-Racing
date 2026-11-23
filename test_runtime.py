"""Simulated serving/security tests. No claim of live inference or mobile access."""
from datetime import datetime,timedelta,timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from runtime.provider import Provider,ProviderFailure
from runtime.service import Service
from runtime.http_api import API


class Clock:
    def __init__(self):self.now=datetime(2026,11,23,0,0,tzinfo=timezone.utc)
    def __call__(self):return self.now
    def advance(self,seconds):self.now+=timedelta(seconds=seconds)

class FakeProvider:
    def __init__(self):self.calls=0;self.error=None
    def fetch(self,day):
        self.calls+=1
        if self.error:raise self.error
        return {'simulated':True}

class FakeEngine:
    """Protocol stub: intentionally emits NO selections or probabilities."""
    def __init__(self):self.calls=0;self.error=None
    def __call__(self,req,out,job,payload,captured):
        self.calls+=1
        if self.error:raise self.error
        out=Path(out)/'public';out.mkdir(parents=True)
        result=dict(status='COMPLETED_NO_BET',ordered_selections=[],roughies=[],best_bets=[],
                    recommended_bet_type='NO BET',progression_bet_type='NO BET',no_bet_reasons=['SIMULATED CONTRACT ONLY'])
        race=dict(meeting=req.get('meeting') or 'Protocol Test',race=req.get('race') or '1',country='AU',
                  captured_at=captured.isoformat(),scheduled_start=(captured+timedelta(hours=1)).isoformat(),models={'V6':result,'V7':result})
        f=dict(schema='monty.operations.v1',date=req['date'],run_id=job,status='COMPLETED_NO_BET',captured_at=captured.isoformat(),
               valid_until=(captured+timedelta(seconds=300)).isoformat(),races=[race],models={},blockers=['SIMULATED CONTRACT ONLY'])
        fp=out/'forecast.json';fp.write_text(json.dumps(f))
        receipt=dict(run_id=job,status=f['status'],forecast_sha256=hashlib.sha256(fp.read_bytes()).hexdigest(),source_mode='SIMULATED CONTRACT ONLY')
        rp=out/'receipt.json';rp.write_text(json.dumps(receipt))
        return f,rp

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.clock=Clock();self.provider=FakeProvider();self.engine=FakeEngine()
        self.service=Service(self.tmp.name,self.provider,self.engine,clock=self.clock,asynchronous=False)
        self.addCleanup(self.service.close)
    def submit(self,command='RM6',**kw):return self.service.submit(command,date='2026-11-23',**kw)
    def test_models_views_and_aliases_share_fresh_execution(self):
        outputs=[self.submit(c) for c in ['RM6','RM7','RM6PS','RM7PS','RMV6PS','RMV7PS']]
        self.assertEqual({x['job_id'] for x in outputs},{outputs[0]['job_id']})
        self.assertEqual([x['view']['view'] for x in outputs],['official','shadow','provisional','provisional','provisional','provisional'])
        self.assertEqual(self.provider.calls,1);self.assertEqual(self.engine.calls,1)
        self.assertEqual(len({x['request_id'] for x in outputs}),6)
    def test_single_race_uses_shared_capture_and_is_not_daily_fallback(self):
        daily=self.submit();single=self.submit('RM7 Ballina R5')
        self.assertNotEqual(daily['job_id'],single['job_id']);self.assertEqual(self.provider.calls,1)
        self.assertEqual(single['view']['races'][0]['meeting'],'Ballina')
        self.assertEqual(single['view']['races'][0]['race'],'5')
    def test_c_never_starts_or_refreshes(self):
        self.assertEqual(self.service.submit('C')['request_status'],'NOT_FOUND')
        a=self.submit();self.clock.advance(301)
        b=self.service.submit('C',request_id=a['request_id'])
        self.assertEqual(b['request_status'],'EXPIRED');self.assertNotIn('ticket',b)
        self.assertEqual(self.provider.calls,1);self.assertEqual(self.engine.calls,1)
        self.assertEqual(b['capture_age_seconds'],301);self.assertTrue(b['valid_until']);self.assertTrue(b['receipt_sha256'])
    def test_stale_replaced_old_receipt_immutable(self):
        a=self.submit();original=self.service.directory/'runs'/a['job_id']/'public/forecast.json';saved=original.read_bytes()
        self.clock.advance(301);b=self.submit()
        self.assertNotEqual(a['job_id'],b['job_id']);self.assertEqual(self.provider.calls,2)
        self.assertEqual(original.read_bytes(),saved);self.assertEqual(b['capture_age_seconds'],0)
    def test_idempotency_does_not_resubmit_even_if_expired(self):
        a=self.submit(idempotency_key='operation-one');self.clock.advance(301)
        b=self.submit(idempotency_key='operation-one');self.assertEqual(a['request_id'],b['request_id'])
        self.assertEqual(b['request_status'],'EXPIRED');self.assertEqual(self.engine.calls,1)
        with self.assertRaises(ValueError):self.submit('RM7',idempotency_key='operation-one')
    def test_failures_no_silent_fallback_or_exception_leak(self):
        self.engine.error=RuntimeError('NEVER PRINT PRIVATE ERROR')
        a=self.submit();self.assertEqual(a['request_status'],'FAILED');self.assertNotIn('ticket',a)
        self.assertNotIn('PRIVATE',json.dumps(a));self.assertEqual(self.engine.calls,1)
    def test_missing_provider_credentials_recorded_without_engine(self):
        self.provider.error=ProviderFailure('PROVIDER_CREDENTIALS_MISSING')
        a=self.submit();self.assertEqual(a['error'],'PROVIDER_CREDENTIALS_MISSING');self.assertEqual(self.engine.calls,0)
    def test_integrity_tampering_withheld(self):
        a=self.submit();fp=self.service.directory/'runs'/a['job_id']/'public/forecast.json'
        fp.write_text('{}');b=self.service.status(a['request_id'])
        self.assertEqual(b['error'],'INTEGRITY_CHECK_FAILED');self.assertNotIn('ticket',b)
    def test_receipt_wrong_run_withheld(self):
        a=self.submit();rp=self.service.directory/'runs'/a['job_id']/'public/receipt.json'
        r=json.loads(rp.read_text());r['run_id']='unrelated';rp.write_text(json.dumps(r))
        self.assertEqual(self.service.status(a['request_id'])['error'],'INTEGRITY_CHECK_FAILED')
    def test_explicit_expiry_cannot_be_extended_by_cache(self):
        a=self.submit();root=self.service.directory/'runs'/a['job_id']/'public';fp=root/'forecast.json'
        f=json.loads(fp.read_text());f['valid_until']=self.clock().isoformat();fp.write_text(json.dumps(f))
        rp=root/'receipt.json';r=json.loads(rp.read_text());r['forecast_sha256']=hashlib.sha256(fp.read_bytes()).hexdigest();rp.write_text(json.dumps(r))
        self.clock.advance(1);self.assertEqual(self.service.status(a['request_id'])['request_status'],'EXPIRED')
    def test_closed_race_withheld(self):
        a=self.submit();self.clock.advance(3601)
        self.assertNotIn('ticket',self.service.status(a['request_id']))
    def test_reject_second_worker_same_state(self):
        with self.assertRaisesRegex(ValueError,'already owns'):Service(self.tmp.name,self.provider,self.engine)
    def test_old_date_rejected_without_provider(self):
        with self.assertRaises(ValueError):self.service.submit('RM6',date='2026-11-22')
        self.assertEqual(self.provider.calls,0)
    def test_pending_requests_deduplicate(self):
        self.service.asynchronous=True;entered=threading.Event();release=threading.Event();original=self.service.engine
        def blocked(*args):entered.set();release.wait(3);return original(*args)
        self.service.engine=blocked
        a=self.submit();self.assertTrue(entered.wait(1))
        try:
            b=self.submit('RM7PS');self.assertEqual(a['job_id'],b['job_id']);self.assertIn(b['request_status'],['QUEUED','RUNNING'])
            self.assertEqual(self.service.submit('C',request_id=b['request_id'])['request_status'],'RUNNING')
        finally:release.set()
        self.service.pool.shutdown(wait=True);self.assertEqual(self.engine.calls,1)

class Opener:
    def __init__(self,items):self.items=list(items);self.calls=0
    def open(self,req,timeout):
        self.calls+=1;x=self.items.pop(0)
        if isinstance(x,Exception):raise x
        return BytesIO(json.dumps(x).encode())

def page(data=None,**meta):return dict(success=True,data=data or [],meta=dict(total=len(data or []),has_more=False,**meta))

class ProviderTests(unittest.TestCase):
    def test_missing_key_no_network(self):
        o=Opener([])
        with self.assertRaisesRegex(ProviderFailure,'CREDENTIALS_MISSING'):Provider('',opener=o).fetch('2026-11-23')
        self.assertEqual(o.calls,0)
    def test_transient_retry_succeeds(self):
        o=Opener([HTTPError('https://example',503,'private',{},None),page()]);sleeps=[]
        self.assertEqual(Provider('test',opener=o,sleep=sleeps.append).fetch('2026-11-23')['data'],[])
        self.assertEqual(o.calls,2);self.assertEqual(sleeps,[.25])
    def test_rate_limit_cooldown_no_extra_calls(self):
        o=Opener([HTTPError('https://example',429,'private',{'Retry-After':'90'},None)])
        p=Provider('test',opener=o)
        for _ in range(2):
            with self.assertRaisesRegex(ProviderFailure,'RATE_LIMITED'):p.fetch('2026-11-23')
        self.assertEqual(o.calls,1)
    def test_incomplete_metadata_fail_closed(self):
        for p in [dict(success=True,data=[],meta={}),dict(success=True,data=[],meta={'total':1,'has_more':False})]:
            with self.assertRaises(ProviderFailure):Provider('test',opener=Opener([p])).fetch('2026-11-23')
    def test_auth_fail_not_retried(self):
        o=Opener([HTTPError('https://example',401,'private',{},None)])
        with self.assertRaisesRegex(ProviderFailure,'HTTP_401'):Provider('test',opener=o).fetch('2026-11-23')
        self.assertEqual(o.calls,1)
    def test_credential_echo_redacted(self):
        data=[dict(date='2026-11-23',country='AU',venue='testsecret',type='T')]
        result=Provider('testsecret',opener=Opener([page(data)])).fetch('2026-11-23')
        self.assertNotIn('testsecret',json.dumps(result))

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.clock=Clock();self.provider=FakeProvider();self.engine=FakeEngine()
        self.service=Service(self.tmp.name,self.provider,self.engine,clock=self.clock,asynchronous=False);self.addCleanup(self.service.close)
        self.execute='e'*40;self.read='r'*40
        self.api=API(('127.0.0.1',0),self.service,self.execute,self.read)
        threading.Thread(target=self.api.serve_forever,daemon=True).start();self.addCleanup(self.stop)
    def stop(self):self.api.shutdown();self.api.server_close()
    def call(self,path,body=None,token=None):
        req=Request('http://127.0.0.1:'+str(self.api.server_port)+path,data=json.dumps(body).encode() if body is not None else None,
                    headers={'Authorization':'Bearer '+(token or ''),'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=3) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    def test_unauthenticated_denied(self):self.assertEqual(self.call('/health')[0],401)
    def test_read_token_cannot_execute(self):
        code,_=self.call('/v1/commands',{'command':'RM6','date':'2026-11-23'},self.read)
        self.assertEqual(code,403);self.assertEqual(self.provider.calls,0)
    def test_status_readonly(self):
        code,d=self.call('/v1/commands',{'command':'C'},self.read)
        self.assertEqual((code,d['request_status']),(200,'NOT_FOUND'));self.assertEqual(self.provider.calls,0)
    def test_rest_execute_and_retrieve(self):
        code,d=self.call('/v1/commands',{'command':'RMV7PS','date':'2026-11-23'},self.execute)
        self.assertEqual((code,d['view']['version']),(200,'V7'))
        _,again=self.call('/v1/status/'+d['request_id'],token=self.read)
        self.assertEqual(again['receipt_sha256'],d['receipt_sha256']);self.assertEqual(self.provider.calls,1)
    def test_mcp_discovery_call_and_status(self):
        _,listing=self.call('/mcp',{'jsonrpc':'2.0','id':1,'method':'tools/list'},self.read)
        self.assertEqual(len(listing['result']['tools']),2)
        _,r=self.call('/mcp',{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'monty_status','arguments':{}}},self.read)
        self.assertEqual(r['result']['structuredContent']['request_status'],'NOT_FOUND');self.assertEqual(self.provider.calls,0)
    def test_mcp_read_token_cannot_execute(self):
        _,r=self.call('/mcp',{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'monty_execute','arguments':{'command':'RM6'}}},self.read)
        self.assertTrue(r['result']['isError']);self.assertEqual(self.provider.calls,0)
    def test_arbitrary_parameters_rejected(self):
        code,_=self.call('/v1/commands',{'command':'RM6','url':'https://untrusted'},self.execute)
        self.assertEqual(code,400);self.assertEqual(self.provider.calls,0)
    def test_separate_roles_required(self):
        with self.assertRaises(ValueError):API(('127.0.0.1',0),self.service,self.execute,self.execute)

if __name__=='__main__':unittest.main()
