import unittest

from operations.public_sources import rq_scratchings


class RaceScratchingPanelTests(unittest.TestCase):
    def panel(self, entries, race=7):
        runners = ''.join(f'<span class="c-race-stratchings__horse">{entry}</span>' for entry in entries)
        return ('<a>Scratchings</a><div data-js-expandable="RaceDetailsScratchings">'
                f'<div class="c-race-scratchings__race"><span class="c-race-scratchings__race-number">{race}</span>'
                f'<div class="c-race-scratchings__horses">{runners}</div></div></div>'
                '<a>Stewards Summary</a><aside>Late Scratchings</aside>').encode()

    def test_race_local_rows_survive_repeated_labels(self):
        self.assertEqual([x['number'] for x in rq_scratchings(self.panel(['2. A Horse', '3. Other']), 7)], ['2', '3'])

    def test_empty_wrong_and_duplicate_rows_fail_closed(self):
        for body in (self.panel([]), self.panel(['2. A', '2. B']), self.panel(['2. A'], race=6),
                     self.panel(['Unrelated text'])):
            with self.subTest(body=body), self.assertRaises(ValueError):
                rq_scratchings(body, 7)
