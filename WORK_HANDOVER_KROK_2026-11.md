# MANDATORY WORK HANDOVER — Krok paid API, November 2026

> **NEW OWNER DIRECTIVE:** Read [issue #13](https://github.com/Spankman/Monty-Racing/issues/13) and [MONTY_BETTING_POLICY.md](MONTY_BETTING_POLICY.md) before making changes. Universal best-bet exotic ladder for all Monty versions and single-race tips; ruffies win-only. Initial code and tests in `monty_exotic_ladder.py` / `test_monty_exotic_ladder.py` require integration. This is mandatory, not optional. Preserve frozen V6.


**READ THIS FIRST whenever resuming Monty-Racing.** Linked at the very top of README.md and tracked in [issue #11](https://github.com/Spankman/Monty-Racing/issues/11).

## User's explicit instruction
- Paid Krok Odds API subscribed on/about **19 Nov 2026**, intended for **one month only**.
- **Renewal is conditional**: user may personally renew if Monty is demonstrably making money on actual prospective betting. Never auto-approve a renewal, spend money, or assume a profitable system.
- **Billing action:** Verify exact expiry, renewal and cancellation status with user/account; user has NOT confirmed auto-renew is off. Do not imply subscription will automatically terminate.
- User specifically instructed us to ensure Work sees this without relying on the user to relay it.

## Time-sensitive tasks
1. Verify actual Krok paid endpoints, historical AU/NZ form/results/sectionals and API quotas; don't invent access or coverage.
2. Capture **as much licensed historical data as reasonably possible** within the month, respecting provider terms, rate limits and costs. Store privately in user-controlled persistent storage with manifest/checksums/provenance and backup. **NEVER commit licensed raw records or API secrets to this public repo.** GitHub Actions artifacts are short-lived and not an archival solution.
3. Recover missing original V6 artifacts and pass the original integrity manifest before claiming genuine V6 is operational. V6 remains frozen. The linear research replay is UNAPPROVED / NO BET.
4. Fix/test live runner normalization, scratchings, AU+NZ meetings, race exclusions (maiden, 2YO, jumps unless expressly overridden), track conditions and prices; use NO BET liberally.
5. Track immutable timestamped pre-race selections vs actual results and TAB executable prices. Account for win-only, 2-horse quinella and 3-horse boxed trifecta separately, plus subscription costs. No retroactive edits, no fabricated edges.
6. Before the billing window closes, provide the user a clear evidence-based renewal/cancellation recommendation. One lucky week is not statistically convincing.

**Next Work session should explicitly acknowledge this handover and make the paid-month data collection a priority.**
