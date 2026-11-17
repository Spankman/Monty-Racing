# V7 first candidate — actual retrospective results

Do not promote this candidate. V6 remains unchanged. No real bets placed.

Common comparison: 1 May–15 June 2025, 1,787 races / 17,987 runners.

| Method | Top-pick strike | Win log loss ↓ | Race Brier ↓ | Calibration ECE ↓ | Top-pick proxy ROI | Value bets | Value proxy ROI | Daily drawdown (units) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V7 | 34.75% | 1.816589 | 0.781546 | 0.004924 | -5.15% | 139 | -14.77% | 31.631 |
| MARKET | 34.92% | 1.815969 | 0.781575 | 0.004270 | -4.92% | 32 | 13.74% | 4.000 |
| V6 | 34.81% | 1.816407 | 0.781712 | 0.005290 | -4.69% | 68 | 17.43% | 7.649 |

These are retrospective scheduled-off best-back payout proxies, with 5%
winnings commission. They are not audited executable betting returns. The
market baseline can select a few apparent value bets when normalized inverse
quotes imply an underround; those are not assumed tradeable arbitrage.

The V7 filtered strategy lost 20.5325 units across 139 bets. Positive V6 or
market subsets here are small, retrospective samples, not profitability proof.

Paired mean win-log-loss differences, V7 minus comparator, day-block bootstrap
95% intervals (2,000 draws, fixed seed 700):

- v7_minus_v6_log_loss_day_bootstrap_95: [-0.001815, 0.002351].
- v7_minus_market_log_loss_day_bootstrap_95: [-0.002592, 0.003861].

All three V7 test folds total 2983 races. Full fold results, calibration bins,
temperatures, selection settings, source digests and runtime versions are in
artifacts/audit_backtest.json. April has no frozen-V6 comparison because that
would reuse V6 selection-period outcomes. No thresholds were retuned after
seeing these results. These are already-exposed retrospective research dates.

Original artifacts: 55 / 55 verified unchanged. Full causal feature replay
matched all 62,255 rows × 55 features using original warm-up history.
