# Owner recovery-key custody procedure

Version 1 · 26 November 2026. Design only. No key rotation, account/secret modification or permission grant performed. Never put private keys/passphrases in Git, artifacts, logs, issues, reports or ChatGPT messages.

## Initial custody

The staged certificate has an existing matching private key in the authorised private workspace. Only its public certificate/fingerprint is in source. Current workspace custody is not durable backup and the key must not be assumed present in future sessions. An earlier Actions-secret creation was denied403; do not retry it.

Before activating retention, the owner should preserve the existing key through an authenticated private transfer into an existing encrypted password manager/secure file store. Keep a second encrypted offline backup under owner control, separately from ciphertext archives and the primary device. Use the platform's supported private file transfer, not a chat attachment or public recovery ZIP. Minimise owner work to this one custody action and one witnessed restore test; an authorised operator can prepare the rest. Record only certificate fingerprint, key ID, custodian, backup-test date and expiry in Git.

New keys, if later approved, are generated in a private offline/isolated environment using a modern OpenSSL-supported CMS encryption certificate, restrictive umask and mode0600. Prefer an encrypted private-key file with passphrase entry outside captured logs. Public certificate installation may be reviewed in a separate PR; never replace it silently. Do not generate a replacement now and strand existing packets.

## Access and recovery

Owner is the default custodian. Grant an authorised researcher temporary access only through the approved private environment/secure store. GitHub Actions needs only the public certificate to encrypt; it does not need the private key. Ordinary ChatGPT receives permitted derived slips from a private delivery sink, not this decryption key.

For recovery, verify certificate fingerprint/key match without printing key material, anchor GitHub artifact digest and receipt hash, decrypt to a new mode0700 directory outside the repository, check every file/model/preprocessing hash and probability replay, then expose only approved fields through the verified research interface. Check retention deadline first. Never downgrade integrity failures, use an unverified archive or regenerate missing evidence.

Test restore from the secondary backup periodically and after any custody/rotation change using a synthetic packet encrypted to the intended certificate. Record packet/receipt hashes, successful verification, authorised operator and test date only. A successful workspace-key decrypt is not proof an independent backup can restore.

## Rotation and revocation

Rotation requires owner approval and reviewed public-certificate change. First prove the new key's independent backup recovery. Future packets use the new certificate fingerprint; preserve old keys only as long as existing unexpired evidence lawfully needs them. Do not rewrite prior forecasts/receipts or claim re-encryption preserves the original cipher hash.

Revoking a key's access does not revoke already-downloaded copies or decryptability of publicly available ciphertext. If compromised, stop new encryption to that key, restrict/delete retrievable affected ciphertext where authorised, expire consumer access, assess provider/owner notification and record the incident. Do not call a replacement certificate retroactive revocation. Do not change provider API secrets as part of encryption-key rotation without separate approval.

## Expiry and plaintext deletion

Maintain a private packet inventory keyed by receipt/cipher/model/certificate hashes and policy deadlines. Delete expired hosted/local cipher copies where authorised, retaining permitted hash-only receipts. Remove recovered plaintext and temporary ZIPs after research or by the earliest source deadline; close open handles and clear temporary directories. Filesystem deletion is not a claim of forensic erasure on SSDs/backups. Owner secure-store/backup retention and access logging must respect the same source rights. Do not delete the only owner key while valid needed packets remain.

## Acceptance checklist

- [ ] Owner confirms approved source/cloud-processing/retention scope.
- [ ] Existing matching key saved in two owner-controlled encrypted locations.
- [ ] Independent backup restore decrypts a synthetic packet; hashes/replay verified.
- [ ] Authorised consumers/processors and removal deadline documented.
- [ ] Incident, rotation and expiry procedures assigned to a custodian.
- [ ] Owner approves activation separately from this documentation.

Outstanding: durable owner custody and independently tested backup remain unverified. No secrets or permission changes are requested through chat.
