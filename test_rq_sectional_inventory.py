import unittest

from operations.audit.rq_sectional_inventory import inventory


class SectionalInventoryTests(unittest.TestCase):
    def setUp(self):
        self.header = b'Date,RaceNumber,21/11/2026 12:00:00 AM;QLD fixture;Race, Example;00:01:26.178;SCTC_1400m_TRACK\n'
        self.first = b'21/11/2026,1,A Horse;6;200;18.18;00:00:13.66;400;0;00:00:00.000\n'
        self.second = b'21/11/2026,1,B Horse;7;200;0;00:00:00.000\n'

    def test_preserves_missing_measurement_counts(self):
        result = inventory(self.header + self.first + self.second)
        self.assertEqual(result['segments'], 1)
        self.assertEqual(result['missing_segments'], 2)
        self.assertEqual(result['runner_rows_without_measurements'], 1)
        self.assertFalse(result['used_in_model'])

    def test_rejects_duplicate_wrong_date_and_conflicting_zero(self):
        for bad in (self.first, self.second.replace(b'21/11', b'22/11'),
                    self.second.replace(b';0;', b';2;')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                inventory(self.header + self.first + bad)
