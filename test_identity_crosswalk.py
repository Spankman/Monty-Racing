from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from operations.audit.identity_crosswalk import Evidence, resolve


class CrosswalkTests(unittest.TestCase):
    def test_exact_race_identity_cutoff_and_collision(self):
        cutoff = datetime(2026, 11, 25, 5, tzinfo=timezone.utc)
        race = ('AU-QLD', '2026-11-25', 'Ipswich', 5, 1666)
        authority = Evidence('authority', 'registered-1', race, 3, 'Example Horse', cutoff, 'authority capture')
        betfair = replace(authority, source='Betfair', source_id='exchange-1', reference='exchange capture')
        krok = replace(authority, source='Krok', source_id='entry-1', reference='provider capture')
        self.assertEqual(len(resolve([authority], [betfair, krok], cutoff)[0]), 2)
        for other in (replace(krok, race=(*race[:-1], 1600)),
                      replace(krok, saddlecloth=4), replace(krok, horse='Different Horse'),
                      replace(krok, observed_at=cutoff + timedelta(seconds=1))):
            self.assertFalse(resolve([authority], [other], cutoff)[0])
        self.assertFalse(resolve([authority], [krok, krok], cutoff)[0])
        authority2 = replace(authority, source_id='registered-2', saddlecloth=4)
        betfair2 = replace(betfair, saddlecloth=4)
        links, blockers = resolve([authority, authority2], [betfair, betfair2], cutoff)
        self.assertFalse(links)
        self.assertEqual(sum(b[-1] == 'conflicting_registration' for b in blockers), 2)
