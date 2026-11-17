# V7 source and access audit — 17 November 2026

No provider predictions or tips were used for training. The historical training
input remains the genuine preserved AU V6 archive, with original warm-up history.
New evidence must pass `evidence.join_evidence` before any future model can use it.
That interface is implemented, but a generic contract is not a completed live feed.

| Requirement | Legitimate source / documented access | This development run |
| --- | --- | --- |
| AU sectionals, pace, position | [RQ thoroughbred sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals) publishes dated PDF, CSV and ZIP links. Different page from harness/greyhound. | Verified official listing and observed 14 Nov Doomben CSV link. Direct CSV fetch returned 403. No sectionals ingested; no bypass. |
| NZ sectionals | [Auckland Racing](https://www.aucklandracing.co.nz/racing-information/sectional-times/) publishes per-race sectional links, with 2025/26 history. | Listing verified. NZ identity joins and full finishing-order data not yet imported. Historical listing alone does not prove original publication time. |
| International tracking and sectionals | [TPD API](https://www.totalperformancedata.com/live-pr-api/) includes sectionals history and post-race feeds. [Coverage](https://www.totalperformancedata.com/racetrack-coverage/) lists ten Victorian tracks as well as overseas jurisdictions. | Documentation verified; account/licensed access required for an authenticated data pilot. No purchase or contact made. International horse/race performance is not assumed transferable to AU/NZ. |
| Interference, vet issues | [RQ stewards reports](https://www.racingqueensland.com.au/racing/race-day-stewards-reports), [QRIC](https://qric.qld.gov.au/stewards-reports), [NZ RaceInfo](https://loveracing.nz/raceinfo) | Discovery verified, not an imported tagged history. Only reports from prior races may inform a future start, with original availability and manual/verified tagging. No invented interference scores. |
| Track bias | Prior published race results, barriers, pace and rail/condition observations | No verified historical bias series. Estimate from earlier available events with shrinkage in a future experiment; never infer today's bias from later results or silently call a barrier feature track bias. |
| Weather | [Open-Meteo single forecast runs](https://open-meteo.com/en/docs/single-runs-api) exposes run initialization and global ECMWF history from March 2024. | Documentation verified. Run initialization is NOT the time a forecast became available: require verified release/ingestion time before decision. Track coordinates and availability history not yet reconciled. Reanalysis/actual future rainfall is forbidden as a pre-race forecast feature. |
| Jockey/trainer | Existing FormFav Pro client, cached 90-day/year statistics; original V6 chronological market residuals | Genuine original residuals used in training. Current FormFav strike rates remain supplementary and cannot replace market residuals. No key copied into V7. |
| Historic market prices | [Official Betfair AU/NZ CSVs](https://betfair-datascientists.github.io/data/dataListing/) and existing importer | Original scheduled-off best-back prices used for baseline and proxy ROI. Monthly lag and full metadata remain limitations. BSP/SP/morning line not substituted. |
| Current prices | Existing TAB fixed-win captures and FormFav adapter | No fresh odds run in this V7 assignment. Quote capture time is recorded; bookmaker update timestamps are not mandatory under Ferg's policy. |
| Overseas public guides | Sky Racing World, Capital OTB, iRace | Prior `OVERSEAS_SOURCE_AUDIT.md` applies. Current Sky retrieval unverified/403, iRace duplicate-history evidence rejected. No fabricated matches. |

The evidence contract separates source availability, publication, capture and
event timestamps. A sectionals/pace/interference report describes a **previous**
race. A weather forecast may target the upcoming race, but must have been
available before the betting decision. Unavailable observations remain missing;
they do not prevent a provisional model run with trained imputation.
