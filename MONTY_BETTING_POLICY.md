# MONTY BETTING POLICY — OWNER DIRECTIVE (18 November 2026)

**GOLDEN RULE: Bet like Monty is staking his own money.** This is a mandatory decision policy for future versions and human-facing recommendations, not evidence that a model is already profitable.

## Selection discipline
- Recommend a bet only with verified runners, scratchings, conditions, current available odds, credible pre-race form, and a defensible estimate of win chance and value. Never invent data, probabilities, model execution or results.
- NO BET is the default when evidence, edge, or price is insufficient. Do not force selections, chase losses, or equate favourite status with value.
- Do not bet on maiden races, two-year-old races, or hurdle races unless the owner specifically requests tips for that category. If verification is unavailable, clearly disclose it; do not represent unverified picks as verified Monty output.
- Freeze picks and odds before the jump; do not retroactively alter them. Keep V6 and historical baselines unchanged.

## Owner's betting preferences
- Horse bets: **WIN ONLY**. No each-way/place staking recommendations by default.
- Quinella: **exactly TWO horses**.
- Trifecta: **normally THREE horses, ALWAYS BOXED** (six ordered combinations). Only propose exotics where the combination and total cost justify the risk. No padded combinations.
- Keep win, quinella and trifecta stakes, strike rates and actual net returns/ROI separate; account for full boxed trifecta stake and actual dividends.

## Performance grading (diagnostic, separate from financial ROI)
- Favourite wins = HIT.
- Favourite finishes 2nd or 3rd = MISS.
- Favourite unplaced = **BIG MISS**, flagged for root-cause review.
- Roughie wins = BIG HIT.
- Roughie finishes 2nd or 3rd = NEAR HIT, **not** a winning bet; record its starting odds and relevance to exotics.
- Roughie unplaced = MISS.
- All losing WIN bets remain losses in ROI, regardless of qualitative grade. Roughie placings alone do not prove positive expected value.
- Analyse favourite BIG MISSES and repeated seconds; test whether changes improve future win profitability without overfitting.

## Handover to Work
Read this file and SELECTION_RULES.md before changing V7 or producing tips. Integrate these directives into candidate V7 decision filters, reporting and tests only after inspecting existing code and avoiding contradictions. Do not modify frozen V6 artifacts. Document implementation status and any unresolved ambiguity. The policy itself does not authorize live betting or certify model performance.

## Owner directive — 19 November 2026: universal best-bet exotic ladder

Applies to **all Monty versions** and to **ad-hoc single-race tips**, including tips outside scheduled Monty selections. This is a human-facing recommendation/presentation rule, **not a change to frozen V6 model weights, historical picks or artifacts**.

1. For **every BEST BET**, start with one defensible WIN selection. If its verified current win odds are short, assess an **exactly two-runner quinella**. If both proposed quinella runners are short-priced, assess a **three-runner BOXED trifecta** (6 permutations). If all three proposed trifecta runners are short-priced, assess a **four-runner first four**, stating explicitly whether boxed or ordered, total combinations and total stake. Each added runner must be justified independently by current form, field, price and value. No automatic escalation; may stop at any rung or NO BET. Do not present a speculative exotic as a recommendation.
2. **Every RUFFY remains standalone WIN ONLY**. Do not add quinella/trifecta/first-four suggestions to roughies unless the owner explicitly overrides.
3. For **user-requested individual races**, progressively relax confidence/edge requirements to seek a defensible best-chance selection. Clearly label a lower-confidence selection and differentiate a *race opinion* from a *positive-value bet*. Never relax evidence integrity, fabricate odds, ignore scratchings, or force a wager when there is no credible basis. The existing maiden/2yo/jumps exclusion can be overridden only when the owner explicitly requests that race category.
4. **Short-priced** is not yet an owner-approved numeric cutoff; implement it as an explicit configurable parameter, not a silently invented fixed threshold. Apply the same price criterion to each step. Quinella is 2 horses; trifecta is 3 horses boxed; first-four format/cost must be specified. Separate stakes, returns and ROI by bet type; never count an exotic as a win-bet hit.
5. For V7, research/shadow probabilities are **not approved bets**. This ladder only applies to eligible, verified, pre-race selections after normal quality gates; it does not turn research ranks into betting tips.

### Work implementation checklist
- Read this section, `SELECTION_RULES.md`, and the existing `race_day.py` and V7 shadow pipeline before modifying decisions.
- Implement and unit-test a **shared post-scoring recommendation layer** for all model versions and one-off tips, without altering the frozen V6 model.
- Define/confirm short-price threshold, runner qualification rules, first-four boxing and staking policy; fail closed on missing information.
- Add output fields `selection_type`, `confidence_tier`, `bet_type`, `runner_numbers`, `quoted_odds_at`, `total_combinations`, `total_stake`, `recommendation_status`.
- Verify actual data and performance before permitting any live exotic recommendation.
