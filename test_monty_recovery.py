"""Operational regressions. Hosted acceptance runs use live providers separately."""
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from monty_operations import command, freshness, projection, selection, utcnow
from operations.combined import combined_ticket
from puntersedge_adapter import fetch_board


class RecoveryTests(unittest.TestCase):
    def test_dated_card_and_rolling_board_reconcile_per_race(self):
        from monty_operations import TZ

        now = datetime(2026, 11, 27, 1, tzinfo=timezone.utc)
        day = now.astimezone(TZ).date().isoformat()
        jump = (now + timedelta(minutes=15)).isoformat()
        provider_runners = [
            dict(number=i, name=f'Horse {i}', bookmakers=[
                dict(key='tab', win_price=4+i, age_basis='poll',
                     last_update=(now-timedelta(seconds=30)).isoformat())
            ]) for i in (1, 2, 3)
        ]
        declared = [dict(number=i, runner_name=f'Horse {i}', scratched=False, emergency=False, age=4)
                    for i in (1, 2, 3)]
        meeting = dict(venue='Example', venue_id='example', races=[
            dict(race_number=1, runners=declared, runner_set_status='checks_passed'),
            dict(race_number=2, runners=declared, runner_set_status='gap_detected'),
            dict(race_number=3, runners=declared, runner_set_status='checks_passed'),
        ])
        board = [dict(venue='Example', venue_id='example', country='AU', category='horse',
                      race_number=n, start_time=jump, runners=provider_runners)
                 for n in (1, 2)]
        with patch('puntersedge_adapter.Client') as client:
            client.return_value.get.side_effect = [
                dict(date=day, meetings=[meeting], meeting_count=1, race_count=3), board
            ]
            payload, received_at = fetch_board(day, 'unused', clock=lambda: now)
        self.assertEqual(received_at, now)
        race = payload['data'][0]['races'][0]
        self.assertEqual(race['number'], 1)
        self.assertEqual(race['runners'][0]['age'], 4)
        self.assertEqual(race['quote_observed_at'], (now-timedelta(seconds=30)).isoformat())
        self.assertEqual(payload['meta']['discovered_races'], 3)
        self.assertEqual(len(payload['meta']['acquisition_skips']), 2)
        self.assertIn('field gap', payload['meta']['acquisition_skips'][0])
        self.assertIn('absent', payload['meta']['acquisition_skips'][1])

    def test_provisional_is_distinct_and_combined_keeps_one_roughy(self):
        now = utcnow()
        rows = [dict(number='1', horse='One', odds=3., probability=.50),
                dict(number='2', horse='Two', odds=8., probability=.26),
                dict(number='3', horse='Three', odds=10., probability=.24)]
        model = dict(selection(rows), status='SCORED', no_bet_reasons=['verification missing'])
        race = dict(meeting='Example', race='4', country='AU', captured_at=now.isoformat(),
                    scheduled_start=(now+timedelta(minutes=2)).isoformat(),
                    models={'V6': model, 'V7': model})
        forecast = dict(provider='PuntersEdge', races=[race], date='2026-11-27',
                        run_id='test', status='DATA_BLOCKED')
        official = projection(forecast, command('RM6', '2026-11-27'), now)
        provisional = projection(forecast, command('RM6PS', '2026-11-27'), now)
        self.assertIn('DATA BLOCKED', official['status'])
        self.assertEqual(official['races'][0]['result']['ordered_selections'], [])
        self.assertEqual(provisional['status'], 'PROVISIONAL ASSESSMENTS')
        self.assertEqual(len(model['roughies']), 1)
        combined = combined_ticket(forecast, now)
        self.assertEqual(len(combined['races']), 1)
        result = combined['races'][0]['result']
        self.assertEqual([row['number'] for row in result['ordered_selections']], ['1', '2'])
        self.assertEqual([row['number'] for row in result['roughies']], ['3'])
        freeze = now + timedelta(minutes=1)
        self.assertIn('CLOSED', freshness(race, freeze))
        self.assertEqual(combined_ticket(forecast, freeze)['races'], [])
