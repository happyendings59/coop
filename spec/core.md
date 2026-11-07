# 5PM Core Specification

> © 2026 Kenneth William Mayle. This document is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/. You may share and adapt it, including commercially, as long as you give credit.

**Status:** Draft 0.1, November 2026. Design intent, not a finished or audited system. Nothing here is legal, tax or financial advice; items marked *attorney review* must be confirmed by qualified counsel before implementation.

This document defines the foundation shared by every 5PM system: the [cooperative marketplace](cooperative.md) and the [document delivery platform](document-delivery.md). Each system spec builds on the rules here and does not restate them.

The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119.

---

## 1. Principles

| ID | Principle |
| --- | --- |
| P1 | **Non-custodial.** The operator MUST NOT hold or control other people's money. Funds move only by the signatures of the parties they belong to, or by narrow, published rules (see §6). |
| P2 | **No admin keys over user funds.** No operator key MAY upgrade, drain or redirect contracts that hold user funds. |
| P3 | **Verifiable without the operator.** Every record that matters (payments, deliveries, completions, reviews) MUST remain independently verifiable if the operator disappears. |
| P4 | **Data minimization.** Collect only what a transaction needs. Data never collected cannot be demanded, leaked or misused. |
| P5 | **Chain-agnostic.** No system is permanently tied to one blockchain. Networks are chosen by published criteria (§9) and can change by member vote. |
| P6 | **Law by module, not by fork.** Jurisdictional rules live in versioned rule modules (§7), not in separate codebases. |
| P7 | **Honest labels.** Every attestation shows who actually signed it. Nothing is labeled "verified" unless it was checked. |
| P8 | **Off by default.** Any function that depends on a qualified person, a license or a legal opinion stays switched off until that requirement is met. |

---

## 2. Data placement

The blockchain holds money, promises and proof. Everything else lives in ordinary, access-controlled storage.

| On-chain | Off-chain |
| --- | --- |
| Value transfers and escrow | Bids, quotes, chat threads |
| State transitions (purchased, checked in, completed, refunded, burned) with reason codes | Calendars and drafts |
| Verified reviews | Names, addresses, phone numbers |
| Status flags and liens (§5) | Credential documents |
| Fingerprints (hashes) of signed documents, price lists and sealed bids | The documents themselves, encrypted (§8) |

Rules:

- **D1.** Personal data MUST NOT be written on-chain, in plaintext or in reversible form.
- **D2.** Document contents MUST NOT be written on-chain. Only a hash and retrieval coordinates may be.
- **D3.** Every off-chain record that an on-chain event depends on MUST be fingerprinted on-chain, so later tampering is detectable.

---

## 3. Privacy

- **PV1. Fresh addresses.** Each payment, escrow or delivery SHOULD use one-time addresses on both sides, so no single address reveals a participant's history or revenue. Stealth addresses (ERC-5564 or equivalent) MAY replace this.
- **PV2. No linking.** The operator MUST NOT build or run tooling that links a participant's addresses together, and MUST NOT read balances or wallet history. The system sees only the transaction in front of it: the item, its listed price, whether its escrow was funded with at least that price, its status events and its one-time addresses.
- **PV3. Owner first.** Requests about a wallet or its contents go to its owner. The operator answers only valid legal process (subpoena, warrant, court order), only for data it actually holds, and notifies the affected person unless an order forbids it. Requests are logged and counted in a yearly transparency report.
- **PV4. Biometrics.** The system MUST NOT use face, fingerprint or other biometric identifiers. (Illinois BIPA carries heavy statutory penalties.)
- **PV5. Privacy tools.** Participants MAY use privacy wallets and shielded pools with their own funds. The operator MUST NOT operate mixing or obfuscation services (see the parked item in §11).

---

## 4. Signers and attestations

An **attestation** is a signed statement of one fact: a license is active, a death occurred, a lien exists, an identity was checked. Contracts react to attestations from **approved signers**.

### 4.1 Signer registry

- **S1.** The registry lists each approved signer, the facts it may attest, its credential (bar license, notary commission, agency identity) and its validity period.
- **S2.** Adding or removing a signer is a governance action (§10), publicly logged.
- **S3.** A government or agency plugs in as a signer with no code changes, by registering its signing key for the facts it is authorized to attest.

### 4.2 Interim attestors

Until a government issues a fact digitally, an **interim attestor** (attorney, notary, compliance officer) may attest what they personally verified against official records.

- **S4.** Interim attestations MUST be signed in the attestor's own name and labeled as such. They MUST NEVER be labeled as issued by a government.
- **S5.** An interim attestor MUST NOT substitute where law requires the actual authority (for example, a license or permit to unlock a restricted category).
- **S6.** When an official signer onboards for a fact, interim attestation for that fact ends. Past interim attestations stay on record, labeled as theirs.

### 4.3 Independent attestor network

Attestation SHOULD be performed by a network independent of the operating cooperative, so the co-op never verifies its own claims.

- Separate governance and funding; no member of the co-op votes on attestations about itself.
- Every attestor holds a verified credential, shown on each attestation.
- Attestors post a bond or carry professional insurance.
- Conflict rules: no attesting for clients, relatives or business partners.
- Random assignment and rotation.
- Sitting judges act only through court orders, not as attestors.

---

## 5. Status flags and liens

Items, vouchers and records MAY carry status flags.

| Flag | Set by | Cleared by |
| --- | --- | --- |
| Reported stolen | Owner, police | Police, or owner on recovery |
| Lien | Lender, government registry | The same lender or registry |
| Disputed ownership | Any claimant, reviewed by the dispute panel | Dispute panel or court order |
| Recall or safety notice | Manufacturer, agency | The same source |
| Court order or freeze | Verified court or agency | That court or agency |

- **F1.** Every flag records who set it, when and why, and has an appeal path.
- **F2.** A flag MAY block a sale or transfer. A flag MUST NEVER move ownership by itself; that requires the owner's signature, a resolved dispute or a court order.
- **F3.** Lien status MUST be worded as *reported*: "No reported liens — Illinois UCC search, 2026-11-06," never "no liens." Records reflect official registries; they do not replace them. Where they disagree, the official record governs.
- **F4.** The lien module is built ahead of government adoption so any approved authority can post and release liens through §4.1.
- **F5.** Owners MAY attach a recovery reward to an item. Tips go to police; the reward pays only on police-confirmed recovery.

---

## 6. Funds and safety powers

These rules apply wherever a system holds value in a contract.

- **E1.** Each transaction's value sits in its own escrow. There is no pooled customer fund.
- **E2.** Release requires the parties' signatures (see the system spec for which parties), or a neutral arbiter's signature when they disagree (2-of-3).
- **E3.** The arbiter MUST be independent of the operator (§4.3).
- **E4. Narrow safety power.** A governance multisig MAY freeze one specific escrow during a dispute, for a limited time, publicly logged. The only release it MAY make is a **refund to the original payer**. It MUST NOT redirect funds to itself or any third party.
- **E5. Court orders.** A court order keeps an escrow frozen until the parties sign the release the court requires, or refunds the payer. The operator never sends funds to an authority's address on its own.
- **E6.** Contracts holding user funds MUST NOT be upgradeable by any operator key. An emergency pause, if present, MAY only freeze, never move funds.
- **E7.** No contract holding real value goes live without an independent security audit.

*Attorney review:* whether this design is non-custodial under FinCEN guidance and Illinois money-transmission law.

---

## 7. Jurisdiction modules

### 7.1 Two kinds of law

Every transaction is checked against both:

- **Personal law**, which follows the person: citizenship and residence (for example, US taxation of citizens, sanctions rules for US persons).
- **Territorial law**, which follows the location: where the customer is (consumer protection), where work is done (licensing), where property sits (property law).

The engine applies every rule set that applies. Conflicts are flagged for human review, never silently resolved.

### 7.2 Module contents

Each module is versioned, written and approved by an attorney licensed there, and enabled for a region only by governance vote. A module defines, as applicable:

- price caps (for example, regulated towing rates; emergency price-gouging limits)
- gift certificate and voucher rules (expiration, fees, refunds)
- required disclosures and contract formats (for example, written estimates)
- labeling and units
- tax collection duties, including marketplace-facilitator thresholds
- which categories are allowed
- estate rules (governing law by citizenship, residence and property location; forced heirship warnings)
- whether contracts may be assigned or traded between providers

### 7.3 Category layers

1. **Platform exclusions.** Categories the operator's home country bars it from facilitating are never available, in any region. For a US operator these include controlled substances, sex work, weapons trafficking and sanctioned parties. Adult content is out of scope.
2. **Regional flags.** Everything else is enabled or disabled per region by module.
3. **Sensitive toggles.** Default off. Unlocking requires all of: an attorney's written opinion that the *operator* may facilitate it, a governance supermajority, the relevant authority's credential, and usually a legally separate entity.

### 7.4 Required everywhere

- **J1. Sanctions screening** at checkout from day one: block sanctioned persons, countries and addresses.
- **J2. Valid-in checks** at purchase (warn before paying) and at redemption (rules where the handoff happens). If blocked, offer a valid alternative or a refund.

---

## 8. Encrypted documents and release rules

Shared by the document delivery platform and the personal records vault.

- **R1.** Documents are encrypted to their named recipients' keys before storage. The operator holds no decryption key.
- **R2.** Encrypted payloads MAY be stored redundantly across decentralized storage. Only the manifest hash and retrieval coordinates go on-chain.
- **R3. Release conditions** are defined per document or per section, for example: 2-of-3 among executor, attorney and court-order key; or proof of death plus executor. Keys MAY be split by secret sharing.
- **R4. Trigger without access.** A signer whose attestation satisfies a release condition (for example, a death attestation) holds no decryption key. Satisfying the condition releases each section only to its own recipients.
- **R5. Challenge window.** Release triggered by an attestation waits a challenge window (for example, 30 days) during which the attestation can be disputed, including by the person themselves.
- **R6. Recovery.** Every recovery or release attempt notifies the owner and waits; a living owner can cancel it. A court order alone is the fallback when key holders are unavailable. Owners MAY name replacement key holders at any time.
- **R7. Legal form.** A record proves a document existed unaltered. Whether the document is legally valid depends on meeting its own legal requirements (witnesses, notarization, filing). In Illinois, a will must still be filed with the circuit court clerk after death.

---

## 9. Chain selection and migration

### 9.1 Criteria

Networks are weighed on:

1. an unfreezable settlement asset (see the system spec)
2. privacy
3. decentralization, including who can upgrade or censor
4. fees
5. developer tooling
6. legal clarity

No current network satisfies all of these. The specs are written so the answer can change.

### 9.2 Migration

- **M1.** Contracts are written to be portable across compatible networks; moving is a redeployment, not a rewrite.
- **M2.** A move is a governance vote.
- **M3.** Open escrows finish on the network where they started.
- **M4.** Records carry over with an attestation linking each new record to its original.

---

## 10. Governance layers

Each layer can overrule the one below it, and each is harder to change.

1. **Law.** No vote overrides state or federal law.
2. **Charter (bylaws).** Fee caps, payout formulas, member rights, signer rules, the safety powers in §6. Changed only by a supermajority (for example, two-thirds) of each member class after a public notice period.
3. **Votes.** Budgets, fees within caps, enabling modules and regions, signer registry changes.

Passed votes take effect after a time-lock, so members can challenge a vote that breaks the charter.

**Oversight:** a read-only view for auditors and regulators; the charter commits the operator to lawful court and agency orders, carried out by its own signers. No outside party holds a master key.

---

## 11. Parked items

| Item | Condition to reconsider |
| --- | --- |
| Built-in mixing or obfuscation | Only if the law changes (for example, the Tornado Cash appeals), with specialist counsel's sign-off, a supermajority, and a legally separate project. |
| Government-issued identity credentials with selective disclosure | When a government issues them; until then, a verified document check. |
| Transferable tax credits | Only where a jurisdiction's law creates a sellable credit, on that program's terms. |

## 12. Units

SI everywhere by default: stored, displayed and in every record. Viewers may switch their own display. Regulated outputs (such as US package labels requiring both metric and US customary units) are generated automatically by the jurisdiction module.
