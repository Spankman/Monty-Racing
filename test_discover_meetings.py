import unittest
from discover_meetings import discover
class Tests(unittest.TestCase):
 def test_meetings(self):
  html='<table><tr><th>Sat 14 Nov 2026</th></tr><tr><td>ASCOT</td><td>10</td></tr><tr><td>RICCARTON PARK - NZ</td><td>12</td></tr><tr><td>CANNINGTON</td><td>8</td></tr><tr><td>CHELTENHAM - ENG</td><td>7</td></tr></table>'
  r=discover(html,'2026-11-14');self.assertEqual(len(r),4);self.assertEqual(r[1]['country'],'NZ');self.assertEqual(r[2]['status'],'excluded_other_code');self.assertEqual(r[3]['status'],'excluded_foreign')
 def test_wrong_date(self):
  with self.assertRaises(ValueError):discover('<h3>Sun 15 Nov 2026</h3>','2026-11-14')
if __name__=='__main__':unittest.main()
