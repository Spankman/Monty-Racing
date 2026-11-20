import unittest
from monty_single_race_ladder import choose, price_ladder

def field():
    return [
        {"number":5,"horse":"Favourite","research_prob":0.55,"odds":1.65},
        {"number":2,"horse":"Value","research_prob":0.28,"odds":4.2},
        {"number":7,"horse":"Other","research_prob":0.12,"odds":9.0},
        {"number":9,"horse":"Fourth","research_prob":0.05,"odds":25.0},
    ]

class TestLadder(unittest.TestCase):
    def test_win_price_progression(self):
        base = [{"number": str(i), "odds": odds} for i, odds in
                enumerate([4.0, 4.0, 4.0, 8.0], 1)]
        self.assertEqual(price_ladder(base)["bet_type"], "BB")
        base[0]["odds"] = 3.99
        self.assertEqual(price_ladder(base)["bet_type"], "QUINELLA BOXED")
        base[1]["odds"] = 3.99
        self.assertEqual(price_ladder(base)["bet_type"], "TRIFECTA BOXED")
        base[2]["odds"] = 3.99
        self.assertEqual(price_ladder(base)["bet_type"], "FIRST FOUR BOXED")
        self.assertEqual(len(price_ladder(base)["selections"]), 4)
    def test_research_only_never_bets(self):
        r=choose(field())
        self.assertFalse(r["bet_authorised"])
        self.assertEqual(r["selections"][0]["number"],"5")
    def test_short_price_top_runner_does_not_switch_to_second_best_win(self):
        r=choose(field(),approved=True)
        self.assertFalse(r["bet_authorised"])
        self.assertEqual(r["selections"][0]["number"],"5")
    def test_no_forced_exotic(self):
        r=choose(field(),approved=True,min_edge=0.9)
        self.assertFalse(r["bet_authorised"])
    def test_verified_quinella(self):
        q={"QUINELLA BOXED":{"verified":True,"calibrated_probability":0.2,"decimal_dividend":10}}
        r=choose(field(),approved=True,min_edge=0.9,exotic_quotes=q)
        self.assertEqual(r["bet_type"],"QUINELLA BOXED")
        self.assertEqual([x["number"] for x in r["selections"]],["5","2"])
    def test_invalid_probabilities_rejected(self):
        bad=field();bad[0]["research_prob"]=0.9
        with self.assertRaises(ValueError):choose(bad)
if __name__=="__main__":unittest.main()
