# Roughie concentration audit · 25 November 2026

**Finding.** All 12 V6 watches at $10 or longer and both V7 watches at that cutoff would have appeared with normalized market probabilities alone. Small model adjustments exist and the two engines genuinely scored the runners. This incident supplies no independent evidence of predictive value or executable book-level edge. Preserve the original official NO BET.

## Frozen incident and coverage

Requests #221–224 reused one exact forecast, run `45551033605-1-221`. SHA-256 matches the request metadata and receipt. The downloadable Actions ZIP matched its published SHA-256 and carried the same public result bundle. The production wrapper recorded 25 scores in each engine, plus one blocked race record (Wyong R5). The same capture generated all four views. Count overlapping views once.

The public production archive removed most full-field rankings. Recovered prices and probabilities are the consistent union of its saved runner selections, watches and best chances. Only two races retained every internally counted active price. `race_books.csv` records every race, complete book percentage where recoverable and a mathematical lower bound elsewhere. Of the other 23 scored races, four were provably overround from their observed prices alone (Geelong R7, Launceston R5/R8 and Wyong R7). Nineteen are indeterminate. Wyong R5 is an additional unscored record. A blank totals cell means incomplete evidence. No odds from other capture times were used as substitutes.

| Race | Archived active prices | Book % | Overround (negative = underround) | Apparent market-only edge per runner | $10+ watches V6 / V7 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Geelong R8 | 10/10 | 95.924% | −4.076 pp | +4.249% | 5 / 0 |
| Launceston R6 | 9/9 | 72.746% | −27.254 pp | +37.464% | 7 / 2 |

For decimal odds o, sum inverse odds to get the book S. The normalized market probability is (1/o)/S. Using that same price to compute value gives p × o − 1 = 1/S − 1 for every runner. A book below 100% gives every runner positive arithmetic edge even without any model uplift. The shared 6% V7 minimum probability admits the Launceston $10 and $21 runners in the market-only control, while the remaining $10+ runners fall below it. The Geelong $10+ runners also fall below it. These existing engine rules apply across the field and neither the audit nor its test cohorts cap watches per race or meeting.

| Shared watch | Normalized market | V6 | V7 | V6 uplift | V7 uplift |
| --- | ---: | ---: | ---: | ---: | ---: |
| Go Jeanie at $10 | 13.746% | 13.866% | 14.062% | +0.119 pp | +0.316 pp |
| Sh'bourne Midnight at $21 | 6.546% | 6.460% | 6.854% | −0.086 pp | +0.308 pp |

V6 rated Sh'bourne Midnight below the normalized market and still returned a +35.66% same-price edge. That is direct evidence that overlapping watch status does not establish independent agreement about runner uplift. Across the 12 V6 watches, the largest absolute model-minus-market difference was 0.120 percentage points. Requiring positive model uplift as well as positive edge would remove one of the 12 and retain 11, most on very small differences. The runner CSV shows every recoverable runner price and model probability, and normalized market comparisons wherever the whole price vector was recoverable. Blank V7 cells are unavailable probabilities. Even for the two complete odds vectors, the archive does not retain full V7 arrays.

## Quote and field integrity

* Both target races had a race-level `TAB (Krok attributed)` label. The original adapter preferred the first valid TAB-tagged price for each runner, with fixed/best-win fallback when no tagged price was found. There is no affirmative evidence of mixed bookmaker labels for these races. Independently synchronized quotes, quote update timestamps, raw alternate quotes and the exact upstream TAB field were unavailable. Race-level attribution alone does not establish a coherent executable book.
* The snapshot was captured at 15:05 Brisbane and expired at 15:10. Capture freshness is distinct from individual quote freshness. No evidence identifies the age of each offer or whether all were simultaneously available.
* Geelong's three and Launceston's one provider-reported withdrawals are absent from their recovered active quote vectors. The internal active count reconciles in both. No authority-confirmed field was available at capture, so this does not rule out late withdrawals, missing external runners, duplicate upstream offers or stale prices. The same-number runner cells retained in the result do not conflict across views.
* The stored scheduled jumps were 17:30 and 19:57 Brisbane. This check took place before those times. No result or actual profit was assigned to the incident.

## Historical recovery and settlement sensitivity

Earlier official Betfair monthly exports supplied 24,797 retained AU markets from May 2025 to October 2026. There were 866 scheduled-off snapshot underrounds (3.49%). 588 were at or below 95.92% and 92 at or below 72.75%. A market-only V6-style control produced at least five $10+ watches in 626 races. The recovered sample supplies official outcomes, scheduled-off exchange best-back snapshots and Betfair SP. These are distinct from TAB fixed odds and neither simulated fill represents actual wagering. Five or more watches is an audit slice only.

| Replay arm | Watches | Winners | Snapshot ROI | Betfair SP ROI |
| --- | ---: | ---: | ---: | ---: |
| Market-only V6-style, 626 clustered races | 4,435 | 199 | +20.97% | −3.27% |
| Frozen V6, all 1,787-race replay watches | 4,047 | 160 | +1.76% | −10.05% |
| Frozen V6, 212 clustered races | 1,292 | 54 | +41.13% | +5.64% |
| Frozen V6, clustered non-underround races | 990 | 35 | −17.92% | −18.57% |
| Frozen V6, clustered positive uplift and positive edge | 1,070 | 38 | −18.27% | −18.43% |

Equal one-unit stakes and 5% commission on each winning return. Commission convention is a proxy, particularly for multiple positions in a market. The frozen V6 replay overlaps part of the monthly scope and uses an already-exposed period. One winning snapshot quote at $650 contributes 616.55 net units, more than that clustered arm's entire 531.38-unit net profit. Pricing and return concentration undermine a durable edge claim. The Betfair SP sensitivity is not a verified fill simulation. Independently timestamped fixed-price tickets and settlements are still needed. A historical V7 model replay for this watch rule was not performed. The evidence JSON includes the V7-style **market-only** control and must not be read as V7 model performance.

## Safeguards and delivery

The audit separates full-book percentage, raw numerical edge and model uplift versus normalized market. It refuses normalization under missing field coverage or conflicting rows, and tests the existing verification gate against missing prices, mixed operators, moved prices, stale captures and changed withdrawal status. A future independently captured underround can warrant a data-quality review without a hard-coded roughie quota. Before promotion, require a complete independently matched field, named contemporaneous executable quotes and their observed times. Keep anomalous-book watches diagnostic until verified. Compare uplift and executable edge prospectively before proposing thresholds. Rejecting underrounds or adding an uplift threshold permanently would need evidence and owner approval.

Verified the saved production text and HTML against a replay through the #213 draft at the original valid timestamp. Production official views hid the watches. Draft views retain all 14 V6 diagnostic watches (12 at $10+) in official and provisional text/HTML and all seven V7 diagnostic watches (two at $10+) in official, shadow and provisional text/HTML. Compact delivery preserves the same counts. All replayed views suppress the watches after expiry. HTML repeats the text in the copy box. No quota or production thresholds changed. V6/V7 artifacts remain frozen and #213 stays unmerged.

[Source forecast](https://github.com/Spankman/Monty-Racing/blob/monty-operations-results/runs/2026-11-25/45551033605-1-221/forecast.json) · [Workflow artifact](https://github.com/Spankman/Monty-Racing/actions/runs/45551033605/artifacts/14993691756) · [Race books](roughie_evidence/race_books.csv) · [Runner comparisons](roughie_evidence/runner_comparison.csv) · [Historical evidence](roughie_evidence/results.json)
