import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from monty_operations import command, timestamp
from operations import ingress, issue_delivery, transport


def opened(title, body='', author='Spankman'):
    return dict(number=194, title=title, body=body, created_at='2026-11-24T15:00:00Z',
                user={'login': author}, state='open')


class IngressContracts(unittest.TestCase):
    def test_incidents_and_plain_requests(self):
        for title, body in [('Monty command: RM6 Tamworth 7', 'RM6 Tamworth 7'),
                            ('RM6 Tamworth 7', '{"date":"2026-11-25","country":"AU"}'),
                            ('Please run Monty for Tamworth Race 7', ''), ('Tamworth R7', None)]:
            with self.subTest(title=title):
                req = transport.parse_request(opened(title, body))
                self.assertEqual((req['command'], req['country'], req['date']),
                                 ('RM6 TAMWORTH 7', 'AU', '2026-11-25'))
        for name in ('RM6', 'RM7', 'RM6PS', 'RM7PS'):
            self.assertEqual(transport.parse_request(opened(name))['command'], name)

    def test_fast_ingress_validation(self):
        for title, body, phases, route in [
            ('Bug report', '', [], ''),
            ('RM8', '', ['ack', 'terminal'], ''),
            ('RM6 Tamworth 7', 'RM7 Tamworth 7', ['ack', 'terminal'], ''),
            ('RM6', '{"country":true}', ['ack', 'terminal'], ''),
            ('RM6 Tamworth 7', None, ['ack'], 'route=true\n'),
        ]:
            with self.subTest(title=title, body=body), TemporaryDirectory() as tmp:
                event = Path(tmp) / 'event.json'
                event.write_text(json.dumps({'issue': opened(title, body)}))
                output = Path(tmp) / 'output'
                output.touch()
                with patch.dict('os.environ', GITHUB_EVENT_PATH=str(event), GITHUB_OUTPUT=str(output),
                                GITHUB_RUN_ID='1'), patch.object(issue_delivery, 'report', return_value=True) as report:
                    ingress.main()
                self.assertEqual([call.args[1] for call in report.call_args_list], phases)
                self.assertEqual(output.read_text(), route)

    def test_untrusted_author_is_not_routed(self):
        self.assertIsNone(transport.parse_request(opened('RM6 Tamworth 7', author='external')))

    def test_recent_reuse_requires_live_scoring_and_fresh_capture(self):
        req = command('RM7 Tamworth 7')
        index = dict(request_status='COMPLETED', source_mode='LIVE', provider='PuntersEdge', forecast_path='path',
                     captured_at='2026-11-24T03:00:00Z', models={'V7': {'scored_races': 1}})
        self.assertTrue(transport.reusable(index, req, timestamp('2026-11-24T03:01:00Z')))
        self.assertFalse(transport.reusable(dict(index,provider='Krok'), req, timestamp('2026-11-24T03:01:00Z')))
        self.assertFalse(transport.reusable(index, req, timestamp('2026-11-24T03:01:31Z')))
        self.assertFalse(transport.reusable(dict(index, models={}), req, timestamp('2026-11-24T03:01:00Z')))
