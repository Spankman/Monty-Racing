# Expert consensus and adaptive weighting — Work implementation specification

Owner directive, 19 November 2026. Collect **many real independent expert tips**, compare them against pre-race Monty V6/V7 selections, then **adapt weights using out-of-sample evidence**, never fabricate tips, sources, dates or prices.

## Data contract
Persist immutable source records: source_name, author, source_url, publication_timestamp, actual_capture_timestamp (offset-aware), meeting/date/race, saddlecloth/horse, bet_type (best/value/roughie/each-way/etc), tip_rank, available fixed odds and odds_capture_timestamp, race_off_timestamp, runner match status, scratchings and race conditions. Keep raw source evidence/provenance privately where licensed. If publication or capture time cannot be verified as pre-off, store as research-only and exclude from predictive backtests and blending. Avoid scraping against terms or paywalls; use licensed APIs and permitted public pages.

## Evaluation
1. Start with source discovery across AU/NZ metro/country. Log missing meetings; avoid selection bias.
2. Freeze Monty model picks, probabilities, expert picks and quoted odds pre-off. Never fill missing expert coverage with made-up picks.
3. Evaluate experts independently and as consensus; report coverage, win hit rate, actual WIN ROI, log loss/Brier where genuine probabilities exist, price bins, going, race class and track. Keep quinella/trifecta/first-four accounting separate.
4. Measure overlap versus disagreement and market-only/V6/V7 baselines on identical chronological windows.
5. Expert opinions are ranks/selections, not calibrated probabilities. Calibrate on **past** data before using as probability vectors; use hierarchical shrinkage for small samples and guard against correlated experts copying each other.
6. Begin research blend at 90/10 where provenance and feature coverage gates pass; test 0/5/10/15/20% expert weight using chronological walk-forward only. Dynamic changes require minimum sample sizes, positive out-of-sample improvement and strict bounds; revert to zero when evidence is insufficient. Do not tune on today's results then claim today's performance.
7. Output source-specific audit, weights used, sample counts, uncertainty, timestamps, coverage, no-bet reasons. Keep V6 frozen; implement shared post-scoring layer, not modifications to V6 artifacts.
8. Respect owner exclusions (maiden/2yo/jumps unless requested), best-bet exotic ladder, standalone win-only roughies, and lower-confidence single-race opinions.

## Immediate next tasks
- Review `EXPERT_TIPS_SOURCES_2026-11-19.md` for *candidate* published source leads, not machine-verified inputs.
- Implement collector adapters with documented legal access and tests for duplicates, time zones, off-time, name mapping, source independence, source downtime, and missing data.
- Integrate into `.github/workflows/monty-daily-research.yml` through the existing `--experts` interface. It currently uses zero expert weight without a verified CSV and requires >=60% model feature coverage.
- Run shadow-only prospective comparisons; don't claim profit or approve bets until evidence warrants.

**Acceptance:** daily report shows real sourced expert picks, each expert's track record, Monty-only baseline, overlap/disagreement, out-of-sample comparison, effective blend weight and reasons for exclusions. Never invent tips.
