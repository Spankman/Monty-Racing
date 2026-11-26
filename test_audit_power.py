"""Planning math checks; no racing claims or target-cohort outcomes."""
import unittest
from operations.audit_alignment.power import *

class Planning(unittest.TestCase):
    def test_known_standardised_normal_design(self):
        self.assertEqual(required_pairs(.1,1),785)
        self.assertEqual(required_pairs(.1,1,design=2),1570)
    def test_multiplicity_and_power_raise_sample_requirement(self):
        n=required_pairs(.005,.05)
        self.assertGreater(required_pairs(.005,.05,alpha=.05/6),n)
        self.assertGreater(required_pairs(.005,.05,power=.9),n)
        self.assertAlmostEqual(minimum_effect(1000,.05,design=3)/minimum_effect(1000,.05),sqrt(3))
    def test_binomial_test_controls_null_size_and_increases_with_edge(self):
        a=binomial_roi_power(500,20,.05);b=binomial_roi_power(500,20,.20)
        self.assertLessEqual(a['size'],.05);self.assertGreater(b['power'],a['power'])
        self.assertLessEqual(a['power'],1)
        self.assertGreater(roi_required_normal(60,.1),roi_required_normal(10,.1))
        self.assertGreater(roi_required_normal(20,.05),roi_required_normal(20,.1))
    def test_scenarios_do_not_claim_target_counts_or_amendment(self):
        r=assessment();self.assertEqual(r['locked_window']['days'],84)
        self.assertIsNone(r['actual_eligible_races']);self.assertIsNone(r['verified_paired_sd'])
        self.assertFalse(r['locked_window']['formal_protocol_modified'])
    def test_independent_verification_of_Work_published_grid(self):
        r=verify_work('operations/audit/QLD_VALIDATION_POWER_2026-11-26.json')
        self.assertLess(r['max_binomial_probability_difference'],2e-6)

    def test_invalid_planning_inputs_rejected(self):
        for kwargs in [dict(effect=0,sd=1),dict(effect=.1,sd=1,design=.9),dict(effect=.1,sd=1,power=.4)]:
            with self.assertRaises(ValueError):required_pairs(**kwargs)
        with self.assertRaises(ValueError):binomial_roi_power(0,20,.1)
        with self.assertRaises(ValueError):minimum_effect(0,.1)
if __name__=='__main__':unittest.main()
