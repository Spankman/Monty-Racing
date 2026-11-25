import unittest

from operations.audit.approval_research import assess


class ApprovalResearchTests(unittest.TestCase):
    def test_genuine_negative_value_and_incomplete_data_are_distinct(self):
        prices = {1: 1.8, 2: 1.8}
        entries = [dict(number=i, fixed_win=1.8, price_floor=1.75,
                        probability_bounds=(.48, .5, .52)) for i in prices]
        self.assertEqual(assess('V6', 'SCORED', prices, [], entries)['decision'], 'NO BET')
        self.assertEqual(assess('V6', 'SCORED', prices, ['going'], entries)['decision'], 'DATA BLOCKED')
        self.assertEqual(assess('V6', 'SCORED', prices, [], entries[:1])['decision'], 'DATA BLOCKED')
        self.assertEqual(assess('V6', 'FAILED', prices, [], entries)['decision'], 'EXECUTION FAILED')
        self.assertEqual(assess('V7', 'SCORED', prices, [], entries)['decision'], 'RESEARCH ONLY')

    def test_positive_interval_remains_provisional(self):
        prices = {1: 4., 2: 1.5}
        entries = [dict(number=1, fixed_win=4., price_floor=3.5, probability_bounds=(.30, .35, .40)),
                   dict(number=2, fixed_win=1.5, price_floor=1.45, probability_bounds=(.60, .65, .70))]
        result = assess('V6', 'SCORED', prices, [], entries)
        self.assertEqual(result['decision'], 'PROVISIONAL')
        self.assertEqual(result['positive_lower_bound'], [1])
        self.assertFalse(result['betting_authorised'])
        entries[0]['price_floor'] = 3.
        self.assertEqual(assess('V6', 'SCORED', prices, [], entries)['positive_lower_bound'], [])

    def test_expiry_and_missing_bounds_never_become_no_bet(self):
        rows = [dict(number=1, fixed_win=1.8), dict(number=2, fixed_win=1.8)]
        self.assertEqual(assess('V6', 'EXPIRED', {}, [], [])['decision'], 'EXPIRED')
        result = assess('V6', 'SCORED', {1: 1.8, 2: 1.8}, [], rows)
        self.assertEqual(result['decision'], 'DATA BLOCKED')
        self.assertIn('invalid_calibration_or_executable_price', result['blockers'])
