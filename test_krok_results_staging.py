import unittest
from krok_results_staging import inspect

class HistoricalStagingTests(unittest.TestCase):
    def test_preserves_unverified_provenance(self):
        payload={'data':[{'runners':[{'entry_id':'e1','name':'Runner A','barrier':3,
            'finish_position':1,'starting_price':4.5,'jockey':'J Smith'},
            {'entry_id':'e2','name':'Runner B','is_scratched':True}]}]}
        rows,audit=inspect(payload,'2026-11-20')
        self.assertEqual(audit['races'],1)
        self.assertEqual(audit['scratched'],1)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['finish_position'],1)
        self.assertFalse(rows[0]['identity_crosswalk_verified'])
        self.assertFalse(rows[0]['scheduled_off_quote_verified'])
        self.assertFalse(rows[0]['v6_history_eligible'])
    def test_rejects_invalid_runners(self):
        with self.assertRaisesRegex(ValueError,'Invalid runners'):
            inspect({'data':[{'runners':'not a list'}]},'2026-11-20')
if __name__=='__main__':unittest.main()
