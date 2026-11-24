# AU verification pilot · Ipswich R5 · 25 November 2026

**Decision: DATA BLOCKED.** This is a reconciliation of archived inputs. Admission to prospective scoring requires a fresh, complete provider snapshot and independent verification in the same pre-jump window.

| Check | Result |
| --- | --- |
| Race identity | Racing Queensland lists Ipswich R5 as 1666 m, Soft 5 turf, jumping 3:23 pm Brisbane. The archived provider jump time agrees. |
| Declared field | The archived provider forecast lists 11 active runners. Racing Queensland's fields PDF lists 11 ordinary entries and two marked emergencies. The authority web page shows five scratchings. The provider records the same five plus the two emergencies as scratched. Final reserve status was not independently established at the provider capture time. |
| Freshness | The 9:14 am Brisbane provider snapshot has expired. The public authority page is useful for factual corroboration but does not establish contemporaneous queue-time odds. |
| Bookmaker | The dated TAB route did not expose usable quotes through public retrieval. No independent fixed-win attestation. |
| Settlement | No fresh verified forecast was admitted to the prospective cohort. No pilot ROI, strike rate or calibration claim. |

Sources: [Racing Queensland race page](https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/ipsw/20261125/race/5) · [archived provider-derived evidence](https://github.com/Spankman/Monty-Racing/actions/runs/45508147641/artifacts/14974930827) · [dated TAB card](https://www.tab.com.au/racing/2026-11-25).

## Identity crosswalk

All 11 active names matched multiple distinct Betfair selection IDs in the available May 2025–October 2026 official monthly exports. A loose search normalized case and whitespace and dropped a terminal uppercase country suffix. It was used only to count candidate IDs. Each name matched 3–13 IDs. None was accepted as an identity link. The reviewed November forecast does not supply usable stable Krok entry IDs, and the Racing Queensland race card does not establish registration IDs. The November monthly Betfair export was unavailable in the audit.

`identity_crosswalk.resolve` accepts reviewed evidence only. The canonical race key includes jurisdiction, local date, venue, race number and distance. It requires matching saddlecloth and normalized name with identical suffixes, source-specific IDs, evidence references and offset-aware timestamps no later than the decision cutoff. Conflicting registrations and duplicate records fail closed. Krok entry links are race-scoped. Keep unverified candidate names out of model inputs.

For a prospective run, obtain the evidence above for the same race and retain the source snapshots and their hashes. Publish only the verification outcome in the pilot ledger. Once the price, freshness and runner checks pass, freeze Monty's and the market's forecasts before jump and settle both against the same result. V6, V7 and the operational workflows are otherwise unchanged.
