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
