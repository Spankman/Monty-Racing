import unittest
from operations.private_command_acceptance import validated_staging_request
class StagingRequestSecurityTests(unittest.TestCase):
    def issue(self,**kw):
        return dict(dict(state='closed',user={'login':'Spankman'},title='[STAGING ONLY] Monty command: RMV7PS Cairns 4',body='{"date":"2026-11-27","country":"AU"}',created_at='2026-11-27T02:00:00Z'),**kw)
    def test_existing_parser_handles_owned_namespaced_command(self):
        r=validated_staging_request(self.issue(),'2026-11-27')
        self.assertEqual((r['command'],r['version'],r['view']),('RM7PS CAIRNS 4','V7','provisional'))
    def test_no_open_production_or_unowned_issue_is_taken(self):
        for issue in [self.issue(state='open'),self.issue(user={'login':'other'}),self.issue(title='RM6')]:
            with self.assertRaises(ValueError):validated_staging_request(issue,'2026-11-27')
    def test_dates_cannot_be_backfilled(self):
        with self.assertRaises(ValueError):validated_staging_request(self.issue(),'2026-11-28')

    def test_staging_namespace_cannot_enter_the_production_parser(self):
        from operations import transport
        self.assertFalse(transport.addressed_to_monty(self.issue(state='open')))
