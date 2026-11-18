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
