# Monty operational readiness — independent review handover (19 Nov 2026)

**Status:** research only. **Branch:** `monty-operational-readiness-2026-11-19`. Do not merge without review. V6 is frozen; V7 is unapproved.

## Evidence verified in GitHub
- The latest offline code-check runs on main completed successfully, including article capture, candidate extraction, field-matching, and safety tests.
- The recent Actions listing contained no daily research workflow runs among the latest 30 entries. **Do not infer that a scheduled live run has succeeded.**
- Public repository does not expose the complete private V6 artifact archive. Never disable integrity checks or fabricate replacement artifacts.
- The public repository tree does not include a clearly identifiable V7 Candidate 1 bet-level backtest package supporting the reported −14.77% ROI. Recover original dated inputs, 139 bet records, odds assumptions, evaluation folds, and run commands before citing it as reproducible.

## Priority 0 — establish a real operational baseline
1. Run the existing daily research workflow with the configured Krok secret in an approved environment. Do not print credentials or raw protected API responses.
2. Verify **actual** field completeness, scratched runners, meetings (AU/NZ, metro/country), scheduled off-times, and odds timestamps.
3. Preserve immutable pre-off model output, source snapshot hash, code commit SHA, UTC creation time, version, and model status. Do not label a later reconstruction as pre-off.
4. Validate probabilities sum to one per race and all eligible runners appear exactly once. Reject missing/duplicate runner keys.
5. Reconcile race results against the frozen predictions without rewriting original records. Report coverage, NO BET rate, calibration, strike rate, market benchmark, and ROI including costs. Separate win, quinella, and boxed trifecta ledgers.
6. Confirm no maidens, two-year-old races or jumps are recommended without a documented user override.

## Expert-tip gates
- Article discovery, capture, extraction and field matching are **not** independently authenticated tips.
- Capture time proves when *our process* saw a page, not when its selection was published or whether it was available before off.
- Named analyst, source URL, matching race/runner, independently verified off-time, valid pre-off capture, source evidence, and non-syndicated identity are necessary before eligibility.
- Never promote `expert_candidate_field_audit.json` or `expert_article_candidates.json` to `expert_tips_raw.csv` automatically.
- Keep expert weight at 0 unless chronological holdout comparison to market and Monty supports an approved change.

## Specific code-review targets
- `monty_expert_article_capture.py`: robots, redirects, hostname comparison, fetch bounds, source permissions and HTTP failures.
- `monty_expert_candidate_extract.py`: false-positive patterns, horse names, missing meeting identity.
- `monty_expert_candidate_field_audit.py`: ambiguous meeting/runner matching and absence of proof of publication time.
- `expert_tip_ingest.py` and `monty_v7_shadow_blend.py`: claimed timestamps are not cryptographically authenticated; inspect provenance trust boundary and possible analyst duplication.
- `.github/workflows/monty-daily-research.yml`: distinguish passing CI unit tests from successful production data retrieval.

## Questions for Claude's independent review
1. What exact command and data are needed to reproduce RM6 and RM7 today, and what is missing?
2. Are the 139 V7 Candidate 1 bets and −14.77% ROI reproducible from available evidence?
3. Can any unverified expert candidate influence scoring through another code path?
4. Does the current workflow persist a provably pre-race prediction and odds snapshot, or only ephemeral artifacts?
5. Which changes are correctness fixes versus speculative model tuning?

**No unverified performance claims. No silent production changes. No V6 modifications.**
