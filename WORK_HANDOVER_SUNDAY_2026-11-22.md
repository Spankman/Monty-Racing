# MONTY V7 — WORK HANDOVER (Sunday 22 November 2026)

**Repo:** https://github.com/Spankman/Monty-Racing  
**Development branch:** `experiment/expert-consensus-v7`  
**Frozen baseline:** V6 — DO NOT MODIFY, overwrite, or silently replace.  
**Status:** Experimental research code committed. No verified end-to-end V7 prediction run, CI pass, or prospective performance improvement has been demonstrated.

## Read this first

The user wants ChatGPT to run Monty with genuine Australian and New Zealand thoroughbred runner data and independently sourced expert opinions, then eventually compare V7 to V6. GitHub automation can be addressed by Work; do not let it block model research. Never invent expert votes, runner odds, model scores, completed tests or pre-race timestamps.

**Universal betting policy (applies to every version):**
- Confirmed maiden races: NO BET.
- Confirmed two-year-old races: NO BET.
- Confirmed hurdle races: NO BET.
- User specifically requesting a tip for an excluded race overrides that race's exclusion.
- If classification cannot be verified, user permits a *clearly flagged* `UNVERIFIED_OVERRIDE`. This is NOT permission to override confirmed exclusions.
- Missing race metadata, runner fields, odds or expert independence must never be silently represented as verified.
- Keep frozen historical picks and quotes unchanged; NO BET is always valid.

## Code map

- `integrations/race_exclusions.py`: universal classification and explicit-request override.
- `integrations/run_snapshot.py`: existing V6 snapshot execution wrapper; emits research-only JSON. **It does not currently join the saved race_metadata JSON into its output.** Treat its category output as unverified.
- `integrations/race_metadata/2026-11-18.json`: manually recorded subset of race classifications; validate source and timestamps before using.
- `expert_consensus_experiment/observations/2026-11-18.json`: sourced editorial mentions; these are NOT proven independent, complete ranked ballots or a fitted dataset.
- `expert_consensus_experiment/audit_observations.py`: basic source audit, no model.
- `expert_consensus_experiment/provisional_overlay.py`: joins V6 predictions and editorial mentions by meeting, race and saddlecloth, and optionally metadata. Produces **null** V7 probabilities.
- `expert_consensus_experiment/provisional_rank.py`: declared fixed expert blend, outputs **ranking indices only**, not win probabilities.
- `expert_consensus_experiment/dynamic_blend.py`: provisional coverage/agreement heuristic, maximum 20% expert influence, but **requires `verified_independent_sources` on each runner**. The current observations do not populate this field, so a genuine run will normally revert to V6 ranking.
- `expert_consensus_experiment/expert_consensus.py`: point-in-time expert features; `fusion_train.py`: chronological research trainer, not a validated production model.
- `integrations/github_dispatch.py`, `github_results.py`, `artifact_validator.py`: proposed GitHub automation and artifact validation, not verified as a live end-to-end service.
- `.github/workflows/monty-v7-research.yml`: workflow definition on development branch; previously queried commit runs returned empty, so do not claim CI success.

## Critical engineering risks and blockers

1. **Verify tests:** `python -m unittest discover -s integrations -p 'test_*.py'` and `python -m unittest discover -s expert_consensus_experiment -p 'test_*.py'`. Execute and repair failures; committed tests have not been confirmed passing.
2. **Join real data:** obtain real V6 runner-level `predictions.json` or auditable snapshot and run `provisional_overlay.py`, then `dynamic_blend.rank_dynamic`. No synthetic input may be presented as real picks.
3. **Race metadata:** integrate authoritative classification into output; avoid treating missing metadata as verified eligible. Confirm 2YO-only, maiden, hurdle and jumps/steeplechase terminology with user before extending exclusions.
4. **Independent expert identities:** editorial source names are NOT evidence of independence. A site may syndicate another analyst. Deduplicate by actual analyst/editorial origin, publication timestamp and race; only add `verified_independent_sources` when proven.
5. **Timestamp safety:** verify publication and source observation time against scheduled jump time; no post-race opinions in pre-race model features.
6. **Heuristic scoring:** dynamic 0–20% expert influence is not calibrated and is not a win probability. Evaluate out-of-sample against frozen V6 on identical races before promoting.
7. **Candidate 1 warning:** previous V7 candidate backtest lost 20.53 units on 139 bets (−14.77% ROI). Do not call V7 an improvement without evidence.
8. **Coverage:** current observation file is sparse and not a 5–20 independent expert ballot per race. The earlier 5–20 target remains research guidance; dynamic module permits 2+ verified voices for *provisional ranking*, not calibrated predictions.
9. **GitHub workflow:** actions runs were not observed on experimental commits. Check repository Actions settings, default branch workflow registration and dependency installation. Do not merge to main or modify V6 without user authorization.
10. **Input checks:** ensure all runners, scratchings, odds, wet-track conditions, track changes, barriers and race numbers are validated. If not, mark unavailable and do not fabricate.

## Recommended Sunday sequence

1. Checkout `experiment/expert-consensus-v7`, record commit SHA, run both test suites, fix failures and commit fixes.
2. Inspect saved runner-level V6 output for 18 Nov, reconcile source names, track variants and race IDs; preserve raw source and SHA256.
3. Build a **read-only** race classification + expert source join, with audit trail and point-in-time checks. Do not silently fill absent independent sources.
4. Run a clearly labelled provisional V7 overlay on real runners. Output source citations, eligible/NO BET/unverified race labels, V6 probability, expert names and provisional ranking index. No invented V7 win probability.
5. Freeze pre-race outputs for subsequent dates. Measure chronological log loss, calibration, top-1 accuracy, ROI after costs and betting exclusions. Compare against V6 and market on same period.
6. Only after validated gains consider learned expert weighting, more coverage and production rollout.

## Reproduction commands

```bash
git checkout experiment/expert-consensus-v7
python -m unittest discover -s integrations -p 'test_*.py'
python -m unittest discover -s expert_consensus_experiment -p 'test_*.py'
python -m expert_consensus_experiment.audit_observations expert_consensus_experiment/observations/2026-11-18.json --output /tmp/monty-expert-audit.json
# Only when a REAL runner-level V6 predictions JSON exists:
python -m expert_consensus_experiment.provisional_overlay --v6-predictions /path/to/real/predictions.json --observations expert_consensus_experiment/observations/2026-11-18.json --race-metadata integrations/race_metadata/2026-11-18.json --output /tmp/monty-overlay.json
python -m expert_consensus_experiment.provisional_rank --overlay /tmp/monty-overlay.json --output /tmp/monty-provisional-rank.json
```

**Important:** the last command uses a fixed 10% provisional blend; dynamic blending is currently a Python API (`rank_dynamic`) and will be 0% without independently verified source identities. Add an audited dynamic CLI before describing it as fully operational.

## User-facing selection format

When the user requests racing selections, return a simple meeting-by-meeting list with **Best Bet** and **Ruffie**, saddlecloth number and horse name; don't invent predictions or substitute tipsters for Monty. State when results are research-only, missing, or unverified. No automatic tip in excluded races unless specifically requested.

**Completion criterion for Work:** a tested reproducible run on actual sourced runners with frozen inputs, source citations, accurate exclusions and honest model-version labels; ideally prospective result tracking. Report remaining blockers plainly.

## 18 November continuation — join safety

- Draft pull request **#9** is open and clearly titled **WORK START HERE**: https://github.com/Spankman/Monty-Racing/pull/9 . It is **draft / DO NOT MERGE**; use it as the discoverable entry point.
- `provisional_overlay.py` now rejects duplicate race classifications, duplicate normalized V6 meeting/race keys and duplicate/missing saddlecloth numbers. This avoids quietly attaching the wrong expert opinion to a horse.
- Overlay explicitly sets `verified_independent_sources: []` for all editorial mentions. **Do not automatically promote named publications to independent votes**. Confirm the actual originating analyst and syndication relationships first. As a result the current dynamic blend correctly remains zero until provenance is established.
- Added regression tests for duplicate joins and unknown source independence. **Not yet executed**. The next Work step remains to run tests and a real runner-level join, then fix any failures.

## 18 November — local REAL-DATA V7 replay completed

- Executed a local deterministic research replay on the existing saved `monty_2026-11-18_v6_expert_comparison_pending.csv` file (SHA256 `49c6140b19efbdd5bdf9d01d7fe539a51e5c6b5b9b90723732f0e5d309ca8bb9`).
- **35 races / 416 runners**, 12 editorial observations, all 12 matched by meeting/race/saddlecloth, 0 unmatched. Six confirmed excluded races using the available *partial* race classification subset; all others marked unverified override, NOT confirmed eligible.
- **0 verified independent expert identities**, therefore the dynamic expert blend is **0%** and the provisional rankings are exactly the normalized V6 probabilities. **No calibrated V7 probability was generated.** This is a genuine input-data replay, not a trained V7 result or verified pre-race freeze.
- Highest-ranked saved V6 horses with a recorded editorial mention: Belmont R4 #1 Rok 'n' Rom (36.81%), Doomben R7 #1 Climb The Ladder (30.31%), Sandown R4 #1 Pariah Pearl (25.08%), Warwick Farm R3 #11 Brightburn (27.80%). Historical research only; not live tips.
- Local outputs in conversation container: `/mnt/data/monty_v7_2026-11-18_replay.json` and `/mnt/data/run_monty_v7_replay.py`. These are NOT in the GitHub repo; Work should reproduce from saved source CSV and committed expert observations. The CSV was sourced from a prior conversation attachment, not committed here.
- **Critical:** prior GitHub integration tests still not executed; local replay independently mirrors conservative dynamic no-independence fallback, not the complete GitHub module test suite.

## IMPORTANT correction — FormFav already integrated on main (18 Nov repository audit)

**Do not waste time reconnecting FormFav.** The canonical `main` branch already has functioning `formfav_client.py`, `formfav_inputs.py`, `collect_connections.py`, `connections_enrichment.py` and corresponding tests. Read `FORMFAV.md`, `CONNECTIONS.md`, `MONTY_CURRENT.md`, `DATA_SOURCE_RESEARCH.md`, `LIVE_COMPLETION.md`, `SELECTION_RULES.md` on **main** before development. Previous chat assertions that FormFav was not connected were incorrect.

**Recorded verified execution:** FormFav Pro API tier and 43 AU/NZ race cards; 35 Australian TAB races refreshed 17 Nov 18:24–18:29 Queensland (450 declared entries, 416 active, 34 scratched), 22 FormFav-vs-TAB scratching disagreements resolved. 80 historical markets identity-checked, and original `jockey_changed` feature recovered for 92 runners. Active feature coverage 13–22 of 43; original 55 V6 artifacts preserved. Connection enrichment changed the top ranked horse in Belmont R5 from Von Rommel to Arizona Sky. The above are documented repository execution records, not newly rerun tests in this session.

**What FormFav does NOT solve:** current fixed-win prices need separate TAB capture, official scheduled-off Betfair historical quotes cannot be substituted by FormFav official SP, FormFav aggregated career/90d/365d stats cannot be substituted for V6 expected-win residuals, historical horse and trainer feature coverage remains incomplete, and NZ model validity is not established. FormFav proprietary predictions are deliberately excluded from V6 scoring. The FormFav card capture is cached unless explicitly refreshed, so stale scratching information is a known risk.

**Sunday priority update:** Do NOT rebuild the existing FormFav integration. Instead, inspect its existing outputs and audit the *incremental* benefit with same-race, same-time comparisons: V6 without supplemental FormFav features vs with eligible verified features, with point-in-time controls. Investigate whether 92 jockey-change inputs and other fields improve log loss, calibration and race ranking, not just feature counts. Keep `main` and V6 immutable while testing in the experimental branch. If saved raw snapshots aren't available to Work, report the dependency; don't invent an ablation result.

## 18 Nov continuation — FormFav paired ablation code

Added `expert_consensus_experiment/formfav_ablation.py` and `test_formfav_ablation.py` on experimental branch. The utility takes **the already-enriched private input CSV** and performs paired frozen-V6 scoring twice with identical race fields, horses and odds: once with only `jockey_changed` reset to missing (model's saved imputation), and once with verified `jockey_changed` values. It reports number of rows with that feature, probability movement and top-rank changes; it **does not** claim accuracy, value or ROI improvement. The test rejects changed fields/quotes and tests a ranking flip with a stub scorer.

To execute from repository root when private enriched input CSV is available:

```bash
python -m unittest expert_consensus_experiment.test_formfav_ablation
python -m expert_consensus_experiment.formfav_ablation --enriched-inputs /private/path/to/enriched/inputs.csv --output /private/path/to/formfav_sensitivity.json
```

**Not yet executed**: GitHub connector can commit code but cannot access the ignored private input CSV in this session. Do not fabricate a sensitivity number. A genuine historical predictive-value ablation requires matched past outcomes and point-in-time FormFav feature availability; a one-day prediction change alone is insufficient. Keep raw inputs, reports and API credentials private.

## 18 Nov further QA — FormFav ablation validation tightened

The paired ablation now validates scorer-output quotes are identical, win probabilities are finite and within [0,1], and each race's win probabilities sum to approximately one. Added negative tests for mismatched scorer quotes and non-normalized probability mass. Changes are committed on the V7 branch; **tests have not been executed in this session**. The required ignored/private `connections_enrichment.py` output `inputs.csv` was not found among accessible GitHub-tracked files; only private source captures can produce the genuine paired analysis. Do not confuse code readiness with a verified predictive improvement.
