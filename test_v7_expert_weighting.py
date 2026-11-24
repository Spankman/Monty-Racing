"""Synthetic policy fixtures only. Never used as racing evidence."""
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
import unittest

from v7 import expert_weighting as study


def card(index, day=None):
    cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(days=index if day is None else day)
    before = (cutoff - timedelta(minutes=1)).isoformat()
    item = dict(race_id=str(index), classification='benchmark', cutoff_at=cutoff.isoformat(),
                shared_model_input_sha256='c' * 64,
                scheduled_start=(cutoff + timedelta(minutes=2)).isoformat(),
                runners={'1': 'one', '2': 'two'}, odds={'1': 2.1, '2': 2.1},
                v7_feature_coverage=.8, odds_verified=True, odds_source='https://example.org/odds',
                odds_captured_at=before, model_captured_at={'v6': before, 'v7': before},
                model_artifacts={v: dict(model_sha256=h, forecast_sha256='b' * 64,
                                         forecast_url='https://example.org/test-forecast')
                                 for v, h in (('v6', study.V6_MODEL_SHA256), ('v7', study.V7_MODEL_SHA256))},
                models={'v6': {'1': .42, '2': .58}, 'v7': {'1': .40, '2': .60}})
    item['tips'] = [dict(author_id=key, independence_group=key, published_at=before, captured_at=before,
                         verified_at=before, number='1', horse='one', provenance_verified=True,
                         evidence_sha256=key * 64, source_url=f'https://example.org/tips/{key}',
                         independence_evidence=f'https://example.org/origin/{key}') for key in 'abcde']
    result = dict(race_id=str(index), official_verified=True, status='official_single_winner',
                  race_off_at=item['scheduled_start'], settled_at=(cutoff + timedelta(minutes=3)).isoformat(),
                  active_runners=['1', '2'], winner='1', source_url='https://example.org/test-result',
                  dividends={'win_tote': 2.2})
    return item, result


class ExpertWeightingTests(unittest.TestCase):
    def test_no_or_late_tips_fall_back_to_exact_v7(self):
        entry, _ = card(1)
        entry['tips'][1]['verified_at'] = entry['cutoff_at']
        f = study.forecast(entry, [], {})
        self.assertEqual((f['monty_pct'], f['expert_pct']), (100, 0))
        self.assertEqual(f['vectors']['dynamic'], f['vectors']['v7_unchanged'])
        self.assertEqual(f['expert_pct_by_arm']['fixed_20'], 0)

    def test_duplicate_authors_documents_and_editorial_groups_cannot_create_quorum(self):
        for field, value in (('author_id', ' A '), ('independence_group', 'a'),
                             ('evidence_sha256', 'a' * 64), ('source_url', 'https://example.org/tips/a')):
            with self.subTest(field=field):
                entry, _ = card(1)
                entry['tips'][1][field] = value
                self.assertIsNone(study.forecast(entry, [], {})['raw_consensus'])

    def test_policy_begins_at_ten_and_deterioration_reduces_weight(self):
        rows = []
        for i in range(100):
            item, result = card(i)
            f = study.forecast(item, [], {})
            f['vectors']['expert_consensus'] = {'1': .95, '2': .05}
            for w in study.WEIGHTS:
                f['vectors'][f'fixed_{w}'] = {'1': .48 + w / 100, '2': .52 - w / 100}
            rows.append((f, result))
        self.assertEqual(study.weight_decision(rows, None)[0], 10)
        self.assertEqual(study.weight_decision(rows, 10)[0], 15)
        self.assertEqual(study.weight_decision(rows, 20)[0], 20)
        for _, result in rows:
            result['winner'] = '2'
        weight, reason = study.weight_decision(rows, 15)
        self.assertLess(weight, 15)
        self.assertEqual(reason['reason'], 'DETERIORATION_REDUCED_WEIGHT')

    def test_future_or_late_recorded_settlement_cannot_train(self):
        entries, results = [], {}
        for i in range(100):
            entry, result = card(i)
            f = study.forecast(entry, [], {})
            result['recorded_at'] = card(110)[0]['cutoff_at']
            entries.append(f)
            results[result['race_id']] = result
        target, _ = card(101)
        f = study.forecast(target, entries, results)
        self.assertEqual(f['calibration_races'], 0)
        self.assertEqual(f['expert_pct'], 0)
        target, _ = card(111)
        f = study.forecast(target, entries, results)
        self.assertEqual(f['calibration_races'], 100)
        self.assertIn('expert_consensus', f['vectors'])
        self.assertEqual(f['expert_pct'], 0)

    def test_changed_field_and_unverified_market_excluded_from_comparison(self):
        entry, outcome = card(1)
        forecast = study.forecast(entry, [], {})
        outcome['active_runners'] = ['1']
        result = study.review([forecast], {'1': outcome}, card(2)[0]['cutoff_at'])
        self.assertEqual(result['settlement_exclusions'], {'invalid_or_changed_field': 1})
        self.assertIsNone(result['comparison']['fixed_10']['roi'])

    def test_ledger_is_write_once_and_hash_checked(self):
        item, _ = card(1)
        with TemporaryDirectory() as ledger:
            study.persist(ledger, item)
            self.assertEqual(study.load_records(ledger), [item])
            with self.assertRaises(FileExistsError):
                study.persist(ledger, item)


if __name__ == '__main__':
    unittest.main()
