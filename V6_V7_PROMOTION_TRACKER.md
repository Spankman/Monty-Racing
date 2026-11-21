# Monty V6 → V7 promotion tracker

Updated: 2026-11-21. Branch: grok-independent-repairs. Latest confirmed passing offline CI 44853046477 (run #641, single-race routing regression tests); manual Krok connection run 44847348535 failed (requires diagnosis).
Rule: mark [x] only after direct evidence; partial work stays [ ].
Frozen V6 artifacts must never be modified.

## Data and operations
- [x] Krok dated full-card connection and provisional operational research run demonstrated (2026-11-21; 95 accepted races / 1002 runners after exclusions). **Not independently TAB verified.**
- [x] Conflicting Wanganui/Whanganui and Pukekohe aliases excluded rather than selecting arbitrary prices.
- [x] Excluded duplicate-alias races explicitly identified in research report (commit d58dce7).
- [x] Shared fixed-win-odds BB/Q/T/FF presentation wired to live research report, with offline tests (commits 823da6a, 985c38d). Research only.
- [x] Fixed odds strictly below $4 trigger escalation; exactly $4 does not (commit 86f2763).
- [x] Offline code checks passed following live report ladder integration (GitHub Actions 44845708799).
- [x] Add safe error-category diagnostics to manual Krok checker (commit f8a85d5; offline CI 44847770547 passed).
- [x] Verify four safe diagnostic regression tests in CI: first run at 684ec77 failed on `paginated`; fixed at 8785d9d and CI 44848255657 **passed**.
- [x] Expanded Krok diagnostic suite included in passing offline CI run 44853046477 (run #641); this does not verify live Krok connectivity.
- [x] Make blank-date fallback explicit in manual Krok workflow (commit 496e88a; offline CI 44847898309 passed). **Correction:** the failed historical run's logs already show a Queensland-date fallback, so blank input is NOT established as its root cause.
- [x] Publish safe live verification and failure-triage runbook (KROK_LIVE_VERIFICATION.md, commit 760658b).
- [ ] Diagnose failed manual Krok connection run 44847348535: generic validation error; rerun with new diagnostics and verify live provider response. Do not confuse this with successful offline CI.
- [ ] Resolve provider duplicate records with verifiable authoritative field/price provenance; recover Wanganui and other excluded races safely.
- [ ] Independent TAB validation of fields, scratchings, odds and quote timestamps for full AU/NZ TAB coverage.
- [x] Verify latest workflow change (d58dce7) by CI (offline checks 44847256229 passed).
- [ ] Production daily report: only qualified BB/ruffies, not every race's provisional leader.

## Authentic V6
- [ ] Restore and integrity-check missing frozen V6 artifacts (28 of 55 absent from available backup at prior audit).
- [ ] Reproduce genuine V6 scoring with verified historical features and demonstrate comparison-ready outputs.
- [x] Retain V6 model files immutable in the single-race routing changes; V6 remains the research comparison baseline. Single-race automatic V6 fallback was explicitly removed under the owner's newer V7 → V7_LE → non-V7 rule.

## Single-race execution readiness
- [x] Routing order V7 → V7_LE → independently labelled FORM_ASSESSMENT; automatic V6 single-race fallback removed (CI run 44853046477 passed).
- [x] Router no longer claims model execution solely from a V7-labelled candidate (CI run 44853046477 passed).
- [ ] Locate or restore executable V7 Candidate 1 scoring engine and its verified artifacts. Repository audit 2026-11-21 found `monty_v7_shadow_blend.py` (research blend only), `research_frozen_linear_replay.py` (frozen V6 coefficients), and no separate V7 scorer in the development branch. **Do not label V6 replay or a V7 shadow blend as a genuine V7 run.**
- [ ] Implement documented relaxed-feature V7 execution using the genuine V7 engine, preserving identity/odds checks; test and capture provenance before authorising a provisional V7 label.

## V7 validation
- [x] V7 Candidate 1 chronological walk-forward assessment performed: 2,983 races / 3 folds; 139 simulated bets; -20.53 units (-14.77% ROI). **Not promoted.**
- [x] Provisional zero-expert-weight V7 shadow integration demonstrated. **Not genuine fully validated V7.**
- [ ] Restore/validate expert-tip data and test dynamic weighting against no-expert baseline.
- [ ] Build verified histories and improve calibrated win probabilities; separately validate AU and NZ.
- [ ] Backtest V7 against authentic V6, Candidate 1 and market on identical chronological periods with leakage protection.
- [ ] Freeze prospective pre-race selections, quotes and scratchings; track win, quinella, trifecta and First Four ROI separately.
- [ ] Demonstrate statistically credible prospective improvement and stable production operations before promoting V7.
- [ ] Promote V7 to default only after evidence; archive V6 as control and fallback.

## Betting policy
- [x] Documented owner directive: fixed-win odds only for BB/Q/T/FF progression; no exotic dividends as selection inputs (SELECTION_RULES.md).
- [ ] Verify every added supporting runner independently; NO BET when qualification/value cannot be shown.
- [x] Add explicit superseding 21 Nov fixed-$4 rule to MONTY_BETTING_POLICY.md (commit 4394524); earlier historical wording retained for audit.

This checklist is evidence-based: passing CI does not prove model accuracy, betting profitability or genuine V6/V7 scoring.
