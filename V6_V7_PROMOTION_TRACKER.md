# Monty V6 → V7 promotion tracker

Updated: 2026-11-21. Branch: grok-independent-repairs. Latest offline CI 44847770547 passed at commit 09c1ef65; manual Krok connection run 44847348535 failed (requires diagnosis).
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
- [ ] Diagnose failed manual Krok connection run 44847348535: generic validation error; next manual run must establish exact cause. Do not confuse this with successful offline CI.
- [ ] Resolve provider duplicate records with verifiable authoritative field/price provenance; recover Wanganui and other excluded races safely.
- [ ] Independent TAB validation of fields, scratchings, odds and quote timestamps for full AU/NZ TAB coverage.
- [x] Verify latest workflow change (d58dce7) by CI (offline checks 44847256229 passed).
- [ ] Production daily report: only qualified BB/ruffies, not every race's provisional leader.

## Authentic V6
- [ ] Restore and integrity-check missing frozen V6 artifacts (28 of 55 absent from available backup at prior audit).
- [ ] Reproduce genuine V6 scoring with verified historical features and demonstrate comparison-ready outputs.
- [ ] Retain V6 immutable as baseline and fallback.

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
