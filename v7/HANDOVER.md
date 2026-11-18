# Monty V7 development handover — 17 November 2026

This branch contains the first evaluated V7 candidate, not an approved V6
replacement or a claim that every development requirement is complete.

## Done and reproducible

Original V6 model/data audited with all 55 hashes intact; causal feature replay
matches 62,255 rows × 55 features using the original pre-2025 warm-up. Three
expanding fits plus disjoint penalty-selection and calibration windows evaluated
2,983 races. Frozen V6 comparison restricted to the fair common May–June period
of 1,787 races. Source/input digests, model coefficients, calibration parameters,
aggregate results and instructions are committed. Private runner predictions
and test logs are in the development delivery ZIP.

Strict earlier-evidence contracts and missing-data handling are implemented.
Win scoring, Harville place/quinella estimates, fixed-quote value decisions,
NO BET, dormant expert blend, confirmed-blackbook candidate matching and
research inference CLI are implemented. They are not a new live betting service.

## Findings

V7 does not beat V6 or market win log loss on the common period; bootstrap
intervals include zero. The +5% net-edge, one-top-runner-per-race V7 strategy
loses 20.5325 units / 139 bets (-14.77% quote-proxy ROI). Do not deploy/promote.
V6 and market filtered subsets are small retrospective samples; positive ROI
there is not proof of executable future profits. See RESULTS.md.

## Exact outstanding work and blockers

1. Point-in-time static metadata: the original reconstructed going/connections
   lack publication snapshots. Chronological parameter splits do not fix that.
2. Sectionals/pace: official RQ listing and CSV link verified; direct retrieval
   403. Auckland official per-race listing verified. No authenticated/licensed
   TPD payload. No new historical sectionals in these fits.
3. Interference/bias/weather: official sources researched, evidence join ready;
   no verified labeled historical cohort or forecast release-time reconciliation.
4. Place: original archive has win labels only. Obtain official final finishing
   order, dead-heat rules, actual place terms and payouts before fitting/testing
   calibrated place probabilities or reporting place/quinella ROI.
5. Experts: no immutable pre-race expert probability history; weight stays zero.
6. NZ/international: acquire matched complete fields and historical quotes, then
   validate jurisdiction-specific performance. Do not label AU training NZ-safe.
7. Blackbook: four confirmed names carried forward. Existing scheduled watch
   already exists. Code emits review candidates; no new push/notification
   integration has been deployed or claimed.
8. Prospective validation: freeze before-race inputs, model/version/odds/picks,
   then append results separately. Do not reuse already-seen test dates as new.

## Rules preserved

V6 untouched; no pickle loading or original retraining. No tipster substitution,
fabricated data, meeting quotas or hindsight pick edits. Missing features may use
trained defaults with disclosed provisional status. Rank within each race. A
blackbook horse enters review/shortlist, not an automatic money bet. V7 promotion
requires Ferg's explicit approval after evidence. Existing V6 permissions and
records remain in force.
