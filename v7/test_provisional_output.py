import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from monty_daily_price_ladder import format_daily
from v7.provisional_output import shortlist, write_single_race


class ProvisionalOutputTests(unittest.TestCase):
    def test_single_copy_matches_daily_in_model_rank_order(self):
        with TemporaryDirectory() as folder:
            output = Path(folder)
            original = output / "v7" / "provisional_selection.json"
            original.parent.mkdir()
            fields = ([4, 5, 6, 7], [2, 4, 5, 6], [2, 3, 4, 5], [2, 3, 3.5, 5])
            results = [
                dict(meeting="Example", race=race, betting_authorised=False, ordered=[
                    dict(number=number, horse=f"Runner {number}", fixed_win_odds=odds,
                         v7_win_probability=probability)
                    for number, odds, probability in zip((9, 2, 7, 1), prices, (0.4, 0.3, 0.2, 0.1))
                ]) for race, prices in enumerate(fields, 1)
            ]
            daily = format_daily([shortlist(result) for result in results])
            labels = ("BB", "Q (boxed)", "T (boxed)", "FF (boxed)")
            for count, (result, label) in enumerate(zip(results, labels), 1):
                content = json.dumps(result)
                original.write_text(content)
                write_single_race(output)
                single = json.loads((output / "selection.json").read_text())
                copy = single["copy_text"]
                block = copy.split("\n\n", 1)[1].strip()
                self.assertIn(block, daily)
                self.assertIn(f"{label} assessment · NO BET", block)
                self.assertEqual([line.split("#")[1].split()[0] for line in block.splitlines()
                                  if line.startswith("-")], ["9", "2", "7", "1"][:count])
                self.assertEqual(copy, (output / "selection.md").read_text())
                self.assertEqual(original.read_text(), content)
                self.assertFalse(single["betting_authorised"])
