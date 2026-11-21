# Grok independent repair — reviewed adaptation

Source: patch supplied in conversation, attributed to Grok commit ebc6b5794d31cf3ed94ceac113cab16d029de9f3. This is a reviewed adaptation, **not** a byte-for-byte application of that commit.

Branch: grok-independent-repairs. Frozen V6 files were not changed.

## Purpose
Score public frozen V6 linear coefficients without the private 55-artifact archive. This is a provisional research fallback only. It does not prove that the model has predictive edge, that the supplied odds were available before race-off, or that the race field was independently verified.

## Review changes
- Validate frozen model contract against public JSON.
- Reject invalid odds, blank identity and duplicate saddlecloths.
- Preserve per-race normalization.
- Explicitly disallow betting authorization.
- Record hashes of input CSV and frozen model.
- Create-only outputs to avoid silent overwrite.
- Add regression tests and CI coverage.

## Run
```bash
python operational/run_operational.py runners.csv --output-dir unique_run_directory
python -m unittest test_operational_v6 -v
```

CSV: meeting,race,number,horse,odds; additional model feature columns optional.

## Outstanding blockers
Full original V6 integrity and replay need missing private artifacts. Live odds and race-field timestamps are unverified. Feature coverage can be low. Original V6 mathematical equivalence has not been independently demonstrated on complete held-out inputs. No betting use permitted.

Never represent provisional outputs as certified V6 or V7 picks.
