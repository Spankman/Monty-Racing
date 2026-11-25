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

    def test_same_race_rejects_contradictory_attributes_and_repeated_registration(self):
        cutoff=datetime(2026,11,25,5,tzinfo=timezone.utc)
        race=('AU-QLD','2026-11-25','Ipswich',4,2150)
        a=Evidence('authority','registered-1',race,1,'Fixture',cutoff,'authority hash',birth_year=2022,sex='gelding')
        b=replace(a,source='Betfair',source_id='selection-1',reference='exchange hash')
        for change in [dict(birth_year=2021),dict(sex='mare')]:
            links,blocked=resolve([a],[replace(b,**change)],cutoff)
            self.assertFalse(links);self.assertTrue(any(x[-1]=='conflicting_identity_attributes' for x in blocked))
        a2=replace(a,saddlecloth=2);b2=replace(b,saddlecloth=2,source_id='selection-2')
        links,blocked=resolve([a,a2],[b,b2],cutoff)
        self.assertFalse(links);self.assertTrue(any(x[-1]=='same_registration_twice_in_race' for x in blocked))
