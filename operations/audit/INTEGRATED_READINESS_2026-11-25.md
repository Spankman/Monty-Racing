# Integrated operational review — 25 November 2026

**Not ready for production deployment.** Draft PR #213, branch
`integration/verified-operations`, integrates #210 and #211. Production remains
`623d46b449e46cfc5fa63b633c3f19b404bba41a`; no merge, retraining, wagering,
expert-weight activation or V7 promotion occurred. Original reports are retained.
Machine-readable evidence: [episode and receipt register](INTEGRATION_VERIFICATION_EVIDENCE_2026-11-25.json).

## Confirmed causes and repairs

The original commands did generate predictions. Betting approval was an
unfinished integration: missing verification was labelled NO BET and standard
views removed rankings. No validated production approval evaluator exists yet.
The repaired views preserve genuine V6 PROVISIONAL and V7 RESEARCH ONLY rankings,
with DATA BLOCKED betting approval separately identified. Technical failures,
partial coverage and expiration remain explicit. No QUALIFIED selection or
verified negative-value decision has been manufactured.

Both frozen engines execute independently. The numerical audit reconstructs
their own market offset, imputation, scaling, correction and temperature without
fitting. A missing compatible historical feature join leaves substantial frozen
imputation; form strings and Betfair BSP are not interchangeable with original
V6 historical residuals. Effective expert weighting remains 100% Monty / 0%
experts. The historical conditional 90/10 blend is deferred, not activated.

Integrated changes include requested-engine status aggregation; retained expired
audit predictions with current display suppressed; consistent attribution of the
exact selected named-bookmaker quote; large-file GET-only blob fallback; receipt-
anchored compact delivery views; paired-ticket deduplication; stronger identity
conflict rejection; bounded public source capture; primary WIN parsing; authority
PDF/scratching parsing; and immutable prospective/official settlement contracts.

The first pilot exposed a missing `pdftotext` runtime dependency, now installed
only in staging. Partial V7 coverage initially failed an overly strict pilot
harness; it now accepts partial completion only when the requested engine
actually scored races. A green job is never substituted for that semantic check.
Inactive bookmaker quotes now require explicit withdrawal evidence before being
labelled scratched. Unparsed numbered authority entries fail field verification.

## Genuine live staging evidence

These were branch-push staging executions using existing Actions secrets and the
real Krok provider. They were **not ordinary production issue-event acceptance**.
Native ChatGPT tools created their staging issues and retrieved derived results.
No manually dispatched workflow was used. Results reside on
`monty-verification-staging-results`, outside production results.

| Request / workflow | Exact runtime commit | Actual outcome |
| --- | --- | --- |
| #214 / [45519528731](https://github.com/Spankman/Monty-Racing/actions/runs/45519528731) | `f31aa73943bfd3efc1d9cc783b528cb1a676601a` | Nine command variants executed; V6 28 races, V7 26 scored / 2 blocked; C fresh, GET only. Harness failed on partial coverage. Authority PDF reader absent. |
| #219 / [45546255339](https://github.com/Spankman/Monty-Racing/actions/runs/45546255339) | `7065db3c2e15cc65bffe4da85a7c3aa2d5c04a69` | All four daily commands, four R4 single-race commands and bare Ipswich 4 returned assessments; V6 27 scored, V7 20 scored / 7 blocked. Job succeeded; zero verified cohort. |
| #220 / [45547304908](https://github.com/Spankman/Monty-Racing/actions/runs/45547304908) | `4daee6f66c745674fe6061cc7dda05b05f6e5117` | R7: V6 and provisional/bare variants scored; V7 blocked on inconsistent price provenance. Job failed honestly. Zero verified cohort. |

#219 shared capture: **04:21:22.063137 UTC**, expires **04:26:22.063137**.
Native connector retrieved and hash-verified the receipt, delivery manifest and
both compact forecasts at approximately **04:26:17 UTC**, still fresh and
pre-jump. C itself used four GETs, no writes or inference; capture age 211.818s.
These forecasts are now expired and are not current selections.

#219 receipt SHA-256:
`10a550bc6afb0e2c86a4f0f551cf0cb1e72751b9bbe53c36db67a8c7a0d61837`.
Forecast SHA-256:
`01d9b22fe439391aa10b118ddd86cb43a4305028f9c538db2a8e1328bc6d9f78`.
[Receipt](https://github.com/Spankman/Monty-Racing/blob/monty-verification-staging-results/runs/2026-11-25/45546255339-integration-1/receipt.json).

#220 capture 04:31:47.221258 UTC, expires 04:36:47.221258.
Receipt SHA-256:
`258fb27c516bf2152f56f0036f40d05494d14bc02a7e8eb7b8aa7e342d7cf974`.
[Receipt](https://github.com/Spankman/Monty-Racing/blob/monty-verification-staging-results/runs/2026-11-25/45547304908-integration-1/receipt.json).
Both full forecast/receipt pairs were independently rehashed from saved bytes.

## Independent verification pilots

TAB was checked first: the live Actions page probes returned HTTP 500. Racing
Queensland HTML and the dated field PDF returned 200, as did Racing NSW's dated
Wyong acceptances. Sportsbet public primary WIN SSR state was accessible with
normal TLS from the workspace, but returned 403 from Actions. No restriction,
CAPTCHA or TLS verification was bypassed. Only normalized public facts and source
hashes were committed, not private provider payloads or raw pages. The workspace
quote packet is a one-off staging aid, **not an unattended production solution**.

Ipswich R4: date, 2150m, Soft 5, turf and 14:48 Brisbane jump agreed. Sportsbet's
explicit deduction record and visible page marked #7 Lord Protector scratched
at 13:45; authority snapshot still listed it active. The declared fields did not
fully agree. Betting verification stayed blocked rather than silently selecting
one scratching state.

Ipswich R7 was the second attempt, scheduled 16:33 Brisbane. Sportsbet declared
17 runners / 13 active. Authority parsing omitted #8 Music Fever and retained
#17 Superhero as an unresolved active emergency. Krok/operator field matching
also failed. V7's consistent-price-provenance guard blocked its inference.
The parser now rejects unparsed numbered entries; authoritative final emergency
and same-race field evidence are still required. Neither race was admitted to
the verified prospective cohort. No forecast settlement or superiority claim is
made. Full-day eligible coverage is not a national TAB completeness attestation.

## Predictive differences and coverage

In #219, 20 races scored by both engines had the same top horse but differing
probabilities. Archived R4 top probability: V6 0.3713254911776831 versus V7
0.3549781380487933; second 0.21638426323760812 versus 0.2128953114957076.
This is historical numerical evidence, not a live ticket. Both models start from
normalized inverse fixed-win odds; missing historical inputs explain substantial
market agreement. There is no shared tipster ranking substitution.

Provider inventory: Albany 7, Geelong 8, Ipswich 7, Launceston 8, Strathalbyn 7,
Wyong 7 and Te Aroha 11 races. #219 scored 27 AU races with V6 and 20 with V7;
class, timing and source guards explain exclusions. Independent national TAB
coverage remains unverified. NZ remains separately available where reliable;
these AU command tests do not establish a complete NZ acceptance.

## Measured latency and freshness

#219 daily commands took 27.40–27.72s each, single races 1.33–1.35s; provider
acquisition 5.815s; publication 3.980s; terminal issue delivery 1.296s; C 1.007s.
#220 provider acquisition 4.463s; publication 4.776s; terminal delivery 1.146s.
Issue #220 was created 04:30:53, worker started 04:31:37.344, acknowledged
04:31:38.533: 44.344s startup and 45.533s acknowledgement latency. These are
staging measurements, not an iPhone latency guarantee. Several sequential daily
tests consumed much of the shared five-minute window. The limit remains 300s;
expired/current and post-jump display safeguards remain intact. Refresh volatile
facts just before an individual production inference/publication; do not extend
the window to disguise startup or verification delay.

## Historical identity and integrity

Original 24,797-race recovery report is preserved. Re-download verified 16 of
18 pinned monthly source hashes, representing 22,499 races / 216,366 runners.
May and July 2026 public source bytes differ from the recorded hashes and row
counts. They are quarantined locally, not substituted into the recovery or model.
Required originals: May SHA
`4814fb3cb27a902ec9d3a684d822549ee4c6a9a4ed10adfe2e2134a293eb0df1`
and July SHA
`ab41b42e2ebb017ecae7330308daf3f2d37ce26f8b4087a214984046002bd5ca`.

The hash-verified subset still produced 3–13 candidate Betfair IDs for each of
the prior 11 Ipswich runners; **zero identities independently accepted**.
Candidate generation is not a crosswalk. Official registration ID or independently
corroborated participation plus nonconflicting identity attributes is needed.
Historical age/sex/trainer/country checks reject contradictions but cannot turn
an ambiguous name into an accepted identity. No trailing-year feature activation,
calibration fitting or historical leakage was introduced.

## Tests and prospective process

Local final code: 136 operational contract tests, 152 existing runner checks and
13 frozen V6 tests passed. Historical replay: 17,987 runners / 1,787 races,
maximum probability difference 1.6653345369377348e-16; all 55 original hashes
verified; `refitted=false`. Final CI must be checked on the final proposed head,
separately from the semantic failure of live pilot #220.

`operations/prospective.freeze` records genuine paired probabilities, fair odds,
market baseline, feature completeness, fixed odds, capture and source/model
hashes before jump. Admission requires fresh authority/operator evidence and
resolved emergencies. `settle` requires a dated same-race final authority result,
exact active identities and source hash; late changes invalidate comparison.
It writes a new immutable result with log loss, Brier and winner rank. Fixture
tests prove this contract; **no actual verified cohort or official settlement has
yet completed**. Report sample size; never infer superiority from one race.

## Prioritised register and owner decisions

- [x] Integrate #210/#211 and retain original reports, model hashes and full-day rules.
- [x] Separate predictions from approval; retain genuine rankings with limitations.
- [x] Test four daily commands, four single variants and V6 shorthand in staging.
- [x] Demonstrate GET-only C and fresh native connector compact retrieval.
- [x] Diagnose pilot failures; preserve essential checks and immutable records.
- [x] Implement prospective freeze/settlement contracts and fail-closed identity checks.
- [ ] Obtain a repeatably accessible authoritative field/emergency and named WIN source
  from Actions; workspace-only acquisition cannot satisfy unattended operation.
- [ ] Complete a fully verified pre-race pilot and independently settle it.
- [ ] Recover the two original pinned historical files; resolve official horse IDs and
  compatible as-of historical features before claiming full feature completeness.
- [ ] Specify/validate the missing production approval evaluator against existing rules;
  positive arithmetic edge alone is insufficient. No threshold changes are proposed.
- [ ] After owner merge approval, test ordinary issue-event queue, repeated/stale requests,
  unattended schedule, iPhone retrieval, combined ticket/blackbook/results-review flows.
- [ ] Confirm approved logo/legend assets where absent; do not invent acceptance.

Owner decisions: no deployment is recommended yet. No paid data or infrastructure
is required/authorised by this branch. Any necessary licensed source access needs
separate approval. Keep expert weighting and V7 promotion deferred.

## Handover and rollback

Commands remain RM6, RM7, RM6PS/RMV6PS, RM7PS/RMV7PS and their meeting/race
variants; bare meeting/race defaults to V6. C reads the existing request and must
never submit another. Read `requests/<issue>.json` on the configured results ref,
then its exact receipt and delivery manifest/forecast paths. Verify receipt and
forecast hashes, request identity, capture expiry and jump before presenting.
Use two separately labelled grouped tickets when both models are requested;
preserve the existing fixed-win progression, standalone roughies and no-wager
labels. PNG only when requested. Do not present these expired staging forecasts.

No deployment has occurred, so rollback now is simply leaving #213 unmerged.
If approved later, revert the integration merge through a reviewed PR to the
recorded production baseline; retain all immutable result refs and audit records,
avoid resetting branches or rewriting forecasts, and use existing queue controls
if processing needs to pause. Never edit model manifests or completed requests.

IN MONTY WE TRUST.
