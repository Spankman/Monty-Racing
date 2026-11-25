# Australian data recovery and prospective measurement · 25 November 2026

## Decision

Keep V6 official and V7 research-only with external experts at 0%. Continue Australian thoroughbreds independently of NZ. Keep production approval **DATA BLOCKED**. The market repair in draft #226 addresses the reproduced arithmetic anomaly and keeps suspicious prices out of release. It does not verify the underlying market or establish a model edge. No merges, deployments, refitting, threshold changes or wagering.

[Market integrity repair](MARKET_INTEGRITY_REPAIR_2026-11-25.md) · [AU live validation](AU_LIVE_VALIDATION_2026-11-25.md) · [Historical study](HISTORICAL_PERFORMANCE_2026-11-25.md)

## Historical inputs recovered for review

Reopened the original private 18 November history-integration archive and rechecked its lead set against 16 source-pinned Betfair monthly exports. May and July 2026 remained quarantined. The archive contains 1,451 parsed starts for 423 runners on 35 races. The archived resolver linked 375 starts by exchange market and selection ID. In the current recheck, 348 of those also matched dates, distances and normalized names exactly. The other 27 differ in apostrophe presentation. Of 103 latest-start candidates that once supplied six recency and distance features offline, 94 retain that strict contextual match. The other nine require reviewed source aliases. Treat all archive matches as historical leads until registration and official race participation are accepted. No row from the archive was copied into the live scoring path.

The first authority profile sample supplies two corroborated Superhero event links. The official registration remains the same while exchange runner identifiers differ. Use registration plus event identity and dated authority declarations to reconcile races, with exact event IDs retained for the exchange join. Do not use name similarity as proof. These samples help recover recency and distance inputs for both models. They cannot reconstruct complete cumulative or contextual horse/jockey/trainer residuals, original as-of conditions, or the missing V5 warm-up. Keep exchange best-back at the scheduled off distinct from printed SP, BSP and fixed-win close. Neither live engine has newly verified historical inputs.

[Aggregate historical recovery evidence](AU_HISTORY_RECOVERY_EVIDENCE_2026-11-25.json) · [Superhero authority profile](https://www.racingqueensland.com.au/racing/profiles/thoroughbred-horse/superhero-403447)

## Cheapest practical acquisition sequence

| Source | Use now | Evidence needed next |
| --- | --- | --- |
| Existing Krok | Discovery and common AU race snapshot. Meter shared-card credits and blocked/retry calls. | An exact offer-level update time for each selected named bookmaker WIN quote. Fetch time alone is insufficient. Trial Free at actual cadence before giving up the current allocation. |
| Racing Queensland | First authority jurisdiction. Use permitted race pages and field/result files for going, jump, declared runners and scratches. | Confirm final emergencies and dated registered identities. Record source hash and as-of timestamp. Keep source bytes private and respect reuse terms. |
| Direct bookmaker or licensed independent feed | Priority purchase evaluation only after a same-race sample. VicBet and LetsBet were reachable in a hosted read-only probe. TAB/Sportsbet unattended access was blocked in prior probes. | Require full price vector from one named book, quote-level time semantics, declared availability and permission for automated capture. A reachable page or price label alone does not qualify. |
| FormFav | Candidate for free form exploration. Premium documents per-runner bookmaker WIN/place prices and past snapshots. No usable configured credential here. | Request a one-race sample and compare with direct operator evidence. Ask whether each price as-of value is a book update, collector timestamp or lookup cutoff. Verify licence, field completeness, registration and upstream independence before paying. |
| Official Betfair exports | Free source for original scheduled-off exchange inputs and historical outcome labels. | Recover pinned revisions and original V5 warm-up through the owner archive. No PDF printed odds or alternative market substitutes. |

Recommended test arrangement is existing Krok plus Queensland authority data and one authorised named bookmaker sample. No upgrade, cancellation, guaranteed saving or independent price-feed compatibility established.

[FormFav price docs](https://formfav.com/docs/endpoints/prices) · [Krok race docs](https://krokodds.com.au/api-docs/racing) · [Racing Queensland open data](https://www.racingqueensland.com.au/about/reports-and-data/open-data) · [Betfair historical data](https://betfair-datascientists.github.io/modelling/dataSources/)

## Live pilot, freeze and settlement

Verified the saved Actions archive and the forecast/diagnostic hashes. Ipswich R7 and Geelong R8 had genuine pre-jump frozen V6, V7 and normalized common-price market distributions. Albany R7 did not produce a valid paired freeze after mixed bookmaker labels blocked V7. Ipswich's authority and provider runner declarations agreed at 13 provisionally active and four withdrawn. Final emergency status, exact named price timestamps and compatible as-of history remained unverified. Of the three AU attempts, two were excluded diagnostics and one lacked a valid pair. There were **zero admitted and zero settled**. Post-race results cannot make a previously excluded diagnostic eligible.

[Actions run](https://github.com/Spankman/Monty-Racing/actions/runs/45559165191) · [Coverage and blockers](AU_PILOT_COVERAGE_2026-11-25.json)

## Prospective program and production approval

Once the first authorised independent operator sample passes, predeclare a fixed Queensland AU thoroughbred calendar window, eligibility, operator and cutoff. Register every eligible race before results, including rejected or unavailable runs with reasons. Use a single shared field and executable price set across V6, V7 and market. Freeze all evidence and the admission decision before jump. Reconcile results afterward against a separate official source hash. Quarantine late changes and dead heats for separate review. Never backfill a verified cohort from post-race material.

The reporting command is `python -m operations.audit.prospective_metrics COHORT.json`. The cohort includes `start` and `end` offset-aware timestamps and a `races` list. Each race records `date`, `country`, `meeting`, `race`, and either a hash-receipted `forecast` path or a `reason`. Attach a `settlement` path only to an admitted race. Paths resolve relative to the invocation directory. The caller authenticates source bytes and provenance. The tool validates the forecast receipt and reruns settlement checks, rejects duplicates and excluded diagnostics, and reports the denominator, score distribution and rejection reasons even with no settlements.

Primary endpoint is paired per-race log loss versus market with Brisbane date-clustered uncertainty. Also report Brier, top-pick strike, calibration by odds band and a one-unit top-ranked fixed-quote proxy. Keep actual stake/return ROI separate, with fees, deductions and licensed fill evidence. Report best bets and roughies separately once the frozen betting decisions and settlement rules exist. Do not use proxy returns to approve exotic wagers. Reserve a later, untouched calendar window before approving calibration or a threshold change.

The shadow evaluator distinguishes expiry, data block, genuine negative upper edge and provisional positive edge. Production activation still needs independently authenticated quote/field evidence, complete compatible history and validated probabilities under the prospective protocol. Owner approval remains mandatory. With no admitted outcomes, the evaluator cannot be validated for production.

## Acceptance

- Independently check a fresh Australian race with final field, reconciled direct quotes, recoverable compatible history and no market quarantine.
- Admit and freeze both frozen engines plus market before jump, then hash and settle final official results. The current pilot exercised the freeze and exclusion path only.
- Register the next cohort before outcomes. Keep #226, #225 and #213 draft and unmerged.
