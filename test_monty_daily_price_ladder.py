import unittest
from monty_daily_price_ladder import format_daily

def r(n,odds):
    return {"number":n,"horse":f"Horse {n}","odds":odds}

class DailyPriceLadderTests(unittest.TestCase):
    def test_groups_and_ladder(self):
        rows=[
            {"meeting":"Pakenham","race":8,"qualified":True,"ranked":[r(2,2.2),r(10,5.5),r(12,5.5)]},
            {"meeting":"Doomben","race":5,"qualified":True,"ranked":[r(1,3),r(2,3.5),r(3,4.1),r(4,2)]},
            {"meeting":"Pakenham","race":3,"qualified":True,"ranked":[r(7,4.0),r(8,3)]},
            {"meeting":"Doomben","race":2,"qualified":False,"ranked":[r(9,2)]},
        ]
        result=format_daily(rows)
        self.assertIn("R8 · Unverified · Q (boxed) assessment · NO BET\n\n"
                      "- **Best Bet · #2 Horse 2 $2.20**\n- #10 Horse 10 $5.50", result)
        self.assertIn("R5 · Unverified · T (boxed) assessment · NO BET\n\n"
                      "- **Best Bet · #1 Horse 1 $3.00**\n- #2 Horse 2 $3.50\n- #3 Horse 3 $4.10", result)
        self.assertIn("R3 · Unverified · BB assessment · NO BET\n\n"
                      "- **Best Bet · #7 Horse 7 $4.00**", result)
        self.assertNotIn("#4 Horse 4", result)
        self.assertNotIn("R2",result)
        self.assertLess(result.index("R3"),result.index("R8"))
    def test_unqualified_never_promoted(self):
        self.assertEqual("",format_daily([{"meeting":"A","race":1,"qualified":False,"ranked":[r(1,2)]}]))
if __name__=="__main__":
    unittest.main()
