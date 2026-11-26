# Engineering integration readiness — 26 November 2026

Development branch `integration/evidence-readiness-20261126`, stacked on #243 `112703369ad8386df50801627b02b2c656092cf2`. No merge, deployment, additional provider API acquisition, trial changes, purchase or wagering. V6 official/frozen; V7 research-only.

## Reviewed versions

Before implementation: AGENTS, Plan, Library, Betting Policy, Selection Rules, README, operations procedures and baseline handover from #234 `14c1d1b7b443b607e0a35e2abff87db40d7f8a74`; #241 `cd775dc07a0a716ecb47a6e4db934c5fb451a72a`; #242 `ad47142f9b824d74d05d30cdc467a416ad987229`; #243 `112703369ad8386df50801627b02b2c656092cf2`; issue #240; trial README/protocol at #235 `84689048a374f2af824da77057623d20809f6baa`; production `623d46b449e46cfc5fa63b633c3f19b404bba41a`. These include the owner-approved extended research/resource/pruning boundaries and current $4 progression override.

The previously missing master is now [MONTY_MASTER_HANDOVER.md](../../MONTY_MASTER_HANDOVER.md), permanent version1, with mandatory startup/significant-completion updates in AGENTS/README. It references authoritative rules and preserves the prior baseline as historical evidence. Full Australian PLS methodology is still missing; dependent exact replication is pending. Existing Benter/conditional-logit/calibration methods and prior negative/null findings were reviewed. No new predictive experiment or training is justified here.

## Integration decisions

| Draft | Review and disposition |
| --- | --- |
| #234 | Import latest AGENTS/Plan/Library/baseline, then add master/startup requirement. Preserve substantive audit/research/engineering records instead of overwriting them with #241's older copied Plan. |
| #241 | Retain full runner rankings, roughie diagnostic states and integrity gates; no price floors/quotas changed. Historical #236–239 recovery gap remains121V6/118V7 records. |
| #242 | Reference its independent research and data contract; keep candidate code/weights isolated. No established incremental edge over calibrated market. Do not import a learner into operational routing. |
| #243 | Retain 55-input/frozen preprocessing diagnostics and encrypted binding; add original PE acquisition wiring, encrypted progress checkpoints, interruption reconciliation/recovery and explicit private-delivery result handling. |

No trial code/workflow/automation copied or changed. When eventually combining #235, retain both its test_pe_trial and existing evidence/ruffie CI entries; do not overwrite the parallel workflow list. This branch's own offline checks do not activate trial schedules.

## Interrupted execution and evidence completeness

Successful racing HTTP responses checkpoint immediately when retention is permitted; canonical capture and each completed race checkpoint again. Each checkpoint contains available original private files and a hash manifest encrypted with the owner's public certificate. It never claims a complete forecast or reconstructs absent probabilities. Count and cumulative encrypted bytes are bounded; checkpoint errors are explicit in the normal evidence index and do not retry provider calls. Final full packet still requires canonical snapshot, original live HTTP bytes and all scored-model feature audits.

An always-step reconciler uses only runs carrying this implementation's evidence-intent marker. It verifies available checkpoint hashes, writes an append-only interruption receipt and removes ephemeral private plaintext. It preserves completed model receipt/forecast files. Interrupted outcomes distinguish recoverable partial evidence from no verified checkpoint. Replay/recovery validates independently anchored recovery receipt, cipher, manifest, expiry and each file; salvage cannot be promoted to an official or completed model forecast. No C acquisition/restart is added.

Limits: checkpoint creation and final upload are not atomic with external GitHub storage. If the runner is destroyed or hard cancellation prevents always-steps/upload, local checkpoints may be lost. This is not a remotely replicated crash journal or WORM. GitHub/admin deletion and copied ciphertext/private-key leakage remain possible. Final run failure handling must report the original request honestly; no automatic duplicate execution. A separately approved durable storage policy would be needed for stronger crash guarantees, not silently introduced here.

## PuntersEdge staged wrapper

`operations.puntersedge_capture.Acquisition` performs one existing bounded venue-board request, matches exact race ID and venue, captures original successful response bytes before parsing, then calls the existing single-book canonical adapter. It never substitutes another race/book, joins invented historical features, adds form/acceptance API calls or changes model inputs. Accepted field matches are same-race only, not lifetime crosswalks. Unverified independent completeness stays explicit. Original provider offer observations, including age_basis, remain distinct from local receive times.

`execute` routes that acquisition through the existing shared frozen pipeline and same model snapshots. C is rejected before acquisition. An acquisition object is single-use and restores the previous observer. No production worker import, primary/fallback switch or trial integration. Existing retry/rate-limit client boundaries remain intact; synthetic tests use injected responses with zero real credits.

## Operational compatibility

Standard/provisional/single-race commands preserve scopes, engine routing and betting classifications. Official view retains diagnostic predictions separately; provisional and V7 research views show their genuine ranks. Missing private rights/access is `PRIVATE_DELIVERY_BLOCKED`, with preserved model execution status, receipt/capture/expiry and no automatic manual assessment. It is not NO BET, no-race-found or failed inference. Issue delivery includes the explicit notice and correct provider source rather than hardcoded Krok attribution.

Repeated projections/read-only C never acquire or rescore. Existing shared reuse, combined-ticket/deduplication, freshness, rendering, blackbook and results logic are retained. Offline acceptance exercises genuine frozen inference through synthetic PE HTTP and all command variants on the same one-race fixture, repeats projections and withholds expired selections. That is not national coverage or ordinary-iPhone/live acceptance. Existing regression suites cover C/queue/reuse and ticket progression; final CI proves only its stated scope.

## Security, permissions and custody

See [provider/private delivery assessment](PROVIDER_PERMISSIONS_AND_DELIVERY.md) and [key custody procedure](RECOVERY_KEY_CUSTODY.md). Public terms now explicitly support Krok permitted retention and PE personal research. Account-specific/cloud-processing/public ciphertext/display scope still needs the documented clarification. No live policy is enabled. No private key/credential exposed, created in account secrets, rotated or shared.

An approved owner-private derived-result repository is the smallest proposed readable ChatGPT sink using existing GitHub tools. It needs owner approval, least-privilege cross-repository write authentication and demonstrated connector/iPhone private reads. No repository/permission/secret created here. Metadata-only delivery is explicit but does not meet full slip-delivery acceptance. Encryption alone does not solve access or licence questions.

## Validation and deployment decision

Final draft PR records exact tested head, CI URLs and independently verified hosted packet receipts. Local/CI contracts use synthetic fixtures. Original historical replay and all55V6hashes remain mandatory; V7 pin unchanged. No live provider or mobile-access acceptance is claimed. Source terms pages were fetched publicly without API credentials; zero provider API credits.

**Not ready for production activation.** Achievable engineering is staged; owner licensing/key/private-sink/access decisions and separately approved live validation remain open. Do not deploy merely because CI is green.

Proposed sequence, each activation step requiring approval:

1. Review stacked draft and exact CI/replay evidence; resolve master/shared-doc baseline with Work via issue240/PR references.
2. Confirm source-specific retention/AI-processing/display rights and attribution. Save the existing owner key in two secure locations and prove backup recovery.
3. Approve/configure private derived delivery and least-privilege access without public raw data. Demonstrate fresh ordinary iPhone ChatGPT reads with exact receipt hashes.
4. Approve a bounded live staged capture; verify all fields, quote clocks, runner matrices, seal/recovery, delivery/expiry and both frozen hashes. Do not consume the trial's budget.
5. Only after owner acceptance, merge/activate approved commits in order, leaving research candidates unpromoted. Verify real issue ingress, queue/schedule and semantic model outcomes.

Rollback while staged: leave this draft unmerged; production is unchanged. If later activated, stop only the approved new source/delivery path, disable its evidence policy, revert its reviewed integration commits and retain prior immutable receipts. Re-enable previously approved provider only if credentials/rights/freshness/budget are still valid; otherwise DATA BLOCKED. No rollback may mutate frozen models, backfill missing originals or delete the owner's only necessary key. Preserve and independently manage the six-day trial.
