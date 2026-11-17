import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from intake_only import capture

class IntakeChecks(unittest.TestCase):
    def fixture(self):
        from test_krok_adapter import KrokAdapterTests
        return KrokAdapterTests().fixture()

    def test_missing_key_never_fetches(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True), patch('intake_only.fetch') as fetch:
            with self.assertRaisesRegex(ValueError, 'absent'):
                capture('2026-11-14', tmp)
            fetch.assert_not_called()
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_fixture_label_and_unique_captures(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture=Path(tmp)/'fixture.json'
            fixture.write_text(json.dumps(self.fixture()))
            a,report=capture('2026-11-14',tmp,fixture)
            b,_=capture('2026-11-14',tmp,fixture)
            self.assertNotEqual(a,b)
            self.assertFalse(report['live'])
            self.assertFalse(report['predictions_generated'])
            self.assertFalse(report['betting_ready'])
            self.assertEqual(report['artifact_hashes'],55)
            self.assertEqual(report['active_feature_coverage']['observed_win_rate']['status'],'missing')
            self.assertEqual({p.name for p in a.iterdir()}, {'provider_response.json','snapshot.json','intake_report.json','assessment_bundle.json'})

    def test_live_mock_redacts_credential(self):
        payload=self.fixture();payload['meta']['echo']='dummy-secret-test-value'
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{'KROK_API_KEY':'dummy-secret-test-value'}), patch('intake_only.fetch',return_value=payload):
            out,report=capture('2026-11-14',tmp)
            self.assertTrue(report['live'])  # mocked call; this test is not proof of real API access.
            for p in out.iterdir():
                self.assertNotIn('dummy-secret-test-value',p.read_text())

if __name__=='__main__':unittest.main()
