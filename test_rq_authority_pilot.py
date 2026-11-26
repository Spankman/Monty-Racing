from types import SimpleNamespace
import unittest
from decimal import Decimal
import xml.etree.ElementTree as ET

from operations.audit.rq_authority_pilot import match_runner, parse_card


class AuthorityPilotTests(unittest.TestCase):
    def test_form_corroboration_and_current_day_leakage_are_separate(self):
        text = (
            "7/06/2025                Page 1 of 1\n"
            "1 11:08AM Open Handicap\n"
            "01. Sample Horse (BLKS)      (4) 56 Ms Example Rider (a2)\n"
            "1-12 E FM 1400 Soft6 7/06/2025 OPEN (Race 1)\n"
        )
        card, count = parse_card(text, "2025-06-07", "E FM")
        self.assertEqual(card[1], [(1,"samplehorse",4,Decimal(56),True)])
        self.assertEqual(count, 1)
        with self.assertRaises(ValueError):
            parse_card(text, "2025-06-08", "E FM")

    def test_name_collision_rejected_and_roles_verified_independently(self):
        row = SimpleNamespace(TAB_NUMBER=1, SELECTION_NAME="Sample Horse", barrier=3,
                              jockey="examplerider", trainer="exampletrainer")
        raw = ET.fromstring(
            '<Horse Id="11"><HorseName>Sample Horse</HorseName><Weight>56.0</Weight>'
            '<Jockey Id="33"><FullName>Ms Example Rider</FullName></Jockey>'
            '<Trainer Id="44"><FullName>Different Trainer</FullName></Trainer></Horse>'
        )
        card = {1: [(1,"samplehorse",4,Decimal(56),True)]}
        candidate = {"samplehorse":[raw]}
        self.assertEqual(match_runner(row,card,{"samplehorse":[raw,raw]})[1],
                         "authority_horse_name_missing_or_ambiguous")
        self.assertEqual(match_runner(row,{},candidate)[1],"booklet_saddlecloth_or_name")
        match, error = match_runner(row,card,candidate)
        self.assertIsNone(error)
        self.assertFalse(match["book_barrier_equal"])
        self.assertEqual(match["jockey_id"],"33")
        self.assertNotIn("trainer_id",match)
