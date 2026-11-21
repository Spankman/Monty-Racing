"""Safety and input tests for GitHub Actions dispatch bridge."""
import unittest
from unittest.mock import patch
from integrations.github_dispatch import payload, dispatch

class DispatchTests(unittest.TestCase):
    def test_payload(self):
        p=payload("2026-11-18")
        self.assertEqual(p["inputs"]["racing_date"], "2026-11-18")
        self.assertEqual(p["ref"], "experiment/expert-consensus-v7")
    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            payload("2026-02-30")
    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            payload("2026-11-18", "../secrets.json")
    def test_missing_token_does_not_dispatch(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": ""}):
            with self.assertRaises(RuntimeError):
                dispatch("2026-11-18")
    def test_dispatch_does_not_claim_completion(self):
        class Response:
            status=204
            def __enter__(self): return self
            def __exit__(self,*args): return False
        calls=[]
        def fake_open(request,timeout):
            calls.append((request.full_url,request.get_method(),timeout))
            return Response()
        result=dispatch("2026-11-18",token="dummy-test-token",opener=fake_open)
        self.assertEqual(result["status"],"DISPATCH_ACCEPTED_NOT_COMPLETED")
        self.assertEqual(calls[0][1],"POST")

if __name__=="__main__":
    unittest.main()
