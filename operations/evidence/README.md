# Private inference evidence — staged, not activated

Engineering interface v1, 26 November 2026. This branch preserves frozen scoring and betting gates. It does not authorise data retention, public redistribution, production deployment, or extra API calls.

## Licensing and custody first

`policy.example.json` permits only explicitly synthetic fixtures. Krok and PuntersEdge remain disabled. Set `MONTY_EVIDENCE_POLICY` to a **private local policy file** only after documenting the source-specific retention permission, reference and review expiry. Configure 1–7 days and at most 100 MB per packet. A separate public-derived-display permission and reference is required before publishing detailed licensed predictions to public GitHub. A private retention permission does not establish public display rights. Without them, delivery returns a metadata envelope and an explicit licensing limitation, not a model NO BET.

The included certificate is public. Its matching owner recovery key is never committed or uploaded. Existing workspace key custody is not a durable disaster-recovery solution: arrange an owner-controlled backup before activation. No new Actions secret is needed to encrypt; the private key is needed only by the authorised research reader. Do not repeat the rejected secret-creation attempt.

## Capture and binding

`Recorder.raw` records exact successful racing HTTP response bytes and their observation metadata. Acquisition observers do not initiate calls or retry a request when capture fails. Canonical caller inputs are separately retained before normalization. Account/usage responses, headers, credentials and unrestricted URLs are excluded. PuntersEdge clients may pass their observer to `Recorder.raw` and pass the captured page tuples to `execute(evidence_raw_pages=...)`; the existing production provider wrapper must be wired explicitly before claiming original PE HTTP capture. Canonical-only live evidence is SEALED_INCOMPLETE, never complete.

Private packet contents:

* Original available pages, canonical provider snapshot and complete shared runner inputs.
* Declared, scratched, unscored and scored runner inventories, all model rankings and eligibility/reporting reasons.
* The actual 55-column scoring inputs, supplied columns, observed/missing masks, frozen imputation, transformed terms, weights and linear logit contributions.
* Market/model probabilities, model/expert weights, prices and attribution available in original inputs, observation/expiry and integrity gates.
* Market-normalisation versus conditional model value decomposition, calibration and within-race cancellation diagnostics.
* Frozen model JSON bytes, original V6 manifest, file hashes, source commit and checkout cleanliness.

Unavailable values remain unavailable. Runner declarations retained only in original HTTP pages are explicitly distinguished from the normalized canonical roster. Individual feature contributions are exact linear logit terms, not causal explanations or additive probability effects.

The packet is a bounded ZIP encrypted using OpenSSL CMS AES-256-GCM to the owner public certificate. No plaintext ZIP is retained. Exclusive file creation prevents overwrite within a run. The public forecast and receipt bind cipher, manifest and private prediction SHA-256 digests, run ID, model pins and expiry. This is tamper-evident append-only application storage, **not independently enforced WORM storage**. GitHub administrators can delete artifacts. Stable GitHub artifact IDs/digests must be retained alongside receipts by the consumer.

## Retention and recovery

Hosted uploads include only `evidence-sealed/`, retained for seven days. The application policy may be shorter; the reader refuses expired packets. Completed execution deletes its ephemeral private directory even if sealing fails. CI has an always-cleanup step. Abrupt cancellation before finalization is not claimed crash-proof; isolated ephemeral Actions runners and bounded artifact uploads are required. Consumers must delete their recovered plaintext at the policy deadline; this code cannot force deletion from independent machines. `expired_bundles(root, apply=False)` previews local cipher expiry and `apply=True` removes only verified expired cipher files, preserving indices. It never deletes immutable forecasts or receipts.

Authenticate and download the exact linked private artifact using authorised GitHub tools. Verify its GitHub artifact digest, then run from a private workspace:

```sh
python -m operations.evidence.verify --cipher /private/run/evidence.cms \
  --key /private/owner-recovery-key.pem --receipt /private/run/receipt.json \
  --forecast /private/run/forecast.json --receipt-sha256 RECEIPT_SHA256 \
  --output /private/new-recovery-directory
```

Anchor the receipt hash independently; do not trust an archive's own hash assertion. Recovery verifies public forecast binding, authenticated cipher, manifest, every file, frozen schema/preprocessing/weights and numerical probability reconstruction. NPZ readers prohibit pickle. Recovery requires a new directory outside this repository. Expired, changed or unbound packets are rejected. After verification, `operations.research_interface.load_verified_evidence` provides a read-only research schema; see [research contract](../RESEARCH_INTERFACE.md).

## Acceptance scope

The new CI runs genuine frozen V6 and V7 on explicitly synthetic seven-runner fields (six active), seals/deletes plaintext and publishes encrypted evidence plus clearly labelled synthetic receipts. No Krok/PuntersEdge keys, live calls, training, trial changes or betting approval are involved. Private replay with the owner key is a separate acceptance step. A green contract job alone is not proof of complete inference evidence or live provider retention.

## Readiness integration supplement — 26 November 2026

`operations.puntersedge_capture` now connects exact successful response observation to the canonical/shared inference pipeline under the source policy; it is not imported into the production worker or trial. `Recorder.checkpoint` encrypts available private files after each successful HTTP response, canonical capture and completed race, with count/cumulative bounds and explicit capture errors. Normal complete packets and interrupted salvage remain different schemas.

`python -m operations.evidence.interrupted operations_output` is an always-step reconciler for this implementation’s intent-marked directories. It preserves completed receipts, records verified partial checkpoint hashes without manufacturing selections, and cleans remaining plaintext. `recover_checkpoint(...)` checks the anchored interruption receipt, cipher, manifest, expiry and file hashes into a new private directory. It never returns a completed forecast. Runner destruction before upload can still lose local checkpoints; no WORM or external crash journal is claimed.

Review the [permanent master](../../MONTY_MASTER_HANDOVER.md), [current terms/private delivery assessment](../governance/PROVIDER_PERMISSIONS_AND_DELIVERY.md) and [owner custody procedure](../governance/RECOVERY_KEY_CUSTODY.md). Earlier blanket Krok-retention uncertainty is superseded by the documented permitted retention clause; specific cloud/AI/display scope and owner policy remain separately reviewed. No live policy enabled.
