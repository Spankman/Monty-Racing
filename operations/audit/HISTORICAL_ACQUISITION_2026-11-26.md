# Monty historical acquisition and predictive science

26 November 2026 Brisbane · AU-RQ-AUTHORITY-20261126 · offline research.

## Decision and reviewed versions

Use Racing Queensland's free historical service to anchor same-event identities and build a trainer/jockey history pilot. This study measured improvements in retrospective identity coverage. Complete histories, pre-jump availability and incremental predictive value remain unverified.

Reviewed [canonical governance #234](https://github.com/Spankman/Monty-Racing/tree/51ba4febd3443eaec4f755777a65bee493e01821) at 51ba4febd3443eaec4f755777a65bee493e01821: Master Handover v1.1, AGENTS, Living Plan, Research Library, Betting Policy, Selection Rules, research/data permissions and owner extensions. Research #244 at 29239357579422148091a3320401d5e0572d774c and engineering #245 at fd901172448f0197b5adb69d8c196660a416f1f6 were reviewed along with #241–243 and the existing 2027 preregistration. #245's private evidence staging and source/custody requirements apply. #244 found positive trainer/jockey standalone signal, no demonstrated blend advantage, and unknown publication time on the original archive. Refit on that archive would not resolve the acquisition question. No model fit was performed here.

## A$0 acquisition

The [Racing Queensland public service](https://www.racingqueensland.com.au/opendatawebservices) lists meeting, race and horse-assignment endpoints. The [interface specification](https://www.racingqueensland.com.au/OpenDataWebServices/rq-open-data-web-services.pdf) identifies internal HORSES IDs, including trainer/jockey licensee IDs, and the public service's use terms. They are scoped to this issuer and system. No national Horse Code or ASB ID is inferred. General [website terms](https://www.racingqueensland.com.au/terms-conditions) apply separately to PDF/HTML material. Only source receipts and derived aggregates are published.

Sample 1–7 June 2025 to overlap the pinned Monty checkpoint. The calendar returned 20 meetings, 15 flagged non-trial. Tested Doomben, Ipswich, Eagle Farm and Kilcoy and used the first three numbered races at each successful meeting. Three meeting responses yielded 27 official race IDs. Kilcoy returned HTTP 200 with an XML application error and was excluded. The first Eagle Farm booklet alias failed, then the published meeting link provided the working filename. The three booklets were hash-pinned and reassembled by printed page before parsing.

| Verified coverage on nine matched archive races | Before in checkpoint | After pilot | Denominator |
| --- | ---: | ---: | ---: |
| RQ-scoped same-event race IDs | 0 | 9 | 9 races |
| RQ-scoped same-event horse IDs | 0 | 68 (70.10%) | 97 runner rows |
| Trainer IDs corroborated against archived assignment | 0 | 47 (48.45%) | 97 runner rows |
| Jockey IDs corroborated against archived assignment | 0 | 30 (30.93%) | 97 runner rows |
| Both roles corroborated | 0 | 20 (20.62%) | 97 runner rows |
| Strict historical training admissions | 0 | 0 | 97 runner rows |

The nine horse lists returned 135 declaration-like entries, including 120 trainer and 62 jockey IDs. The join counts measure agreement between two Racing Queensland artifacts and an exchange-based archive. This does not verify full field completeness or scratches. Unmatched entries in the 135 have unknown status. Linked runners: 68 distinct horses, 29 distinct verified trainers and 14 verified jockeys. No linked horse recurred across sampled races, so the pilot did not verify longitudinal horse history. Of 29 unresolved archive rows, 23 had a missing or ambiguous exact-event ASMX name and six had a missing, differing or ambiguous booklet saddlecloth/name.

The join required jurisdiction context, date, exact venue/race number/distance, a single exchange market, official race ID, a unique numbered entry with matching name in the booklet, a unique official horse within that event and matching printed weights between the two authority artifacts. Names do not create lifetime joins. Roles were checked against archive assignments separately. 59 linked barriers match the checkpoint and seven linked entries carry printed claim markers. Matching printed weights support identity reconciliation. Declared and carried weights and exact claim vintage remain separate questions.

November 2026 receipt times do not attest June 2025 pre-jump publication. The three full booklets contain **322 dated result-like lines for the meetings they describe**. Their current-day results and revised statistics cannot be used for those predictions. ASMX descriptions can reflect later changes as well. Preserve licensed source revisions, receipt times and hashes, fail closed on ambiguous identity, keep independently published official labels separate, and require provable release or first-seen times before admitting earlier revisions. The optional private local crosswalk export is 0600, with source hashes/times, explicit scope and unset historical publication time. No archive or frozen inputs were overwritten.

[Aggregate evidence](RQ_AUTHORITY_ACQUISITION_2026-11-26.json) · [23-source acquisition register](HISTORICAL_SOURCE_COVERAGE_2026-11-26.csv) · [79-feature coverage register](HISTORICAL_FEATURE_COVERAGE_2026-11-26.csv)

## Source priority and cost

| Priority | Source and potential research gain | Cost and gap |
| --- | --- | --- |
| 1 | RQ public ASMX and dated authority publications for stable roles, official starts and event revisions | A$0 in this pilot. Need repeated runner links, official outcome chain, historical publication times and cross-jurisdiction mapping. |
| 2 | Existing private Monty and authorised Krok archives, plus Betfair free AU files | No new credits. Original checkpoint passed 55 hashes. Prior 16-month Betfair evidence and May/July 2026 quarantines preserved. Exchange prices are a separate research series. |
| 3 | RQ sectional and position files and stewards archives. Racing Australia, state authorities, Australian Stud Book, Racing.com and NSW Punter's Intelligence for targeted claims, gear, interference, speed and pedigree leads | A$0 public sample. Rights differ. Public access does not prove lawful automated reuse or dated machine-readable coverage. No complete join tested. |
| 4 | PuntersEdge open September multi-book export and separately permitted existing FormFav/Krok records | Public PE export CC BY 4.0. Private APIs have separate terms. No new complete pre-cutoff named fixed-win vector qualified. |
| 5 | Author or rights-holder route for 2019–2021 replication data. Racing and Sports Group/Listed archives for secondary pedigree/result checks | No original paper dataset located and no request sent. Limited stakes coverage cannot substitute for a broad racing sample. |

No purchase recommended. The free state identity route works and existing archives have untested intersections. Reconsider a paid source only after a documented free-source gap and a permitted sample shows increased eligible races, correct timestamps, authority identifiers and retention rights. Compare cost per newly eligible race. Krok public page versions reported different paid prices, A$49/mo and A$79.99/mo. The owner's rate remains unverified. FormFav displays $50/month Premium for live prices, without established historical coverage or checkout currency in this audit. PuntersEdge private history and Betfair's registered archive have separate entitlements. No authenticated API use, billing action or purchase.

[Authority rights](https://www.racingaustralia.horse/AboutUs/TermsOfUse.aspx) · [Stud Book terms](https://studbook.org.au/TermsAndConditions.aspx) · [RQ stewards](https://www.racingqueensland.com.au/racing/race-day-stewards-reports) · [NSW sectionals](https://www.racingnsw.com.au/punters-intelligence/) · [Racing.com historical access](https://racing.zendesk.com/hc/en-us/articles/31361351167001-How-do-I-access-past-race-replays-or-results) · [Betfair free data](https://betfair-datascientists.github.io/modelling/dataSources/) · [Betfair historical portal](https://historicdata.betfair.com.au/) · [PuntersEdge export](https://github.com/Puntersedge-api/puntersedge-datasets) · [Group racing archive](https://www.racingandsports.com.au/breeding/stakes-races) · [FormFav tiers](https://formfav.com/pricing/) · [Krok pricing](https://krokodds.com.au/data-api/racing)

## Predictive science and December

[West–Kazakov replication requirements](WEST_KAZAKOV_REPLICATION_REQUIREMENTS_2026-11-26.md) map the paper's stated 22 inputs and 26 appendix entries. Missing original inputs include ratings, selected factor subset, start-of-day odds, closing-speed/pace data and fit details. The paper's morning odds are a market input. Its tested forecast is distinct from Monty's independent form arm. Keep #244's PLS adaptation, #242's Benter/conditional-logit/Harville benchmarks and calibrated market. No new model result or improved profitability claim is supported by these data.

1. First obtain initial declarations, changes/scratchings and official result revisions with source publication or independently receipted first-seen times. Use a small Queensland cohort and count eligible rows before expanding. Complete separate trainer/jockey histories and previous official run joins.
2. Test prior wins and beaten favourites with verified earlier starts and stated price semantics. Add subsequent gear/gelding, trip/class transition and trainer interactions only with dated observations. Do not infer these events from a later profile.
3. Keep pedigree, adjusted speed, pace, interference, adaptive weighting, modern challengers and Roughie Score in research. Require source-verified features, matched baselines and genuinely later testing. Preserve existing roughie thresholds.
4. **January prerequisites remain unmet.** The 4 January–28 March 2027 Queensland window remains locked and unopened. Preserve the existing through-29-November fit cutoff and 1–27 December calibration window. Later recovery may establish earlier existence with matching immutable evidence. It cannot move those cutoffs. No qualifying complete named fixed-win book, settled outcome chain or locked candidate manifest was produced here. No shadow forecasts run. If the gates cannot be met at the registered freeze, record BLOCKED and avoid backfill.

## Reproduction and engineering handoff

Use the historical source hashes in the aggregate and the original frozen checkpoint. Preserve captured bytes in the approved private workspace. Put the aggregate capture_attempts array into receipts-private.json. Later server responses with different hashes are new observations and cannot recreate the original. Run from repo root:

```sh
PYTHONPATH=.:monty_v6 python -m unittest -q test_rq_authority_pilot test_identity_crosswalk test_historical_asof
PYTHONPATH=.:monty_v6 python -m operations.audit.rq_authority_pilot --captures PRIVATE_CAPTURE_DIR --archive monty_v6/results/joined_development_runners.csv.gz --output PRIVATE_OUTPUT.json
```

11 targeted checks passed. Two local runs on preserved bytes produced identical aggregate output. SHA-256 4f80ae24929d8c606c3e18f68c030578a391d8870d5bbb9f404748669539b900. Codex should supply authority revisions, role-specific denominators and evidence vintages through #245's existing private contract after permissions are confirmed. No live provider API credits used, purchases, trial action, model fitting, wagers, deployment, merge or rules change. V6 official/frozen and V7 research-only.

IN MONTY WE TRUST.
