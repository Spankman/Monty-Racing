# Monty V7 Candidate 2 — Expert Consensus Intelligence (ECI)

Experimental feature group; **V6 and V7 Candidate 1 are unchanged**. This branch adds an isolated feature builder, not a trained or deployed prediction model.

## Inputs
Capture approximately 10 genuinely distinct named analysts per race where legally accessible. Store source URL, publication timestamp/timezone, race/runner identifiers, explicit rankings, best-bet and roughie flags, collection timestamp, and licensing/provenance. Do not invent missing selections. Avoid syndicated duplicates and retrospective edits. Use a fixed pre-race cutoff and archive original snapshots.

## Features
The `expert_consensus.py` builder computes top-three votes, first-choice votes, best-bet/roughie votes, expert coverage, and weighted support. No source data is bundled. Expert weights are optional and **must be learned from strictly earlier races**, not the evaluation fold. Zero available analysts means missing consensus, not zero support.

## Required next stages
1. Build timestamped, permission-compliant AU/NZ tipster ingestion with canonical runner matching and scratchings handling.
2. Add source deduplication, independent analyst identities, and explicit non-selection vs unavailable distinctions.
3. Add race-normalized divergence features using Monty's *frozen pre-race* probabilities and timestamped market odds; never compare raw percentages to unnormalized implied odds.
4. Compare V6 baseline, V7 Candidate 1, V7 Candidate 2 without ECI, equal-weight ECI, and prior-history-weighted ECI on identical chronological folds; evaluate AU/NZ separately.
5. Measure win calibration (log loss/Brier), win/place/top-four hit rates, ROI with realistic odds and costs, sample sizes, coverage, and uncertainty. Freeze all shadow-test predictions before race time.
6. Promote ECI only if it improves genuinely out-of-sample performance. Preserve V6 artifacts and historical pre-race selections.

No profitability or performance improvement is claimed by this commit.
