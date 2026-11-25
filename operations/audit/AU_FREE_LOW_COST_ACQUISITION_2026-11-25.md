# Australian thoroughbred data acquisition · 25 November 2026

**Decision:** Target A$0 for authority, historical and optional form research. Retain the existing Krok access until a separately measured Free trial shows acceptable coverage and freshness. A zero-cost verified live bookmaker workflow remains unproven. There is no evidence that production depends on paid FormFav. Test Free against an entitled sample before deciding whether to give up any private subscription features. All work is research-only.

[55-feature matrix](AU_FREE_DATA_55_FEATURE_MATRIX.csv) · [Source availability and reliability register](AU_FREE_SOURCE_REGISTER_2026-11-25.csv) · [Krok racing endpoint inventory](KROK_RACING_ENDPOINTS.csv) · [Prior AU live validation](AU_DATA_RECOVERY_FOLLOWUP_2026-11-25.md)

## Verified retrieval and feature reuse

| Source | Actual sample | Monty use |
| --- | --- | --- |
| Krok hosted account | Meetings and one field-form request returned HTTP 200. Meetings cost 1 credit on one page, with 44 AU races, 39 returned meetings across jurisdictions and 11,841 WIN offer records with bookmaker and per-offer captured_at fields. Field-form cost 5 credits. Headers showed a 500/minute limit and 49,419 remaining afterward. | Production primarily uses meetings. Existing field-form and result probes are research pathways. Selected model quote extraction currently recognizes quoted_at/updated_at and does not recognize this nested capture field. Validate format, actual age, precise selected-price binding and observer versus bookmaker semantics before adapting it. Preserve existing integrity rules. |
| Krok archived Free samples | Field-form HTTP 200 with 14 runners, jockey/trainer, draw, form and three sectional entries. Dated results HTTP 200 for 16 November 2026 and 17 November 2025. Returned entries included identity, outcome, and variable completeness in connection fields. | Free endpoint access includes some results and form, with limited credits and windows. Race-local IDs and provider aggregates are insufficient for original residual reconstruction. |
| FormFav | Docs retrieved. The hosted run had no configured FormFav credential. | The repository has a separate form/meetings, form, results, usage and connection-stats client. Standard RM scoring uses Krok. The probe adds a capability check for Premium prices when the entitlement is available. It did not authenticate FormFav or validate the user's plan. |
| Racing Queensland | Official Ipswich race page and Open Data index returned 200. Three dated sectional CSV bodies from Cannon Park, Sunshine Coast and Toowoomba returned 200. The linked Open Data catalogue attempt was denied. | Retain latest authorised authority declarations, going and results; validate final reserves and field versions. The index does not itself establish a bulk sectional API or licensed redistribution. |
| RQ sectionals | 26 race blocks, 342 runner rows, 1,713 positive segments and 509 missing placeholders. 79 runner rows had no positive measurements. | Reproducible parser validates date/race blocks and runner duplicates. It counts paired zero placeholders as missing. Preserve raw units, field identifiers and timing semantics until independently documented. Neither frozen engine consumes sectional inputs. |
| PuntersEdge | Downloaded September 2026 release 2026-09.3 from GitHub. Publisher and downloaded SHA-256 matched. 234,230 rows across codes, including 55,420 rows for 1,283 AU thoroughbred races. | Independent-source candidate and useful historical named-book price benchmark. The file contains open and close quotes, advertised-jump offsets, result labels and provider-scoped horse references. Keep separate from Betfair residual inputs and live execution proof. |
| Betfair original compatible history | 16 pinned AU months, 22,499 retained races. Prior archive recheck retained 348 strict historical event links and 94 strict prior-start leads. | Use full-field scheduled-off back price plus retained outcomes for original probabilities. Protect pinned May/July 2026 gaps, registered identity and cutoff. Do not substitute printed SP, BSP, bookmaker closing quotes or form summaries for original inputs. |

The PuntersEdge sample had 37 offsets after the advertised jump and two repeated saddlecloth rows in book vectors. Quarantined those vectors. Advertised jump offsets are not actual off-time evidence. Even after cleaning, TAB was complete relative to the provider's own union in 436 of 1,276 vectors, with only 20 of those having identical integer capture offsets. Four internally complete TAB books were underround. This sample does not prove that either collector captured a simultaneously executable field, and the sample identifiers are provider-scoped rather than demonstrated national registrations. Source attribution: PuntersEdge Australian racing closing-line sample (puntersedge.online), CC BY 4.0, derivative count audit.

[Probe workflow](https://github.com/Spankman/Monty-Racing/actions/runs/45561929597) · [Probe output](acquisition_evidence/provider_probe.json) · [Sectional evidence](acquisition_evidence/rq_sectionals.json) · [PuntersEdge audit](acquisition_evidence/puntersedge_sample.json) · [Public retrieval evidence](acquisition_evidence/public_pages.json) · [PuntersEdge release](https://github.com/Puntersedge-api/puntersedge-datasets/releases/tag/2026-09)

The Krok register covers all 27 documented racing routes, including 25 marked Free and two paid international routes. The wider Krok API publishes 137 Free routes out of 178, including unrelated sports and product endpoints. The audit did not call those unrelated routes or claim authenticated access for all published racing endpoints. Keep rankings, provider AI and market summaries outside the frozen model inputs.

## Source order and independence

| Category | Primary | Secondary and fallback |
| --- | --- | --- |
| Card, going, final scratchings and reserves | Queensland authority documents for the first live cohort | Krok for discovery and reconciliation; FormFav or Breednet for corroboration; approved Racing Australia or state authority feed when jurisdiction expands. |
| Registered horse and dated race participation | Authority registration/profile and dated declarations or steward records | FormFav Free or Krok runner/field form for leads; recheck exact race and official identity before bridging to exchange. |
| Outcomes and official settlement | Independently saved final authority result | Krok results, FormFav Pro or PuntersEdge result label for comparison only. Keep late changes and dead heats under manual review. |
| Frozen historical market inputs | Original pinned Betfair scheduled-off backs | Restore verified private archive or source revisions. Missing stays missing. |
| Sectionals and connection/context research | Racing Queensland downloadable sectionals and authority event data | Krok sectionals and connections; FormFav form and Pro analytics for comparison. Do not install a new feature into frozen scoring. |
| Current named fixed-WIN | Authorised direct single-book capture with complete latest active field and per-offer time | Krok named offer plus validated PuntersEdge or FormFav sample and direct evidence. Otherwise keep provisional or DATA BLOCKED. |

Racing Australia and Racing NSW FreeFields routes and Punters.com.au form were denied by robots in this probe. Racing.com returned a homepage and Breednet returned a dated meeting index. Racing SA returned 202 without usable data, WA’s robots fetch returned 403 and Tasracing redirected to a second host without a validated payload. Racing and Sports returned 403. These limits are probe-specific. Verify authorised channels before automating. Track official feed lineage separately from guide/publisher origin and bookmaker origin. PuntersEdge documents collecting from bookmakers. Krok and FormFav may also publish the same offers or share a collector. No matched live sample established which provider pairs have genuinely independent collection. Compare raw quote identifiers/time semantics, simultaneous price differences, aligned withdrawal events, characteristic shared lags and provider-confirmed lineage. Repeated price agreement alone cannot prove a common collector or independence.

## Cost and consumption

**Krok observed price per call, not an account invoice.** One credit per returned meetings page and five per field-form call. Published 50-credit monthly Free allowance, five requests per minute and a 300-second cache floor. The five-minute Monty gate still applies. Near-expiry quote data can fail even when the request fits the credit allowance.

| Scenario | Daily credits or average | Credits/month | Free fit |
| --- | ---: | ---: | --- |
| One complete one-page shared card per day | 1 | 30–31 | Leaves 19–20 in calendar months. Underlying freshness still untested on Free. |
| One daily card plus 15 fresh requests and four spare pages/retries in a 31-day month | 1.61 | 50 | Fits exactly under these assumptions. |
| Two captures each day, one page apiece | 2 | 60–62 | Exceeds Free. |
| One daily card and one five-credit enrichment call per day | 6 | 180–186 | Exceeds Free. |
| 44 field-form calls daily plus one card | 221 | 6,630–6,851 | Unnecessary for routine RM. |
| One five-credit dated Krok results retrieval per day in addition to the daily card | 6 | 180–186 | Prefer authority feeds for settlement. |

C reads the original capture and should spend zero provider credits. The four RM variants already can share an eligible snapshot. Multiply card counts by actual billable pages and measure successful and failed capture costs from headers. Do not infer Monty's month consumption from shared account remaining balance. A 44-race FormFav day would use about 45 requests for one meetings call plus one form call per race, or 46 with a usage check (1,350–1,426 monthly across 30–31 days). Free’s published cap is 1,000 daily and 10 per 10 seconds, so volume can fit a batched form job. Free live odds and latest final scratches are not entitled. Live price polling per race would have different costs and still requires verified provenance.

| Acquisition arrangement | Monthly external-data estimate |
| --- | --- |
| Free Krok + free permitted authority and historical archives + optional FormFav Free | **A$0** for bounded private research. Operational live readiness unproven. |
| Keep existing paid Krok API if Free fails | Public Krok marketing lists A$49 and its terms list A$79.99/month. Check actual AU checkout/invoice. Budget up to A$79.99 pending confirmation. |
| Optional FormFav Pro/Premium | Website lists $10/$50 monthly. If charged in AUD that is A$10/A$50. Checkout currency, tax and existing charges unverified. Do not subscribe based on this estimate. |
| PuntersEdge | Open sample A$0. API advertises a Free key and paid plans from A$9/month. Verify the required exact endpoints, coverage and licence before counting the API as a replacement. |

[Krok plans](https://krokodds.com.au/api-access) · [Krok terms](https://krokodds.com.au/terms) · [FormFav pricing](https://formfav.com/pricing) · [PuntersEdge API](https://puntersedge.online/api) · [Racing Queensland sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)

## Implementation

1. Meter credits and pages per capture. Start with a separate Free key or authorised existing Free credential; do not switch billing for the trial. Compare complete daily cards and exact selected offer ages at actual RM traffic. Stay under published burst and monthly limits. A successful paid probe alone cannot validate Free.
2. Coalesce RM views using the same valid capture and scope. Record its original acquisition and offer timestamps. Reuse only while eligible under existing freshness and jump rules. Refresh or block after field changes. Never carry prior-day live prices forward or use C to re-poll.
3. Cache historical inputs by source, stable event identity, observed-at, checksum and revision. Keep append-only private observations and a registration crosswalk. Refresh changed event files only; use permitted conditional HTTP requests when available. Ingest one authority meeting file for its races where possible. Keep results separately versioned with correction and dead-heat handling. Persist missingness. Do not download the same pinned archive every run.
4. Ask for an authorised same-race direct operator sample and a separately collected feed. Check final emergency/withdrawal status, full field, named WIN product, exact selected prices and observation timestamps. Reconcile with one bookmaker throughout. No FormFav or Krok plan change until the sample proves the required feature coverage and practical reliability.
5. Preserve V6/V7 definitions, existing five-minute and market gates, betting rules and draft stack. Review costs and prospective evidence before any approval. The draft adds count-only probing and offline archive validators. It does not change production workflows, scoring or quote extraction.

Raw source captures and credentials remain private. Published samples are counts and digests. Only use documented routes and agreed licence terms.
