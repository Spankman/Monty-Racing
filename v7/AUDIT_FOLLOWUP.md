# Candidate 2 audit follow-up

Research only. Candidate 2 and all diagnostic outputs remain unapproved. No wagers were placed. The operational shadow workflow uses 0% expert weight.

## Evidence and evaluation

Run `python -m v7.reconcile --date YYYY-MM-DD --decision-at <UTC-timestamp> --krok <receipt> --fixtures <receipt> --quotes <receipt> --output <new-file.json>`. See the module docstring for normalized records. Each receipt has `raw_file`, `raw_sha256`, `normalized_file` and `normalized_sha256`. An independent reviewer must establish source origin, normalized field accuracy, complete capture scope and the ID crosswalk. Each capture must represent one information vintage. Archive each vintage separately. A SHA-256 verifies bytes against a receipt. Source attribution, completeness, publication timing and data rights require separate verification.

Use the output JSON with `python -m v7.predict` for Candidate 1 or 2 research. Legacy CSV is provisional and exported feature columns are ignored by the scorer. The reconciled card supports race class and going encodings. Additional earlier-available form and weight inputs still need licensed, timestamped releases and stable IDs. The Krok CLI can archive original HTTP response pages and hashes. Its capture receipt leaves publication time unresolved until supported by source evidence.

Use `python -m v7.holdout --help` for the locked paired comparison. It reports AU and NZ separately when scored fields are available, with separate inputs and reports for exchange proxies and bookmaker fixed win. The benchmark must equal normalized inverse odds for the same field. Win returns use one simulated unit and assume the verified price is the settlement price. Actual paid returns, deductions, dead heats, exotic settlement and changed-field payout evaluation need bookmaker settlement records. Missing and excluded races remain in the reconciliation and holdout audits.

The Racing Queensland pilot fetched the 21 November Sunshine Coast sectionals CSV over HTTPS (HTTP 200, 27,639 bytes). The official listing covers several venues, including Sunshine Coast, Toowoomba and Kilcoy. The capture establishes current availability only. Original publication timing, a stable ID crosswalk and usable data rights remain unresolved. Racing Queensland's terms limit use and reuse. The pilot payload stayed out of the repository and model inputs. [Listing](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals) [Terms](https://www.racingqueensland.com.au/terms-conditions)

Betfair's AU/NZ index was reachable. Scheduled-off best-back quotes remain an exchange proxy. No new dated official Betfair cohort was integrated. LOVERACING.NZ RaceInfo returned HTTP 403 from this workspace. No data was purchased. [Betfair index](https://betfair-datascientists.github.io/data/dataListing/) [LOVERACING.NZ](https://loveracing.nz/raceinfo)

## Workflow map

| Entry point | Engine and scope |
| --- | --- |
| `monty-v6-readiness.yml` | Frozen V6 integrity and readiness. Full scoring requires the private archive. |
| `monty-daily-research.yml`, `monty-race-research.yml` | Sparse frozen V6 linear replay. The daily job also builds the shadow blend at 0% expert weight and emits its own research ladder report. |
| `python -m v7.predict` | Candidate 1 or Candidate 2 based on the selected frozen model artifact. Offline and research only. |
| `monty-v7-daily.yml`, `monty-v7-single-race.yml`, `monty-issue-request.yml`, `monty-poll-race-requests.yml` | Separate provisional engine from `grok-independent-repairs`. The daily wrapper now rejects unresolved or conflicting provider country. Its legacy dated fixture count input cannot verify fields or named prices. The external engine's single-race selection, watcher and comment output are separate from the frozen-linear research entry points. |
| `monty-ci.yml` | Offline code checks at the event checkout. A separate job explicitly pins the external provisional engine at `efc51abb1595ef1eb8417e2d4e0d591f6d3c9378`. |

## Preservation and unresolved evidence

- All 27 available V6 manifest files match their declared hashes. The 28 absent entries include `results/april_recovery/input_manifest.json`, `results/frozen_feature_matrix.npz`, `results/joined_development_runners.csv.gz`, and `results/diagnostic_predictions.csv.gz`. The checkout cannot replay the 1,787 races or rebuild the audited Candidate 1 and Candidate 2 predictions. The original Candidate 1 runner-level predictions and source warm-up files are also needed.
- The separate Ballina card is dated 23 November. Its receipt requires `ballina_frozen.json` with SHA-256 `29728e9b16dfd1184585d6825801eaeffb5d62129fabaa175db22ee35165f51b`. Keep the original forecast outside the checkout. Use `python -m v7.shadow --forecast <path> --receipt <receipt>` to verify its bytes before importing results.
- Complete AU/NZ TAB cards with race and runner ID crosswalks, named fixed-win captures and official settlement evidence remain necessary for held-out evaluation. The audited period is already exposed. Candidate 2's archived common-period loss is 18.9755 units on 124 exchange-proxy selections, with 1.818081 log loss on 1,787 races. These are saved outputs. [Archived comparison](candidate2_artifacts/comparison.json)

## Independent review update

The independent reviewer verified all 55 frozen V6 artifact hashes and replayed
1,787 races. The earlier 27-file check describes the public checkout only. The
reviewer also matched the original 18 November forecast bytes to the published
SHA-256 `d5ac93d09ce8a294a398206c250ffd4fced719f62b596853eaac75ed02cd786e`.
These were independent checks reported to this follow-up. The private archive
and forecast bytes remain outside this checkout.

The provisional daily and single-race workflows pin the same separate engine
commit and preserve explicit runner evidence and roughie flags from its scored
CSV through the shared ladder. Missing evidence stops the ladder. Krok-only
runs continue to report unverified evidence and NO BET. Each workflow writes
identical visible Markdown and JSON `copy_text`.

## 18 November shadow settlement

The supplied settlement record reconciled all 35 races against the original
forecast SHA-256 above. Zero results remain pending. Scratchings changed 27
frozen fields, leaving eight races eligible for paired probability scoring.
Frozen V6, V7 Candidate 1, V7 Candidate 2 and the market each picked three
winners on those eight races. Candidate 2 matched the market's log loss.
The card contained zero wagers and provides no exotic payout validation.

## Next prospective shadow run

Declare the schedule in UTC before the card. Capture the Krok field, an
independent official TAB field with explicit scratching dispositions, and a
named fixed-win book after T−5 minutes. Freeze each race by T−1 minute using
the independently confirmed scheduled jump. An independent reviewer checks
capture provenance, timestamps, full field and publication evidence plus the
runner ID crosswalk. Retain the original provider bytes, each later capture
and its receipt in private storage outside the GitHub checkout.

Run `python -m v7.near_jump_shadow --date YYYY-MM-DD --country AU --race-id <TAB-ID> --krok <receipt> --fixtures <receipt> --quotes <receipt> --scored <scored.json> --output <new-private-attempt-dir>` for each race. The scored JSON has `rows` in `v7.shadow.freeze` format and `models` identifying the frozen models. Score the freshly reconciled active runners at the named prices. The gate writes `attempt.json` for each attempt, including skipped races and reasons. A successful attempt writes an immutable `forecast.json` and includes its receipt in `attempt.json`.

After jump, preserve official dispositions separately. Reconcile with `v7.shadow` using the `receipt` object from `attempt.json` saved to a separate receipt file. The result records changed fields and excludes them from paired probability scoring. Keep every attempt research only and NO BET.

The offline fixtures exercise the freeze and settlement gate. A live attempt
requires a Krok credential and dated, independently reviewed near-jump TAB
scratching and named fixed-win capture receipts. Those inputs were unavailable
for this follow-up.
