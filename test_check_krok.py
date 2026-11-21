"""Offline regression checks for safe Krok connection failure diagnostics."""
import contextlib
import io
import os
import unittest
from unittest.mock import patch

import check_krok


class ConnectionDiagnosticTests(unittest.TestCase):
    def run_case(self, error, key='placeholder-test-key'):
        output = io.StringIO()
        with patch.dict(os.environ, {'KROK_API_KEY': key}, clear=False), \
             patch('check_krok.check', side_effect=error), \
             patch('sys.argv', ['check_krok.py', '--date', '2026-11-21']), \
             contextlib.redirect_stdout(output):
            status = check_krok.main()
        return status, output.getvalue()

    def test_missing_key_is_classified_without_leakage(self):
        status, output = self.run_case(ValueError('secret'), key='')
        self.assertEqual(status, 2)
        self.assertIn('missing_api_key', output)
        self.assertNotIn('secret', output)

    def test_provider_validation_is_classified_without_payload(self):
        status, output = self.run_case(ValueError('sensitive provider response'))
        self.assertEqual(status, 2)
        self.assertIn('provider_input_validation', output)
        self.assertNotIn('sensitive provider response', output)

    def test_pagination_is_classified(self):
        status, output = self.run_case(ValueError('Meeting feed paginated/truncated'))
        self.assertEqual(status, 2)
        self.assertIn('incomplete_pagination', output)

    def test_duplicate_is_classified(self):
        status, output = self.run_case(ValueError('Duplicate meeting/race identity in provider feed'))
        self.assertEqual(status, 2)
        self.assertIn('duplicate_race_identity', output)


if __name__ == '__main__':
    unittest.main()
