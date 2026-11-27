"""Offline authority regressions; synthetic transport is not live verification."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from operations.public_sources import rq_declaration, AuthorityDependencyError
from operations.rq_verification import capture_races

HTML=b'<h2>Rockhampton 26 Nov 2026 1.30pm 1800m</h2><p>Soft 6 Turf</p>'
SCR=HTML+b'<h3>Scratchings</h3><p>2. Second</p><h3>Other</h3>'
PDF=b'Rockhampton Thursday 26 November, 2026\n2 BENCHMARK HANDICAP\n1800 metres\n01 First(Trainer One) Rider\n02 Second(Trainer Two) Rider\n03 Third(Trainer Three) Rider\n'

class AuthorityRecoveryTests(unittest.TestCase):
    def test_separate_scratching_page_preserves_race_local_metadata(self):
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=PDF)):
            result=rq_declaration(HTML,b'%PDF','2026-11-26','Rockhampton',2,scratchings_body=SCR)
        self.assertEqual(result['distance_m'],1800)
        self.assertEqual([r['number'] for r in result['runners'] if r['scratched']],['2'])

    def test_missing_decoder_has_actionable_dependency_diagnostic(self):
        with patch('subprocess.run',side_effect=FileNotFoundError),self.assertRaisesRegex(AuthorityDependencyError,'poppler-utils'):
            rq_declaration(HTML,b'%PDF','2026-11-26','Rockhampton',2)

    def test_missing_scratching_evidence_remains_blocked(self):
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=PDF)),self.assertRaisesRegex(ValueError,'scratching section'):
            rq_declaration(HTML,b'%PDF','2026-11-26','Rockhampton',2)

    def test_batch_deduplicates_races_meeting_and_pdf(self):
        calls=[]
        def fetch(url,directory):
            calls.append(url)
            body=(b'%PDF' if url.endswith('.pdf') else
                  HTML+b'<a href="/fields.pdf">Race Fields PDF</a>' if '/race/' in url else SCR)
            return {'url':url},body
        with patch('operations.rq_verification.rq_declaration',return_value={'field_verified':True,'emergency_status_verified':False}):
            rows=capture_races('2026-11-26',[2,2,3],'.',fetch,meeting='Rockhampton',meeting_code='rock')
        self.assertEqual(len(rows),2)
        self.assertEqual(len(calls),4)
        self.assertFalse(any(r['verified'] for r in rows))

    def test_unknown_authority_mapping_never_fetches(self):
        with self.assertRaisesRegex(ValueError,'mapping'):
            capture_races('2026-11-26',[1],'.',meeting='Other',meeting_code='other')

    def test_mixed_case_and_numeric_title_keep_exact_race_boundary(self):
        pdf=(b'Rockhampton Thursday 26 November, 2026\n2 Mixed Case Handicap\n$21000\n1800 metres 1:30PM\n'
             b'01 First(Trainer One) Rider\n02 Second(Trainer Two) Rider\n'
             b'3 102.7 Station Handicap\n$21000\n1200 metres 2:00PM\n01 Other(Trainer Three) Rider\n')
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=pdf)):
            result=rq_declaration(HTML,b'%PDF','2026-11-26','Rockhampton',2,scratchings_body=SCR)
        self.assertEqual([r['horse'] for r in result['runners']],['First','Second'])
