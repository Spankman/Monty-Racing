from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest,json,time

from operations.market_integrity import quote_evidence
from operations.data_acquisition import CaptureBatch,HistoryStore,eligible,record_usage,usage_summary,independent_lineage
import krok_adapter


class DataTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,25,7,tzinfo=timezone.utc)
        self.offer=dict(bookmaker='TAB',win=3,captured_at=self.now.isoformat())
        self.runner=dict(number=1,name='Fixture',is_scratched=False,odds=[self.offer])
        self.payload=dict(success=True,data=[dict(venue='Fixture',country='AU',type='T',date='2026-11-25',
            races=[dict(number=1,jump_time=(self.now+timedelta(hours=1)).isoformat(),runners=[self.runner])])],meta={})

    def test_nested_capture_bound_to_first_selected_book_not_runner_or_other_offer(self):
        r=deepcopy(self.runner);r['captured_at']='unrelated'
        r['odds'].append(dict(bookmaker='Sportsbet',win=3,captured_at='unrelated'))
        evidence=quote_evidence(r)
        self.assertEqual(evidence['quote_timestamps'],[self.now.isoformat()])
        self.assertIn('NOT_BOOKMAKER_UPDATE',evidence['quote_time_basis'])
        r['odds'][0]['updated_at']=(self.now-timedelta(minutes=1)).isoformat()
        self.assertEqual(quote_evidence(r)['quote_timestamps'],[self.now.isoformat()])
        del r['odds'][0]['captured_at'];del r['odds'][0]['updated_at']
        self.assertEqual(quote_evidence(r)['quote_timestamps'],[])

    def test_fixed_price_unique_offer_binding_and_ambiguous_offer_rejection(self):
        r=dict(number=1,name='Fixture',fixed_win=3,fixed_win_bookmaker='Sportsbet',
            odds=[dict(bookmaker='Sportsbet',win=3,captured_at=self.now.isoformat())])
        self.assertEqual(quote_evidence(r)['quote_timestamps'],[self.now.isoformat()])
        r['odds'].append(dict(r['odds'][0],captured_at=(self.now-timedelta(seconds=1)).isoformat()))
        self.assertEqual(quote_evidence(r)['quote_timestamps'],[])

    def test_cache_never_resets_capture_or_quote_age_and_C_never_calls_fetch(self):
        calls=[]
        def fetch(*args,**kwargs):calls.append(args);return deepcopy(self.payload)
        batch=CaptureBatch(fetch,'fixture-not-a-secret',clock=lambda:self.now)
        for cmd in ('RM6','RM7','RM6PS','RM7PS','RM6 Fixture 1','RM7 Fixture 1'):
            p,at=batch.get('2026-11-25','AU',cmd);self.assertEqual(at,self.now)
        self.assertEqual(len(calls),1)
        with self.assertRaises(ValueError):batch.get('2026-11-25','AU','C')
        self.assertEqual(len(calls),1)
        self.now+=timedelta(seconds=300)
        batch.get('2026-11-25','AU','RM6 Fixture 1');self.assertEqual(len(calls),2)
        self.assertFalse(eligible(self.payload,self.now,self.now))  # Original offer is expired.

    def test_unknown_quote_times_do_not_get_cache_savings(self):
        self.offer.pop('captured_at');self.assertFalse(eligible(self.payload,self.now,self.now))
        self.offer['captured_at']='2026-11-25T07:00:00'  # no inferred UTC
        self.assertFalse(eligible(self.payload,self.now,self.now))

    def test_meter_records_only_safe_header_costs_unknown_is_not_zero(self):
        rows=[];record_usage(rows,'https://krokodds.com.au/api/v1/racing/meetings?private=never-log',200,
            {'X-Credits-Cost':'1','X-Credits-Remaining':'900','Authorization':'never-log'},'RM6',time.monotonic())
        record_usage(rows,'https://krokodds.com.au/api/v1/racing/meetings',503,{},'RM7',time.monotonic())
        summary=usage_summary(rows);self.assertEqual(summary['measured_credits'],1);self.assertEqual(summary['unknown_cost_attempts'],1)
        self.assertNotIn('never-log',json.dumps(rows))

    def test_dated_card_alias_keeps_strict_pagination_and_filters(self):
        body=json.dumps(dict(success=True,data=[],meta=dict(total=0,has_more=False))).encode()
        calls=[]
        def get(req,*args):calls.append(req.full_url);return body
        with patch.object(krok_adapter,'_fetch_body',side_effect=get):
            result=krok_adapter.fetch('2026-11-25','fixture',country='AU',dated_card=True)
        self.assertIn('/meetings/2026-11-25?',calls[0]);self.assertIn('country=AU',calls[0]);self.assertNotIn('?date=',calls[0])
        self.assertEqual(result['meta']['pages_fetched'],1)

    def test_append_only_history_and_conditional_headers_do_not_modify_pinned_sources(self):
        with TemporaryDirectory() as root:
            store=HistoryStore(root);a=store.update('official','race-1',b'original',observed_at=self.now.isoformat(),etag='v1')
            b=store.update('official','race-1',b'revision',observed_at=(self.now+timedelta(days=1)).isoformat(),etag='v2')
            self.assertNotEqual(a['sha256'],b['sha256']);self.assertEqual(len(list(Path(root).rglob('*.bin'))),2)
            self.assertEqual(store.conditional_headers(a),{});self.assertEqual(store.conditional_headers(a,permitted=True),{'If-None-Match':'v1'})
            blob=next(Path(root).rglob(a['sha256']+'.bin'));blob.write_bytes(b'changed')
            with self.assertRaises(ValueError):store.update('official','race-1',b'original',observed_at=self.now.isoformat())
        with self.assertRaises(ValueError):HistoryStore('monty_v6/results')

    def test_distinct_domains_or_matching_prices_do_not_establish_independence(self):
        self.assertFalse(independent_lineage({'collector':'Krok'},{'collector':'Other'}))
        a=dict(collector='one',upstream='shared',evidence_sha256='a'*64)
        b=dict(collector='two',upstream='shared',evidence_sha256='b'*64)
        self.assertFalse(independent_lineage(a,b));b['upstream']='separate'
        self.assertTrue(independent_lineage(a,b))  # Caller must authenticate evidence bytes.


if __name__=='__main__':unittest.main()
