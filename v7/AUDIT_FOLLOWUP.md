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
- The 18 November card requires `2026-11-18_AU_frozen.json` matching the committed receipt, official results and scratching dispositions for all 35 races. The separate Ballina card is dated 23 November. Its receipt requires `ballina_frozen.json` with SHA-256 `29728e9b16dfd1184585d6825801eaeffb5d62129fabaa175db22ee35165f51b`. The receipts are available. Original forecast files were absent from the checkout and the inspected Actions artifact. Use `python -m v7.shadow --forecast <path> --receipt <receipt>` to verify bytes before importing any results.
- Complete AU/NZ TAB cards with race and runner ID crosswalks, named fixed-win captures and official settlement evidence remain necessary for held-out evaluation. The audited period is already exposed. Candidate 2's archived common-period loss is 18.9755 units on 124 exchange-proxy selections, with 1.818081 log loss on 1,787 races. These are saved outputs. [Archived comparison](candidate2_artifacts/comparison.json)
