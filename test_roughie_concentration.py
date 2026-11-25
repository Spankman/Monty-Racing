from datetime import datetime, timedelta, timezone
from copy import deepcopy
import unittest

from operations.audit.roughie_concentration import audit_forecast
from operations.audit.verification import reconcile


class RoughieAuditTests(unittest.TestCase):
    def test_underround_reproduces_edge_without_runner_uplift(self):
        rows = [dict(number=1, horse='Short', odds=2, probability=5/6),
                dict(number=2, horse='Long', odds=10, probability=1/6)]
        model = dict(status='SCORED', ranked_runners=rows, roughies=rows[1:])
        race = dict(meeting='Fixture', race='1', data_completeness={'active_runners': 2},
                    models={'V6': model, 'V7': model})
        books, comparisons = audit_forecast({'races': [race]})
        self.assertEqual(books[0]['book_pct'], 60)
        self.assertAlmostEqual(comparisons[1]['V6_uplift_pp'], 0)
        self.assertAlmostEqual(comparisons[1]['V6_edge'], 2/3)
        self.assertTrue(comparisons[1]['V7_market_only_watch'])
        race['data_completeness']['active_runners'] = 3
        books, comparisons = audit_forecast({'races': [race]})
        self.assertIsNone(books[0]['book_pct'])
        self.assertIsNone(comparisons[1]['market_probability'])
        race['scratchings'] = [{'number': '2'}]
        with self.assertRaises(ValueError):
            audit_forecast({'races': [race]})

    def test_quote_verification_blocks_mixed_missing_stale_and_moved_prices(self):
        now = datetime(2026, 11, 25, 5, tzinfo=timezone.utc)
        provider = dict(lineage='Provider', observed_at=now,
                        race_key=('AU', '2026-11-25', 'Fixture', 1),
                        status='open', distance_m=1200, condition='Soft 5', surface='turf',
                        scheduled_start=now+timedelta(hours=1),
                        runners=[(1, 'A', False), (2, 'B', False)],
                        quotes={1: ('2.00', 'TAB'), 2: ('10.00', 'TAB')})
        authority = dict(provider, lineage='Racing authority')
        operator = dict(deepcopy(provider), lineage='Direct', market='fixed_win', bookmaker='TAB')

        def verified(p):
            return reconcile(p, authority, operator, decision_at=now,
                             max_age=timedelta(minutes=5))['fixed_win_verified']

        self.assertTrue(verified(provider))
        for quotes in ({1: ('2.00', 'TAB')}, {1: ('2.00', 'TAB'), 2: ('10.00', 'Other')},
                       {1: ('2.00', 'TAB'), 2: ('11.00', 'TAB')}):
            self.assertFalse(verified(dict(provider, quotes=quotes)))
        self.assertFalse(verified(dict(provider, observed_at=now-timedelta(minutes=5))))
        self.assertFalse(verified(dict(provider, runners=[(1, 'A', False), (2, 'B', True)])))
