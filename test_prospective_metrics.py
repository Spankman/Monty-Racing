from datetime import timedelta
import json
import unittest

from operations.audit.prospective_metrics import report
from operations.prospective import freeze, settle
import test_verification_integration as fixtures


class ProspectiveMetricsTests(unittest.TestCase):
    setUp = fixtures.IntegrationTests.setUp
    run_it = fixtures.IntegrationTests.run_it
    scorer = fixtures.IntegrationTests.scorer
    verified_fixture = fixtures.IntegrationTests.verified_fixture

    def test_only_admitted_settlements_count_and_prices_are_proxies(self):
        f, race, evidence = self.verified_fixture()
        path = self.root / 'frozen.json'
        settled = self.root / 'settled.json'
        record = freeze(f, race, evidence, path, self.now)
        post_jump = self.now + timedelta(hours=2)
        key = {field: record[field] for field in ('date', 'country', 'meeting', 'race')}
        official = dict(key, official=True, status='FINAL', late_field_change=False,
                        observed_at=post_jump.isoformat(), winners=['1'],
                        active_runners={r['number']: r['horse'] for r in record['market_baseline']},
                        source_url='https://www.racingqueensland.com.au/fixture-only',
                        source_sha256='a'*64)
        first=settle(path, official, settled, post_jump)
        original=settled.read_bytes()
        repeated=settle(path, official, settled, post_jump+timedelta(minutes=1))
        self.assertEqual(first,repeated)
        self.assertEqual(original,settled.read_bytes())
        with self.assertRaisesRegex(ValueError,'Conflicting settlement'):
            settle(path,dict(official,winners=['2']),settled,post_jump)
        self.assertEqual(original,settled.read_bytes())
        entry = dict(key, forecast=str(path), settlement=str(settled))
        missing = dict(key, race='99', reason='quotes unavailable')
        window = dict(start=self.now.isoformat(), end=post_jump.isoformat())
        output = report([entry, missing], **window)
        self.assertEqual(output['counts'], {'registered': 2, 'unavailable': 1, 'admitted': 1, 'settled': 1})
        self.assertIsNone(output['actual_roi'])
        self.assertEqual(output['models']['V6']['top_pick_fixed_quote_proxy_roi'], 1)
        self.assertIsNone(output['models']['V6']['paired_log_loss_day_bootstrap_95'])
        self.assertEqual(output['models']['MARKET']['paired_log_loss_delta_vs_market'], 0)
        tampered = json.loads(settled.read_text())
        tampered['metrics']['V6']['log_loss'] += 1
        settled.write_text(json.dumps(tampered))
        with self.assertRaisesRegex(ValueError,'Settlement integrity'):
            settle(path,official,settled,post_jump)
        with self.assertRaisesRegex(ValueError, 'metric mismatch'):
            report([entry], **window)
        with self.assertRaisesRegex(ValueError, 'Duplicate race'):
            report([missing, missing], **window)

    def test_excluded_diagnostic_cannot_be_counted_as_settled(self):
        f, race, _ = self.verified_fixture()
        path = self.root / 'unverified.json'
        record = freeze(f, race, {}, path, self.now)
        key = {field: record[field] for field in ('date', 'country', 'meeting', 'race')}
        entry = dict(key, forecast=str(path))
        window = dict(start=self.now.isoformat(), end=(self.now + timedelta(hours=2)).isoformat())
        result = report([entry], **window)
        self.assertEqual(result['counts'], {'registered': 1, 'excluded': 1})
        self.assertEqual(result['models'], {})
        with self.assertRaisesRegex(ValueError, 'Excluded diagnostics'):
            report([dict(entry, settlement='unverified-result.json')], **window)
