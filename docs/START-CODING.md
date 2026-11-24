# Prompt to start coding the 5PM Cooperative (paste into a coding AI with this repo attached)

Read README.md, CONTRIBUTING.md and spec/core.md in happyendings59/coop first and follow them, especially the firm rules: test networks only, no secrets, no custody, no admin keys over user funds, no personal data on-chain.

Start the first component: an off-chain **attestation library** for spec/core.md section 4 (signers and attestations) and section 13.2 (fact ledger and stipulations). Folder `attest/`, branch `attest-v0`, pull request to main (do not push to main directly; sign off commits with `git commit -s`).

Scope for v0:
1. A JSON schema for an attestation: who signed (public key and signer-registry entry), the fact stated, the subject, time with time zone, an optional expiry, and a revocation pointer.
2. Sign and verify with standard keys (Ed25519 and secp256k1/Ethereum-style signatures), so a wallet can sign.
3. A signer registry file format (core.md 4.1) and checks against it.
4. A stipulation record (13.2): two or more parties sign the same fact; a disputed fact keeps each side's version.
5. A hash-only anchor format so a record can be timestamped on a test network later without putting any personal data on-chain.

Language: TypeScript or Python (pick one and say why), tests for every path including bad signatures, expired and revoked attestations, and unknown signers. Docs go in the folder's README. Describe features as "designed to support", never "legally valid".
