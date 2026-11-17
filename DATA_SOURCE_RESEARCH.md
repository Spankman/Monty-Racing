# Missing-feature source research — 17 November 2026

Missing features alone do not veto a run or provisional selections. Use the
frozen model's saved imputation, disclose gaps and keep seeking compatible data.
Do not silently reinterpret historical features when a source offers a different
statistic. This investigation did not buy subscriptions, send messages or change
the model. No API credentials or third-party runner data are published here.

## Sources and realistic fit

| Source | What it can supply | Fit and unresolved limits |
| --- | --- | --- |
| [Betfair historical CSVs](https://betfair-datascientists.github.io/data/dataListing/) | Full race fields, runner IDs, outcomes and scheduled-off exchange back quotes | Already imported and parity-tested. Strongest fit for original historical market probabilities; monthly publication leaves recent-data gaps. |
| [Betfair metadata tutorial](https://betfair-datascientists.github.io/tutorials/automatedBettingAnglesTutorial/) | A public Hub endpoint linked by Betfair provides historical runner IDs, barriers, jockeys and results | Four live samples returned HTTP 200. Two complete field ID/name sets matched exactly; two included extra entries requiring reconciliation. Trainer and going were missing in these samples. The endpoint is described as unsupported; no reliability guarantee. Its BSP prices must not replace scheduled-off CSV quotes. |
| [FormFav jockey stats](https://formfav.com/docs/endpoints/jockey-stats) and [trainer stats](https://formfav.com/docs/endpoints/trainer-stats) | Already-held Pro access; career, course, condition and recent-window splits, including selectable 90-day/year windows | Useful supporting evidence. Aggregated strike rates lack the expected-win sums and exact retained universe for V6's market-adjusted residuals. Preserve them as separate source observations unless exact formulas can be reconstructed. |
| [Punting Form form API](https://docs.puntingform.com.au/reference/form-1) | Batch whole-meeting form, up to ten previous runs per horse | Current docs say Starter and up. Starter pricing page shows $59/month. Does not by itself establish full historical feature parity. Older developer page says Pro; confirm entitlement before buying. |
| [Punting Form Modeller](https://www.puntingform.com.au/pricing) | Advertises optional modelling-ready point-in-time data and historical Betfair prices/fluctuations | Most relevant paid candidate for a combined dataset. Sales quote; samples, historical depth, AU/NZ coverage, IDs and exact scheduled-off quote semantics remain unverified. Starter price does not imply this historical package is included. |
| [Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data) | Official QLD form, fields, jockeys, trainers, conditions and results in published pages/files | Free cross-check and metadata source. The published limited API is for calendar/club details, not a verified national bulk form API. |
| [LOVERACING.NZ RaceInfo](https://loveracing.nz/raceinfo) | Official NZ horse performances, fields/results, rider and trainer profiles | Good NZ reconciliation source. A bulk API and exact historical exchange-quote compatibility are not verified; NZ model validation remains a separate issue. |
| [Racing and Sports company description](https://lb-oci.racingandsports.com/faq/our-company/overview/453739) | Free detailed form/PDFs and commercial wholesale racing data | The supplied PDFs were parsed. Direct website access was challenged in this browser; licensed API access and pricing have not been established. No safeguard bypass was attempted. |

## Pilot evidence

Tested the Betfair Hub route on four retained October markets (Gatton, Doomben,
Ascot and Randwick). All four returned JSON. Gatton and Doomben had exact full
runner ID/name sets; Ascot and Randwick each returned one additional runner.
Missing trainer fields and empty going prevent claiming complete metadata.
Raw samples and identity audits remain in private ignored output.

## Recommended order

1. Use the FormFav Pro access already held for supplemental jockey/trainer
   90-day/year statistics; label those separately from original V6 residuals.
2. Pilot Betfair CSV + same-source Hub metadata joins by market/selection IDs,
   checking dates, names, outcomes and extra entries. Keep the original quotes.
3. Fill missing trainer/going metadata from official published form and results
   using complete-field reconciliation; retain unknowns when uncertain.
4. Ask for a Punting Form point-in-time sample and explicit scheduled-off price
   definition before recommending another paid subscription. No contact has
   been sent and no purchase has been made.

These are source-capability findings, not a claim that new historical features
have already been integrated into a Monty run.
