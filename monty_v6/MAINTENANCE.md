# Monty 6.1 maintenance release

This release changes code organisation and verification, not model selection or coefficients. The original V6 performance conclusions and data limitations remain in effect. No model was retrained and no new accuracy or exotic-bet edge is claimed.

| Module | Responsibility |
|---|---|
| `monty/normalization.py` | Names, going categories, comparable class labels and clock parsing |
| `monty/ingestion.py` | Source joins, metadata QA and timestamped overlays |
| `monty/features.py` | Prior-day form and connection features |
| `monty/fitting.py` | Training and validation-only selection |
| `monty/evaluation.py` | Already-exposed diagnostic reporting |
| `monty/model_math.py` | Race probabilities, objective and metrics |
| `monty/scoring.py` | Frozen inference without outcome labels or retraining |
| `monty/integrity.py` | Hash, model-schema, feature-order and scaler checks |
| `monty/pipeline.py` | Stage orchestration |
| `run_multivariable.py` | Compatible legacy entry point |
| `gear.py` | Explicit gear-change parser, unchanged |

## Reproduce the tested environment

Use Python 3.12 and `python -m pip install -r monty_v6/requirements.txt` from the extracted pack root. Exact pins are unchanged. `pyproject.toml` records separate compatibility bounds and editable-package metadata; those ranges are not a claim that every version in them has been tested. Research data remain in the extracted project layout, rather than being bundled into an installable wheel.

## Verify before scoring

From the extracted pack root:

```
python monty_v6/verify_project.py
python -m unittest discover -s monty_v6 -p 'test_*.py'
```

Verification checks the shipped hashes, loads the frozen feature matrix, applies the saved model/scaler without fitting, verifies runner identity/order and compares every diagnostic probability with its pre-refactor value. Tests additionally require exact preservation of a pre-refactor feature fixture and reject changed/missing artifacts, unsafe manifest paths, reordered features and mismatched scaler dimensions.

`monty.scoring.score_features` verifies artifacts by default and rejects incompatible inputs before scoring. Boosting binaries are read only after integrity checks and an exact saved scikit-learn version check. Callers must still establish that their historical input features were available before the race; file integrity cannot prove data timing or authenticity. Do not pass outcome labels as input features.

Artifact verification is mandatory in the scoring entry point; there is no scoring flag to bypass it.

## Updating a release deliberately

Training or editing governed files invalidates the existing manifest. Review the changes, then explicitly run `python monty_v6/refresh_manifest.py`, followed by verification and tests. Scoring and CI never silently regenerate hashes to bless stale files. Hashes detect accidental drift; they are not a digital signature or protection against someone changing both a file and its manifest.

The pack-root manifest also covers the required V5 source code, registry and cleaned data. The project-level manifest covers V6 code/data/models. CI runs pack verification, project verification, frozen prediction replay and tests. The included GitHub Actions workflow is ready to use in a repository containing this extracted layout; it has not been deployed or run on GitHub. The equivalent checks were executed locally.

All diagnostic periods are already exposed. Replaying predictions here is a refactoring regression check, not a fresh backtest, new model selection or prospective performance result.
