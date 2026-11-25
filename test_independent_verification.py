from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from operations.audit.verification import reconcile


class IndependentVerificationTests(unittest.TestCase):
    def test_declared_field_and_exact_named_quote_reconciliation(self):
        now = datetime(2026, 11, 24, 23, tzinfo=timezone.utc)
        provider = dict(lineage='Krok', observed_at=now,
                        race_key=('AU', '2026-11-25', 'Ipswich', 5),
                        status='open', distance_m=1100, condition='Soft 5', surface='turf',
                        scheduled_start=now+timedelta(hours=1),
                        runners=[(1, 'Example Horse', False), (2, 'Withdrawal', True)],
                        quotes={1: ('4.00', 'TAB')})
        authority = dict(provider, lineage='Racing Queensland')
        operator = dict(provider, lineage='TAB direct', market='fixed_win', bookmaker='TAB')

        def check(a, o):
            return reconcile(provider, a, o, decision_at=now, max_age=timedelta(minutes=5))

        self.assertEqual(check(authority, operator)['blockers'], [])
        changed = deepcopy(operator)
        changed['quotes'][1] = ('4.10', 'TAB')
        self.assertTrue(check(authority, changed)['race_verified'])
        self.assertFalse(check(authority, changed)['fixed_win_verified'])
        withdrawn = dict(authority, runners=[(1, 'Example Horse', True), (2, 'Withdrawal', True)])
        self.assertIn('field_or_scratching_mismatch', check(withdrawn, operator)['blockers'])
        stale = dict(authority, observed_at=now-timedelta(minutes=5))
        self.assertFalse(check(stale, operator)['race_verified'])
        self.assertFalse(check(dict(authority, status='abandoned'), operator)['race_verified'])
        same_feed = check(authority, dict(operator, lineage='Krok'))
        self.assertTrue(same_feed['race_verified'])
        self.assertFalse(same_feed['fixed_win_verified'])
        self.assertFalse(check(dict(authority, condition=None), operator)['race_verified'])
