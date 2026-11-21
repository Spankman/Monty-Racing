"""Regression tests for the isolated V6 linear recovery scorer."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from recovered_v6_linear import ROOT,load_verified_linear,score_recovery
from monty.integrity import ArtifactError

class RecoveryTests(unittest.TestCase):
    def test_frozen_model_hash_and_probabilities(self):
        model=load_verified_linear()
        names=model['input_feature_names']
        X=np.full((4,len(names)),np.nan)
        base=np.array([.4,.6,.25,.75])
        ids=['race1','race1','race2','race2']
        p=score_recovery(X,names,base,ids)
        self.assertTrue(np.isfinite(p).all())
        self.assertAlmostEqual(p[0]+p[1],1)
        self.assertAlmostEqual(p[2]+p[3],1)

    def test_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'results').mkdir()
            (root/'artifact_hashes.json').write_text((ROOT/'artifact_hashes.json').read_text())
            (root/'results/frozen_model.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ArtifactError,'hash mismatch'):
                load_verified_linear(root)

    def test_incomplete_market_rejected(self):
        model=load_verified_linear()
        names=model['input_feature_names']
        with self.assertRaisesRegex(ArtifactError,'sum to one'):
            score_recovery(np.full((2,len(names)),np.nan),names,[.2,.3],['r','r'])

if __name__=='__main__':unittest.main()
