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
        self.assertIn("R8 — Q (boxed): **#2 Horse 2** → #10 Horse 10",result)
        self.assertIn("R5 — T (boxed): **#1 Horse 1** → #2 Horse 2 → #3 Horse 3",result)
        self.assertIn("R3 — BB: **#7 Horse 7**",result)
        self.assertNotIn("R2",result)
        self.assertLess(result.index("R3"),result.index("R8"))
    def test_unqualified_never_promoted(self):
        self.assertEqual("",format_daily([{"meeting":"A","race":1,"qualified":False,"ranked":[r(1,2)]}]))
if __name__=="__main__":
    unittest.main()
