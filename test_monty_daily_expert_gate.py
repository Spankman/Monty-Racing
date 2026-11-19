import unittest
from pathlib import Path

class DailyExpertGateTests(unittest.TestCase):
 def test_raw_tips_must_pass_ingestion(self):
  workflow=Path('.github/workflows/monty-daily-research.yml').read_text()
  self.assertIn('if [ -f expert_tips_raw.csv ]; then',workflow)
  self.assertIn('python expert_tip_ingest.py research_scores.csv expert_tips_raw.csv',workflow)
  self.assertIn('if [ -f expert_tips_validated.csv ]; then',workflow)
  self.assertIn('python monty_v7_shadow_blend.py research_scores.csv --output v7_shadow.csv',workflow)
  self.assertNotIn('expert_tips_verified.csv',workflow)
if __name__=='__main__':unittest.main()
