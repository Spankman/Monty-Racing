# FormFav and TAB source integration

`formfav_client.py` reads `FORMFAV_API_KEY` from the process environment. Never
commit a key or save it in reports. It captures AU/NZ thoroughbred cards and
account tier/quota with bounded requests, cached cards, no automatic retries,
no redirects carrying authentication, and no provider prediction requests.

```sh
python formfav_client.py --date 2026-11-18 --output-dir race_day_output/formfav-2026-11-18
```

Use `--refresh` for a deliberate one-time refresh; cached cards may have stale
scratchings. This command is not a scheduler or a live odds feed.

The account was verified as Pro. Pro returned speed maps and class profiles;
the free capture covered 43 AU/NZ races. These proprietary model assessments
are not substituted for original Monty V6 features. Pro results supplied
official starting prices, not the scheduled-off best-back market required
by the original historical feature contract. Career totals and form strings
are not a complete dated retained-history dataset.

`formfav_inputs.merge_card` checks complete active fields against saved odds.
`reconcile_tab` can apply a rendered complete TAB card only after checking
host, date, meeting, race, unique saddlecloths and every runner name. It records
scratching disagreements and uses the TAB barrier, scratching and fixed-win
quote. TAB observations contain read-only rendered page data; there is no
hidden API or authenticated TAB session integration.

## Verified 17 November, for 18 November

- Refreshed all 35 Australian TAB races: 450 entries, 416 active, 34 scratched.
- Capture window: 18:24–18:29 Queensland, 17 November 2026.
- Resolved 22 scratching disagreements with FormFav's older cards. TAB confirms
  Fammi scratched in Sandown R3. Current prices now account for that withdrawal.
- Reran original frozen V6 on all 416 active runners, with 13–21/43 active
  features observed. All 55 original artifact entries still verify.
- Cumulative horse/market residuals, connections residuals and connection
  changes remain missing. No retraining, research-pickle loading or provider
  prediction substitution occurred.
- NZ cards are cached separately; the AU-trained baseline remains unvalidated
  for NZ and this reconciled rerun excludes NZ.

This is an audited research pipeline, not a fully informed betting service.
FormFav Pro does not by itself solve the original historical market contract.
TAB browser capture is a practical one-time refresh, not the desired fast
unattended live feed. Do not call sparse-input rankings validated value bets.
