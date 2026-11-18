"""Test that discovery artifacts cannot masquerade as predictions."""
import io
import json
import unittest
import zipfile
from integrations.artifact_validator import validate_artifact_bytes

def artifact(status,predictions=None):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        z.writestr("output/run_status.json",json.dumps(status))
        if predictions is not None:
            z.writestr("output/predictions.json",json.dumps(predictions))
    return out.getvalue()

class ArtifactTests(unittest.TestCase):
    def test_discovery_is_not_predictions(self):
        result=validate_artifact_bytes(artifact({"model_executed":False,"status":"DISCOVERY_ONLY_NO_RUNNER_SNAPSHOT"}))
        self.assertEqual(result["state"],"NOT_EXECUTED")
    def test_successful_model_requires_predictions(self):
        with self.assertRaises(ValueError):
            validate_artifact_bytes(artifact({"model_executed":True,"status":"MODEL_COMPLETED","model_version":"v6"}))
    def test_valid_research_output(self):
        p={"model_version":"v7_research","generated_at":"2026-11-18T00:00:00Z",
           "data_cutoff":"2026-11-17T00:00:00Z","races":[{"race_id":"test|1"}],
           "research_only":True}
        r=validate_artifact_bytes(artifact({"model_executed":True,"status":"MODEL_COMPLETED",
                                             "model_version":"v7_research"},p))
        self.assertEqual(r["state"],"VALIDATED_MODEL_OUTPUT")
    def test_v7_cannot_be_misrepresented_as_approved(self):
        p={"model_version":"v7_research","generated_at":"2026-11-18T00:00:00Z",
           "data_cutoff":"2026-11-17T00:00:00Z","races":[{"race_id":"test|1"}]}
        with self.assertRaises(ValueError):
            validate_artifact_bytes(artifact({"model_executed":True,"status":"MODEL_COMPLETED",
                                             "model_version":"v7_research"},p))
    def test_version_mismatch(self):
        p={"model_version":"v6","generated_at":"2026-11-18T00:00:00Z",
           "data_cutoff":"2026-11-17T00:00:00Z","races":[{"race_id":"test|1"}]}
        with self.assertRaises(ValueError):
            validate_artifact_bytes(artifact({"model_executed":True,"status":"MODEL_COMPLETED",
                                             "model_version":"v7_research"},p))

if __name__=="__main__":
    unittest.main()
