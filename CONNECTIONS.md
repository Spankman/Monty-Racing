# Historical metadata and connection-statistics enrichment

`collect_connections.py` captures only the unique jockeys/trainers appearing
in the supplied fields, for 90-day and 365-day windows. Each source response is
cached separately. It also retrieves the historical Betfair markets referenced
by the already-verified latest-start audit. Credentials come only from
FORMFAV_API_KEY; there are no provider-prediction requests, retries or schedules.

`connections_enrichment.py` validates market/date/venue, retained runner IDs and
names against the canonical Betfair history. Extra metadata entries do not
expand the retained field. Blank or abbreviated people remain unknown.

The only new model input is `jockey_changed`, and only where the prior actual
PDF start had already been verified as the latest eligible retained start and
the current full-name booking is corroborated by the captured TAB display.
Full names are normalized using the original model helper. Current TAB prices
and previous source records remain unchanged.

FormFav aggregated statistics are written separately to
`connections_supplement.csv` with `support_` column names. They are never used
as jockey/trainer market residuals. Ambiguous people, mismatched windows and
unavailable records have explicit statuses and do not become invented zeroes.

## Execution

Both commands consume private source files. Every input path is explicit;
outputs should stay in ignored `race_day_output/` or private report storage.

```
python collect_connections.py --inputs inputs.csv --cards source_cards --latest enrichment_audit.csv --output-dir race_day_output/connections --date 2026-11-18
python connections_enrichment.py --inputs inputs.csv --history canonical_history.csv.gz --latest enrichment_audit.csv --bindings race_day_output/connections/runner_connections.json --observations tab_observations.json --cache race_day_output/connections --output-dir race_day_output/enriched
```

## Actual first enrichment

The 18 November saved Australian snapshot has 416 active runners in 35 races.
All 80 relevant historical markets passed retained-ID/name/date/venue checks.
Verified jockey-change inputs were added for 92 runners. Coverage now ranges
13–22/43 active features. Original artifacts and preprocessing are unchanged.
All 55 manifest entries verify. The rerun changed one race's leading win
probability ranking: Belmont R5, Von Rommel to Arizona Sky. This is a
provisional ranking, not a claim of proven betting value.

The source odds are the saved TAB fixed-win capture from 17 November,
18:24–18:29 Queensland. This enrichment is not a new price refresh.
Historical expected-win sums, full cumulative histories and trainer-change
metadata remain incomplete. Missing inputs use the trained imputation and do
not veto provisional runs under SELECTION_RULES.md. No retraining occurred.
