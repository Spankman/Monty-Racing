# Finite PuntersEdge acceptance trial — staging only

Owner authorisation: 26 November 2026. Stack: draft #231 → draft #235.
No production deployment, provider switch, paid plan, merge, model development,
threshold change, retraining, wagering or promotion of V7 is authorised here.

## Execution and preregistration

`protocol.json` is fixed before the first preregistration. Target: three races
per day, 26 November–1 December inclusive (18 slots; at least 12 genuinely
complete races required). Future slots are **not** registered races: the priced
provider board has a rolling horizon. Actual identities are frozen daily in
`plans/YYYY-MM-DD.json` before T−60. Select by geography, race class and clocks,
never predictions/prices/outcomes. Saturday prefers Queensland metropolitan and
another metropolitan venue; other slots prefer country. Do not call provincial
meetings metropolitan or count unknown classifications. Doomben's 28 November
meeting is independently advertised by BRC:
https://www.brc.com.au/event/recognition-stakes-day/ .

One bounded ChatGPT automation runs 08:30, 11:30 and 19:30 Brisbane for six days,
then a final read-only catch-up 2 December 08:30. Its returned configuration
confirms creation/enabled state; future delivery/authenticated environment
availability are **not yet demonstrated**. The account has five active-task
slots, so phases share one task; unrelated tasks were preserved.

- 08:30: obtain actual current allowance, board, selected meeting acceptances and
  three race forms. Verify the artifact/receipt, then register the exact plan.
- 11:30: issue one staging marker push. Hosted Actions executes all twelve
  scheduled paired windows at T−60/15/5/2. Launch margin covers the fixed
  13:00–17:00 jump window within a 350-minute standard Ubuntu job. Startup delay,
  >30s-late windows and rescheduled races are recorded, never backfilled.
- 19:30: obtain bounded provider results, primary-source documents, inspect actual
  receipts and report. Provider results alone never become independent settlement.
- 2 December: aggregate the six days; report unmet criteria rather than accepting
  the provider automatically. Final settlement can remain pending.

The workflow is **push-triggered on the trial branch only**, not a production
cron. Default-branch scheduling cannot execute an unmerged workflow. ChatGPT's
scheduled coordinator uses the existing authenticated `gh` CLI for staging
marker commits; the read-only native connector retrieves artifacts. This is not
proof that a read-only connector can dispatch workflows by itself.

From repository root, using existing GitHub authentication:

```sh
python -m operations.trial.control --date 2026-11-26 --mode plan
python -m operations.trial.control --register /private/path/plan.json
python -m operations.trial.control --date 2026-11-26 --mode capture
python -m operations.trial.control --date 2026-11-26 --mode results
```

**Do not run capture early:** use the automated 11:30 phase. Each phase has an
immutable launch ID atomically committed with its marker. `ALREADY_LAUNCHED`
means do not duplicate/retry it. Rerun attempts are disabled. A technical retry
requires review of evidence; it must not hide the original failure or overwrite
a preregistration. `C` is not a supported acquisition mode and cannot fetch data.

## What each capture proves

Exact PE race ID, date, AU country, horse code, venue, race number and unchanged
jump are required. Requests for PE and Krok overlap; upstream observation
instants may differ and are measured, never claimed identical. Runner matching
uses same-race saddlecloth **and** name and bookmaker; not a lifetime name-only
horse crosswalk. PE `age_basis=poll`/`last_update` and Krok per-offer `captured_at`
are kept distinct from price-change clocks. All books get existing full-field
market-integrity arithmetic; no normalized baseline is labelled model value.
Missing runners, pagination, stale/mixed/inconsistent prices stay visible.

A fresh acceptance baseline is acquired once per selected meeting during
capture (not reused from the hours-old planning call), then compared by exact
race ID/number/venue and number+name+SCR at every point. Its age and unresolved
emergencies remain visible; cached declarations never attest to current
independent field verification.

The complete single TAB fixed-win vector feeds the unchanged V6 and V7 engines
once per point on one byte-identical canonical snapshot. Existing inference,
feature completeness/imputation, market baseline, probabilities, fair odds,
rankings and all rules are preserved in encrypted outputs. Real inference can
still be DATA BLOCKED for betting. Missing TAB prices can prevent this strict
paired comparison; other books are measured diagnostically, never substituted
silently. Existing runner command/full-day behaviour is unchanged.

Each window immediately uploads its own immutable artifact. Check both internal
frozen-at times and GitHub artifact creation time before jump. An artifact not
uploaded before jump is not fully externally timestamp-verified prospective
acceptance. Reports expose aggregate freshness/counts/overround/latency/cost/hash
information, not raw licensed runner/odds feeds. Six days have not happened yet.

## Independent verification and history

The existing RQ HTML+PDF parser is reused for validated Queensland venue codes;
full field, withdrawals and final emergencies must reconcile to the exact race.
No new authority verification is invented for unsupported states. TAB is tried
first through the public race URL supplied by the provider. Only permitted
public pages are fetched, no challenge/login/TLS/access-control bypass. Existing
Sportsbet parser is used if public state is accessible; 401/403/challenges stop
that host for the day, transient failures get only the bounded T−2 retry.
A successfully fetched page is not automatically a verified price vector.

Original historical identity/residual reconstruction and independent operator
reconciliation remain blockers. `operations.prospective.freeze` records both
models plus market baseline before jump, but its **unchanged** admission checks
exclude unverified diagnostics. This trial does not attest to missing history.
No diagnostic record is promoted retrospectively. `operations.prospective.settle`
requires independent final authority result, exact active field, no unresolved
late field changes and an admitted forecast. Only eligible settlements yield
log-loss, Brier, winner rank and top-pick hit metrics for V6/V7/MARKET. No ROI or
estimated exotic dividends; no superiority claim from one race.

Recovered form is candidate evidence only. Exclude same-day/future/invalid run
rows. Provider `form_as_at` may denote scheduled race cutoff, not observation;
a future `form_as_at` is flagged, never used as acquisition time or availability
proof. No new form summaries enter frozen features; lifetime horse crosswalks
are still unverified. See the existing 55-feature mapping under
`operations/audit/puntersedge_evidence/FEATURE_55_MAPPING.csv`.

## Budgets and costs

PE hard reservations per day: plan24 + captures32 + results6 = **62 credits/day,
372 maximum over six days**, including bounded retries. Preserve500 operational
credits and fail closed on unknown remaining allowance. Expected no-retry usage
for three distinct meetings: board4 + acceptances6 + form9 + twelve targeted
boards24 + capture-time acceptance baselines6 + results2 = **51/day or306/six days**. This is a trial estimate, not a
measured monthly full-national-service cost. Header costs and account-wide usage
deltas are recorded separately; concurrent production use prevents blindly
attributing all account delta to this trial. `/usage` has documented zero cost
but missing cost headers remain honestly unknown in meter totals. Use server
Retry-After within original bounded client limits; no unrestricted retries.

Krok: maximum14 requests/day, one bounded call per scheduled pair; remaining
credits must stay above1000. If the first probe lacks remaining allowance, stop
further Krok calls and disclose missing comparison. Pagination gaps are not
called complete. No historical bulk job or billing endpoint is invoked.
Subscription expiry is **unverified**; a quota reset is not expiry evidence.
Never reuse expired prices to save credits. Standard Ubuntu Actions on this
public repository has no paid-runner charge; no new infrastructure/subscription.

## Private evidence and recovery

Raw board/form/authority pages, model inputs, forecasts and prospective records
are AES-256-GCM CMS encrypted before authenticated artifact upload. Only the
public recipient certificate is in Git. Private key (mode0600) is preserved at
`/workspace/private/monty-pe-trial-20261126/recovery-key.pem`; it is not a provider
credential, is never printed and was not inserted into existing recovery ZIPs.
**This integration cannot write Actions secrets (HTTP403)**. Do not repeat that
operation. Current workspace key custody is not a durable independent backup.
Owner should securely preserve the private key or provide a permitted private
secret-storage route before discarding this workspace. Future raw recovery is
blocked if that key is lost; aggregate receipt retrieval does not need it.

Download an artifact using the supported GitHub connector; verify its GitHub
SHA-256, receipt checksum and ciphertext hash. Recover to a **new private path
outside the repository**:

```sh
python -m operations.trial.recover /private/artifact.zip --sha256 ACTUAL_GITHUB_DIGEST --key /private/recovery-key.pem --output /private/new-directory
```

90-day artifact retention is not permanent archival storage. Preserve encrypted
artifacts and receipts privately before expiry. No key value belongs in reports,
chat, Git, logs, public artifacts or issue comments.

## Staged migration and rollback

1. Finish six-day collection; verify all strata, exact pre-jump receipts,
   source independence, budgets, hashes and independently settled cohort.
2. Resolve every essential field/history/operator gap; quantify observed provider
   failures and quote-age distributions. Stop on excessive cost or missing data.
3. Submit owner-reviewed results with proposed source configuration and costs.
   A paid PE plan is only a recommendation until separately approved/purchased.
4. Only after owner approval: a separate production source-selection change with
   pinned model hashes and identical approval gates. No automatic fallback/model
   substitution. V7 stays research-only.
5. Rollback proposal: revert that future source-config commit to the previously
   approved Krok configuration, subject to still-valid credentials/licence,
   freshness and budget; if Krok expired/unreliable, DATA BLOCKED rather than
   fabricate selections. Preserve all PE receipts, do not overwrite forecasts.

Present staging rollback: disable **only this trial automation**, stop pending
trial jobs if needed, leave draft235 unmerged. Production is already untouched.
No claim that PE can replace Krok before its unknown expiry is justified yet.
