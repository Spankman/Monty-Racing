# Monty live-data gate — Saturday 21 November 2026

## Live provider connection — VERIFIED 19 November 2026

GitHub Actions [run #44493611326](https://github.com/Spankman/Monty-Racing/actions/runs/44493611326), on default branch, **completed successfully**. For Queensland racing date **2026-11-20**, the actual Krok request accepted **48 races and 535 runners**, with reported quote source **TAB**. The key was present as a masked GitHub secret. The run explicitly recorded `tab_verified=false`, `complete_au_nz_coverage_verified=false`, `model_loaded=false`, and `predictions_generated=false`. This proves **provider connectivity**, not scoring, independent TAB validation or complete meeting coverage.

Next: execute the separate end-to-end live smoke workflow after review/deployment; it now accepts an optional explicit Queensland racing date. No selections before Saturday morning.

## Verified offline
- The Krok fixture -> adapter -> provisional V6 scorer -> create-only prediction/audit pipeline is covered by `test_krok_adapter.py::test_fixture_cli_to_provisional_predictions` and GitHub CI.
- This is **not** a successful live Krok API request. No private API credential or live field is available in CI.
- Provisional V6 is **not betting-authorised**. Missing private V6 artifacts prevent full frozen-model integrity certification.

## GitHub Actions execution prerequisite

**Existing live-connection shortcut:** The default `main` branch already contains `.github/workflows/monty-manual-intake.yml` (`Monty manual Krok connection check`). It can be manually dispatched in GitHub Actions with a Queensland racing date, and invokes `check_krok.py` with the `KROK_API_KEY` repository secret. This tests provider connectivity without predictions and uploads a seven-day connection report. Inspect its run conclusion and report before claiming live access. The default `main` branch now also contains `.github/workflows/monty-live-smoke.yml` (commit `0610ca395`, 19 November), but that version performs **connectivity-only** checks and deliberately generates no predictions. The full end-to-end scoring implementation of the same workflow path remains only on the **unmerged** `grok-independent-repairs` branch. GitHub normally requires a `workflow_dispatch` workflow to exist on the repository's **default branch** before it can be manually dispatched in the Actions UI/API. Passing ordinary branch CI does not mean the live smoke workflow ran. The authorised maintainer must separately review and deploy the **full scoring workflow implementation** to the default branch before its manual dispatch can test scoring; dispatching the existing default-branch connectivity-only workflow cannot establish end-to-end readiness. Confirm the `KROK_API_KEY` Actions secret exists; do not print or paste its value. A live provider connection was proven by run #44493611326 above; ordinary offline CI still does not prove end-to-end scoring or complete coverage.

## Live smoke run (only when authorised key is available)

Do not put a key in code, GitHub issues, logs, or chat. Set `KROK_API_KEY` as an environment secret in the execution environment, then run from the repository root:

```sh
python -m pip install -r requirements-runner.txt
python krok_adapter.py --date 2026-11-21 --output-dir output_live_2026_11_21 --provisional-operational
```

Expected output files:
- `krok_raw.json`: unmodified provider payload (may contain sensitive provider data; do not publish blindly)
- `krok_snapshot.json`: normalized runners and source-supplied race counts
- `krok_adapter_audit.json`: accepted/skipped races and quoted price source
- `provisional_scored/operational_predictions.csv`
- `provisional_scored/prediction_record.json`
- `provisional_scored/snapshot_provenance.json`

A failure is a **NO BET / no selection** outcome, not permission to fabricate missing runners or prices. A successful command proves only that the provider response was parsed and provisionally scored; it does **not** prove that TAB fields and scratchings were independently verified or that quoted odds were pre-off.

## Saturday morning acceptance checklist

1. Capture a fresh, date-correct, non-paginated AU/NZ thoroughbred feed with a confirmed timestamp and identify any meetings/races omitted by the provider.
2. Verify each intended race's runners, active scratchings and price basis against an independent trusted source. A race's `expected_active_runners` from Krok is **not independent verification**.
3. Check all maiden, two-year-old and jumping exclusions and unknown race classifications. Unknown status means NO BET.
4. Preserve immutable source, model hash, UTC capture time, complete runner identities and pre-jump timestamp evidence. Never overwrite a previous prediction.
5. Apply the betting-own-money value and NO BET gate. The provisional scorer cannot certify a betting edge.
6. **No Saturday selections before Saturday morning**, per user instruction. Never describe research outputs as genuine fully certified V6 selections.

## Remaining blockers
- Fresh live Krok access for Saturday 21 November with valid permissions and a complete, current feed (the successful 20 November connection check does not establish Saturday coverage).
- Independent TAB (or other authoritative) field and scratching cross-check.
- As-of historical features for meaningful predictions.
- Original private V6 artifacts for full integrity verification.
