import unittest
from unittest.mock import patch
import monty_poll_race_requests as m

class TestPoll(unittest.TestCase):
    def test_title(self):
        self.assertEqual(m.TITLE.fullmatch("Monty race: Grafton 5").groups(),("Grafton","5"))
        self.assertIsNone(m.TITLE.fullmatch("Monty race: Grafton 0"))
        self.assertIsNone(m.TITLE.fullmatch("Monty race: Grafton 5; echo hacked"))
    @patch.object(m,"gh")
    def test_marker_prevents_duplicate(self,gh):
        gh.return_value='[{"body":"<!-- monty-race-request-v1 --> done"}]'
        self.assertTrue(m.already_handled(21))
    @patch.object(m,"gh")
    def test_no_marker_means_pending(self,gh):
        gh.return_value='[{"body":"hello"}]'
        self.assertFalse(m.already_handled(21))
if __name__=="__main__":unittest.main()
