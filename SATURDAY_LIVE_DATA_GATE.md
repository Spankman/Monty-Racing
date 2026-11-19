# Monty live-data gate — Saturday 21 November 2026

## Live provider connection — VERIFIED 19 November 2026

GitHub Actions [run #44493611326](https://github.com/Spankman/Monty-Racing/actions/runs/44493611326), on default branch, **completed successfully**. For Queensland racing date **2026-11-20**, the actual Krok request accepted **48 races and 535 runners**, with reported quote source **TAB**. The key was present as a masked GitHub secret. The run explicitly recorded `tab_verified=false`, `complete_au_nz_coverage_verified=false`, `model_loaded=false`, and `predictions_generated=false`. This proves **provider connectivity**, not scoring, independent TAB validation or complete meeting coverage.

The separate end-to-end live smoke workflow was subsequently executed successfully on the repair branch for 21 November; see the verified run below. No selections before Saturday morning.

## Verified live provisional scoring — 20 November, for racing date 21 November 2026

[Actions run #44633410641](https://github.com/Spankman/Monty-Racing/actions/runs/44633410641) manually dispatched `.github/workflows/monty-live-smoke.yml` on `grok-independent-repairs` at commit `cd040a2`, with `RACING_DATE=2026-11-21` and restricted flat research disabled. The job and audit upload succeeded. Its logs confirm 17 provider meetings, **73 accepted races / 963 runners**, and **61 skipped races**: 40 for active-runner identity/price incompleteness and 21 for prohibited race type. Sources of accepted quotes included `TAB`, `best_win`, and `fixed_win`; these are not independently verified TAB prices. Provisional scoring and probability/identity/NO BET audits passed. `betting_authorised=false`; full V6 artifact integrity, independent field checks, as-of odds timing and complete AU/NZ coverage remain **unproven**. The 40 incomplete races may be awaiting prices; the logs do not prove this is the sole cause. Re-fetch closer to race time, retaining race-level missing-price/missing-identity diagnostics. Never fill gaps with invented prices.

## Verified offline
- The Krok fixture -> adapter -> provisional V6 scorer -> create-only prediction/audit pipeline is covered by `test_krok_adapter.py::test_fixture_cli_to_provisional_predictions` and GitHub CI.
- This is **not** a successful live Krok API request. No private API credential or live field is available in CI.
- Provisional V6 is **not betting-authorised**. Missing private V6 artifacts prevent full frozen-model integrity certification.

## GitHub Actions execution prerequisite

**Confirmed branch-dispatch shortcut:** The default `main` branch registers `.github/workflows/monty-live-smoke.yml` as a connectivity-only workflow. Selecting `grok-independent-repairs` in the manual Run workflow branch selector successfully executed the full provisional scoring implementation from that branch in run #44633410641. **No merge or workflow copy to `main` was needed.** Select the repair branch explicitly; selecting `main` executes connectivity-only code. The `KROK_API_KEY` secret stays in Actions and must never be pasted into logs, issues, or chat.

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
- Recheck Saturday's live feed closer to the off: the successful 21 November provisional run accepted 73 races / 963 runners but skipped 40 races with missing active-runner prices or identities. Complete AU/NZ coverage is not proven.
- Independent TAB (or other authoritative) field and scratching cross-check.
- As-of historical features for meaningful predictions.
- Original private V6 artifacts for full integrity verification.

## Daily selection policy — global, not per meeting

Assess every available eligible AU/NZ race, then rank candidates **across the entire day** by model win probability, evidence quality, value and risk. **Never impose one best bet or one roughie per meeting.** Some meetings may have multiple qualified candidates; others none. Group the resulting global shortlist by meeting only for readability. Missing/incomplete races remain pending or NO BET, not fabricated. Keep best bets and roughies distinct; do not mistake the highest-probability $10 outsider for proven value. Experimental V7 shadow output and provisional V6 output are research rankings only until independent verification and model approval establish a betting edge. Preserve the no-maidens/no-2YO/no-jumps betting policy absent explicit override.
