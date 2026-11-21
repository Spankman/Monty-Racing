import unittest
from .value_watch import select_value_watch

def horse(n,p,odds):
    return {"number":str(n),"horse":f"Horse {n}","v7_win_probability":p,"fixed_win_odds":odds}

class ValueWatchTests(unittest.TestCase):
    def test_best_value_can_differ_from_best_chance(self):
        v=select_value_watch([horse(1,.45,2),horse(2,.18,8),horse(3,.12,6)])
        self.assertEqual(v["number"],"2")
        self.assertFalse(v["same_as_best_bet"])
        self.assertFalse(v["betting_authorised"])
    def test_no_positive_edge_is_no_candidate(self):
        self.assertIsNone(select_value_watch([horse(1,.45,2),horse(2,.1,8)]))
    def test_zero_edge_is_no_candidate(self):
        self.assertIsNone(select_value_watch([horse(1,.25,4)]))
    def test_empty_field(self):
        self.assertIsNone(select_value_watch([]))
    def test_invalid_inputs_rejected(self):
        for p,odds in [(0,5),(1,5),(-.1,10),(.2,1),(.2,float("nan")),(float("nan"),5)]:
            with self.subTest(p=p,odds=odds),self.assertRaises(ValueError):
                select_value_watch([horse(1,p,odds)])
if __name__=="__main__":
    unittest.main()
