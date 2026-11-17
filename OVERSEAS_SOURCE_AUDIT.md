# Overseas source pilot — 17 November 2026

## Outcome

No overseas source observation was admitted to Monty's inputs in this pilot.
No current 18 November AU/NZ Sky past-performance guide was retrieved, so no
current-runner historical join or model rerun was warranted. Existing provisional
runs remain valid under the user's permission to use trained missing-value defaults.

## Actual checks

| Route | Evidence | Decision |
| --- | --- | --- |
| Sky Racing World, US | Search-rendered Warwick March 2026 PDF exposes dated runs, going, class, distance, finish, jockey/barrier, weight and Off prices. Homepage and direct PDF download returned HTTP 403; direct files host sample also returned 403. | Format promising, current file acquisition unverified. Search-rendered text is not an authenticated downloadable source file. No access-control bypass attempted. |
| Sky second sample AU2pp0309 | Search text includes harness starting-position notation, Fr/Sr and handicapped yards. | Do not infer thoroughbred code or meeting identity from an AU filename. |
| Capital OTB, US | Public tip-sheet page currently displays AU/NZ sheets through 13–14 November; full past performances advertised free for members. | No current 18 November historical-form file obtained. Tip sheets are not model inputs. |
| Hollywood Races, US | Public international PP page rendered 12 November listings (France, South Africa, UAE). | No relevant current AU/NZ file obtained. |
| iRace, Singapore | Scone 17 November racecard fetched HTTP 200 (1,327,896 bytes). Public HTML contains 28 occurrences of 08May24; rendered Smart Scud, Think Back and Admire Me sections repeat identical May 2024 Warwick Farm and November 2023 Rosehill runs. | Reject displayed histories pending independent validation; could be page/template or extraction error. Do not attribute those runs to the horses. |
| iRace PDF | Observed link opens a two-page Scone express-form PDF with fields, previews and aggregate statistics. | Accessible publication, but not the dated full-run history needed for original residual features. No tips used. |

## Compatibility requirements

- Verify Australian local date, meeting, race number, horse identity and racing code.
  US publication dates/times and imperial units require explicit conversion.
- Validate jockey/trainer roles against the original PDF layout; rendered text can
  label jockey lines as trainer lines.
- Separate trials from actual retained eligible races. Career totals and L50/L350
  percentages are not original V6 retained-universe or 90-day/year residuals.
- Off, SP, morning-line and BSP prices are not established equivalents of
  BEST_AVAIL_BACK_AT_SCHEDULED_OFF. Preserve original Betfair historical quotes.
- Reconstruct market residuals only from complete reconciled retained fields.
- Missing features alone do not veto a provisional Monty run.

## Source links

- https://www.skyracingworld.com/download-file?fileName=WAWpp0309.pdf&mDate=2026-03-10
- https://www.skyracingworld.com/download-file?fileName=AU2pp0309.pdf&mDate=2026-03-10
- https://files.skyracingworld.com/files/ADpp0106.pdf
- https://www.capitalotb.com/handicapping/
- https://www.capitalotb.com/handicapping/tip-sheets/
- https://www.hollywoodraces.com/horse-betting/free-international-past-performances/
- https://www.irace.com.sg/form-guide/race-card/?gtag=australia&meetingname=Scone&racedate=2026-11-17&racemeet=AUS&racerefid=40105
- https://www.irace.com.sg/wp-content/uploads/2026/11/AUS_EXPRESSFORM_171126_SCO.pdf

No credentials, third-party datasets, model weights or historical records are
included in this audit. No subscription purchased or provider contacted.
