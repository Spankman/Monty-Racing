"""Unit tests for Github workflow result retrieval."""
import io
import json
import unittest
from integrations.github_results import run_status,list_artifacts

class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

def fake_opener(payload):
    def open_request(request,timeout):
        return Response(json.dumps(payload).encode("utf-8"))
    return open_request

class ResultTests(unittest.TestCase):
    def test_completed_workflow_not_equated_with_predictions(self):
        status=run_status(123,opener=fake_opener(
            {"status":"completed","conclusion":"success","html_url":"https://github.com/example"}))
        self.assertEqual(status["state"],"WORKFLOW_SUCCEEDED_ARTIFACT_UNVERIFIED")
    def test_failed_workflow(self):
        status=run_status(123,opener=fake_opener({"status":"completed","conclusion":"failure"}))
        self.assertEqual(status["state"],"WORKFLOW_FAILED_OR_CANCELLED")
    def test_pending(self):
        status=run_status(123,opener=fake_opener({"status":"in_progress","conclusion":None}))
        self.assertEqual(status["state"],"WORKFLOW_PENDING")
    def test_artifacts(self):
        items=list_artifacts(123,opener=fake_opener(
            {"artifacts":[{"id":5,"name":"research","expired":False,"size_in_bytes":42}]}))
        self.assertEqual(items[0]["id"],5)
    def test_bad_run_id(self):
        with self.assertRaises(ValueError):
            run_status(-1)

if __name__=="__main__":
    unittest.main()
