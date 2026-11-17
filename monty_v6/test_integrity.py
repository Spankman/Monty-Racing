import hashlib,json,tempfile,unittest
from pathlib import Path
import numpy as np
from monty.config import HERE
from monty.integrity import ArtifactError,verify_artifacts,validate_model_contract

class IntegrityChecks(unittest.TestCase):
    def test_changed_missing_and_unsafe_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'model.bin').write_bytes(b'original');m={'model.bin':hashlib.sha256(b'original').hexdigest()};(p/'artifact_hashes.json').write_text(json.dumps(m))
            self.assertEqual(verify_artifacts(p),1)
            (p/'model.bin').write_bytes(b'stale')
            with self.assertRaises(ArtifactError):verify_artifacts(p)
            (p/'model.bin').unlink()
            with self.assertRaises(ArtifactError):verify_artifacts(p)
            (p/'artifact_hashes.json').write_text(json.dumps({'../escape':'bad'}))
            with self.assertRaises(ArtifactError):verify_artifacts(p)
    def test_model_schema_and_dimensions_rejected(self):
        a=json.loads((HERE/'results/frozen_model.json').read_text());n=a['input_feature_names'];validate_model_contract(a,n)
        with self.assertRaises(ArtifactError):validate_model_contract(a,n[::-1])
        a['scale']=a['scale'][:-1]
        with self.assertRaises(ArtifactError):validate_model_contract(a,n)
    def test_pre_refactor_feature_values_preserved(self):
        from test_multivariable import MultivariableChecks
        from monty.features import build_features
        _,X,n=build_features(MultivariableChecks().fixture())
        with np.load(HERE/'testdata/pre_refactor_features.npz',allow_pickle=False) as z:
            self.assertEqual(n,z['names'].tolist());np.testing.assert_array_equal(X,z['X'])
    def test_shipped_manifest_and_frozen_prediction_replay(self):
        from verify_project import verify_project
        result=verify_project();self.assertFalse(result['refitted']);self.assertLessEqual(result['maximum_probability_difference'],1e-12)

if __name__=='__main__':unittest.main()
