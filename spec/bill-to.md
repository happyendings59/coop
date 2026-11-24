# Bill To: Pay For Someone Else, On Chain

> © 2026 Kenneth William Mayle. This document is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/. The contract sketch in `contracts/bill-to/` is licensed under the GNU AGPL v3 with the attribution term in `NOTICE`.

Status: DRAFT v0.1, 2026-11-23 (Chicago). Idea by Kenny (HAPPY). Spec written by Claude.
Not audited. Not deployed. Not legal advice. Nothing here has been put on any chain.
Moved into this repository on 2026-11-23 from the project's working folder; content unchanged except the license header, paths, section 12 and the repo answer in section 11.

Document structure follows Kenny's standing rule for technical docs:
IEEE 1012 (system and software verification and validation) for the V&V plan and
integrity levels, and ISO 37301 (compliance management systems) for the compliance
obligations, risks and controls. Section numbers below are this document's own, not
clause numbers from either standard.

---

## 1. Purpose and scope

### 1.1 The problem
Uber can split a fare. Almost nothing else lets you say "send this bill to someone
else." On sites like Holiday Studios or Foxglove an order sits in limbo until it is
paid, and only the person at the keyboard can pay it. Kenny's ask (2026-11-23):

> "you should be able to like 'bill to' someone else"
> "they should be a standard design in our websites that you can put in an order and (crypto like) send the bill to someone else"
> "it may need to be on chain to like the bill is the NFT but the transaction doesn't approve untill the payer pays for the other"
> "it's an option this belongs in my coop project ... and doof.top and rebu and all of them"

### 1.2 What this spec defines
A shared, open "Bill To" standard for every Kenny site:

1. A buyer builds an order on a merchant site.
2. The buyer names a payer: an Ethereum address, an ENS name, or a SimpleX or
   Telegram handle that receives a claim link.
3. The bill is minted as an NFT (the Bill NFT) and delivered to the payer.
4. The order stays PENDING. Nothing ships, nothing is booked.
5. The payer (or several payers, split style) pays in USDC or ETH.
6. When fully funded, settlement is atomic: the merchant is paid, the Bill NFT
   flips to PAID and becomes the receipt, and the site releases the order.
7. If nobody pays before expiry, the bill dies, any partial money goes back, and
   the order is released or cancelled.

### 1.3 Who uses it (the shared standard)
| Consumer | Typical use |
|---|---|
| 5PM Cooperative (co-op project) | member orders, a co-op pays for a member, pooled buys |
| doof.top | equipment rental deposit billed to a friend or a camp |
| rebu.life | ride or item share, split the cost among riders |
| happyendings59/nonprofitwebsites templates | donor pays a family's bill, sponsor a booking |
| any Kenny site with a checkout | one drop in widget plus one shared contract per chain |

One contract per chain, many merchants. A site integrates with a small JS widget and
a webhook; it never holds keys or funds.

### 1.4 Out of scope (v0.1)
Card payments, fiat on ramps, tax calculation, shipping, disputes beyond a simple
merchant refund, private (shielded) payments. Section 9 notes where these plug in.

---

## 2. Terms

| Term | Meaning |
|---|---|
| Buyer | person who builds the order and requests the bill |
| Payer | person (or people) who pays it |
| Merchant | the site or co-op receiving the money (an address it controls) |
| Bill | on chain record: merchant, token, amount, expiry, order hash, status |
| Bill NFT | ERC-721 token for the bill, held by the payer, later the receipt |
| Claim link | URL carrying a one time secret so a handle (SimpleX, Telegram, email) can claim a bill to a wallet |
| Order hash | keccak256 of the merchant's order JSON; the chain never sees the order itself |

---

## 3. Existing standards we build on (do not reinvent)

| Standard | What we take from it |
|---|---|
| ERC-721 | the Bill NFT. Ownership = who is asked to pay; transfer = "pass the bill on" |
| ERC-5192 (minimal soulbound) | optional: lock the NFT once PAID so receipts cannot be traded |
| ERC-1155 | considered for split shares; rejected for v0.1 (one bill, one NFT is easier to reason about). Splits are tracked as contributions instead |
| EIP-681 (payment request URIs) | the QR and link format: `ethereum:<contract>@<chainId>/payBill?...`. Wallets that do not understand the call still show the chain and contract |
| EIP-712 (typed data signing) | merchant signs the bill terms off chain; buyer sees readable terms in the wallet |
| EIP-4361 (Sign In with Ethereum) | login by signing a challenge, no passwords (section 6) |
| ERC-2612 permit and Uniswap Permit2 | pay in one transaction without a separate approve step |
| ERC-3009 (transferWithAuthorization) | USDC supports it; lets a relayer submit the payment, payer pays no ETH gas |
| ERC-4337 (account abstraction, paymasters) | optional sponsored gas so a non crypto payer can pay with only USDC |
| Escrow patterns (OpenZeppelin Escrow / pull payments, ReentrancyGuard, SafeERC20) | refunds are pull based; no loops that send money to many people |
| Request Network | existing on chain invoicing protocol. Worth a look before we build; it covers invoices but not the "order held until a third party pays, NFT is the bill" flow. Decision for Kenny in section 11 |

---

## 4. Requirements

IL = integrity level (section 8.1). "Shall" items are tested.

### 4.1 Functional
| ID | Requirement | IL |
|---|---|---|
| F1 | A merchant shall create a bill from merchant signed EIP-712 terms: merchant, token, amount, expiry, order hash, split allowed, min contribution | 3 |
| F2 | The bill shall be minted as an ERC-721 to the payer address, or held by the contract against a claim key hash if the payer is a handle | 3 |
| F3 | A claim link holder shall claim the Bill NFT to any address by signing that address with the claim key (front run safe) | 3 |
| F4 | Anyone may pay; the Bill NFT holder is who is asked, not the only one allowed | 2 |
| F5 | If split is allowed, partial contributions shall be accepted and recorded per contributor | 4 |
| F6 | The payment that reaches the full amount shall settle in the same transaction: merchant paid, status PAID, event emitted | 4 |
| F7 | Overpayment shall be refused (exact or less than remaining) | 4 |
| F8 | After expiry, an unpaid bill shall become EXPIRED and contributors shall withdraw their own money (pull) | 4 |
| F9 | Buyer or merchant shall be able to cancel an unpaid bill; contributions become withdrawable | 4 |
| F10 | Merchant shall be able to refund a PAID bill in full; money goes back pro rata to contributors (pull) | 4 |
| F11 | Supported tokens shall be an allowlist per deployment. The list is short on purpose: BOLD (default), USDC, Tether (USDT) and native ETH. The merchant picks one of these for each bill in the signed terms (decided by Kenny 2026-11-23) | 3 |
| F12 | Sites learn status from events (`BillPaid`, `BillCancelled`, `BillExpired`, `BillRefunded`) via a watcher, never from the browser alone | 3 |

### 4.2 Non functional
| ID | Requirement |
|---|---|
| N1 | Contract shall be non upgradeable, no owner who can move funds. Admin limited to adding tokens to the allowlist (behind a timelock or multisig) |
| N2 | No protocol fee in v0.1 (co-op spirit). If a fee is added later it is a separate, visible field |
| N3 | Target chains: Base and Arbitrum One (low fees, native USDC by Circle). Ethereum mainnet optional |
| N4 | Gas per payment target under 120k on L2 |
| N5 | Order contents never go on chain, only the order hash |
| N6 | Works for a payer with no ETH (permit / ERC-3009 plus optional paymaster) |

---

## 5. Design

### 5.1 Lifecycle
```
            createBill
                |
                v
   OPEN (NFT with payer or claimable) --claim--> OPEN (NFT with claimer)
     |    |        |
     |    |        +--pay (partial)--> OPEN (funded < amount)
     |    |        +--pay (completes)--> PAID  --refund--> REFUNDED
     |    +--cancel (buyer or merchant)--> CANCELLED
     +--expiry passes--> EXPIRED (computed, no tx needed)
  CANCELLED / EXPIRED / REFUNDED: contributors call withdraw()
```

### 5.2 Why money goes straight to the merchant on PAID
Kenny's line is "the transaction doesn't approve until the payer pays." The escrow is
the waiting period before full funding. Once full, the merchant is paid at once, so the
merchant is never stuck waiting on a second release step. Refunds then need the
merchant to send funds back in (`refund` pulls from the merchant). A hold window
variant (merchant paid after N days) is an option in section 11.

### 5.3 Claim links for SimpleX, Telegram, email
1. Site generates a throwaway keypair (claim key) in the buyer's browser.
2. Contract stores only `claimSigner` (the claim key's address).
3. Buyer sends the link `https://<site>/bill/<chainId>/<billId>#k=<claimPrivateKey>`
   through SimpleX, Telegram or email. The `#` fragment is never sent to a server.
4. The payer opens it, connects a wallet, and the page signs
   `(billId, payerAddress)` with the claim key. `claim()` checks that signature and
   transfers the NFT. A watcher copying the transaction cannot redirect it, because
   the signature names the payer's address.
5. Handles are never stored on chain. No registry of Telegram names to wallets.

### 5.4 Split pay (Uber style)
`splitAllowed` and `minContribution` are set at creation. Each `pay(billId, amount)`
adds to `contributed[billId][payer]`. The last payment that reaches the amount settles.
The Bill NFT stays with whoever holds it; contributors get a `BillContribution` event
(their receipt). A site can show "3 of 4 friends paid".

### 5.5 Tokens: BOLD, USDC, USDT, ETH
Decisions (Kenny, 2026-11-23): "i'd prefer bold, but they could pick" and "it should be
eth usdc tether or Bold just a few options." BOLD is the default; the merchant may pick
USDC, Tether (USDT) or ETH instead when it creates the bill. No other tokens.

| | BOLD | USDC | USDT | ETH |
|---|---|---|---|---|
| Price stable | USD pegged, not guaranteed (cooperative.md N6) | yes | yes | no, the bill amount moves in dollar terms |
| Issuer can freeze | no freeze, pause or blacklist function (cooperative.md N1) | yes (Circle blacklist, required by the GENIUS Act). A frozen merchant or contract stops settlement | yes (Tether can freeze addresses). Same effect as USDC | no |
| Gasless pay | to be checked (permit support not confirmed here) | ERC-3009 / permit | to be checked (permit support not confirmed here) | needs ETH anyway |
| Token quirks | none known | none known | on Ethereum, USDT's transfer does not return a value; the contract's SafeERC20 handles this, and tests MUST cover it | native, no approve step |
| Recommendation | default | allowed | allowed | allowed, priced at creation, short expiry |

Freeze risk is real: if Circle or Tether blacklists the contract address, all open
USDC or USDT bills on it are stuck. Mitigation: one contract per token per chain, short expiries, and
document it to users (section 7).

### 5.6 Chains
Base and Arbitrum One first: fees of cents, native USDC. Same contract bytecode on each.
Bill IDs are per chain; links always carry the chain id (EIP-681 `@chainId`).

### 5.7 Site integration (the shared widget)
- `billto.js` widget: "Bill to someone else" button at checkout. Calls the site's
  backend for merchant signed terms, asks the buyer for a payer (address, ENS, or
  "send a link"), submits `createBill`.
- Order stays PENDING in the site database with `chainId + billId`.
- `billto-watcher` (small service, one per site or one shared for the co-op) listens
  for events and calls the site's webhook: `paid`, `cancelled`, `expired`, `refunded`.
  Waits for a confirmation depth (L2: finalized or 2 minutes) before releasing goods.
- Static sites (Hostinger) can use a hosted watcher plus a Supabase table; a decision
  for Kenny.

---

## 6. Login: sign a challenge, no passwords
EIP-4361 (Sign In with Ethereum): the site sends a message with domain, nonce,
issued at and expiry; the wallet signs; the server checks the signature and the
domain, and burns the nonce. The same wallet that pays is the account. This matches
the wallet login already on twooffive.io and the /wallet-simplex-login/ proposal on
kwm59.io (challenge delivered over SimpleX). No email, no phone number required.

---

## 7. Compliance management (ISO 37301 structure)

Not legal advice. These are questions to put to a lawyer before anything goes live.

### 7.1 Context and scope of the compliance system
Scope: the shared contract, the widget, the watcher, and each site that offers
Bill To. Interested parties: buyers, payers, merchants (including the co-op and
nonprofits), Kenny as publisher, stablecoin issuers, regulators.

### 7.2 Compliance obligations register
| ID | Obligation (area) | Why it may apply | Initial position | Owner |
|---|---|---|---|---|
| C1 | Money transmission, federal (FinCEN MSB rules; FinCEN 2019 guidance on convertible virtual currency business models) | a party that accepts and transmits value for others may be a money transmitter. The 2019 guidance discusses non custodial software differently from custodial services | contract is non custodial, no admin can move funds, no Kenny controlled address in the money path. Get counsel to confirm | Kenny + counsel |
| C2 | State money transmitter licensing (and NY BitLicense) | states define transmission differently | same as C1; geofence if counsel says so | counsel |
| C3 | Sanctions (OFAC) | US persons may not deal with sanctioned addresses | screen payer and merchant addresses in the widget and watcher against the OFAC SDN list; contract stays neutral | site operator |
| C4 | Stablecoin rules (GENIUS Act, issuer terms) | issuer can freeze; terms of use | disclose freeze risk (5.5) | Kenny |
| C5 | Consumer protection, refunds, unfair practices (FTC Act, state UDAP) | users must understand that blockchain payments are final | plain language terms at checkout; refund policy shown before the bill is sent | site operator |
| C6 | Sales tax | merchant sells goods or services | handled by the merchant off chain | merchant |
| C7 | Tax reporting (1099-DA for brokers; disposal of crypto is a taxable event for the payer) | paying in ETH is a disposal | disclose; no broker activity by us | Kenny + counsel |
| C8 | Nonprofit rules (for nonprofitwebsites) | a payer covering a family's bill may think it is a donation | do not label a Bill To payment as tax deductible unless the nonprofit is the merchant and issues a receipt | nonprofit |
| C9 | Securities | NFT must not look like an investment | Bill NFT carries no yield, no resale promise; soulbound after PAID (ERC-5192) | Kenny |
| C10 | Privacy (state privacy laws, GDPR for EU visitors) | addresses and payments are public forever | order data off chain; only hashes on chain; privacy notice (7.5) | site operator |
| C11 | Co-op governance | co-op paying a member's bill is a member decision | co-op bylaws decide; spec does not | 5PM Cooperative |

### 7.3 Compliance risks
| Risk | Likelihood | Impact | Control |
|---|---|---|---|
| Contract bug loses funds | medium before audit | high | IL 4 tests, external audit, cap per bill at launch (e.g. 500 USDC) |
| Regulator treats the system as transmitter | low to medium | high | C1, C2 counsel review before mainnet |
| Sanctioned address pays | low | high | C3 screening |
| Payer phished by a fake "bill" | medium | medium | bills only from allowlisted merchant signers shown by name; widget shows merchant domain |
| USDC freeze strands bills | low | medium | 5.5 mitigations |
| Spam bills to random addresses | medium | low | only merchant signed bills mint; wallets can hide spam NFTs |

### 7.4 Controls and records
- Merchant registry: which merchant signer belongs to which site (off chain JSON,
  published and signed).
- Change log for every deployment, with source verified on the block explorer.
- Incident log and a pause plan: the contract has no pause over funds; the widget and
  watcher can stop new bills.

### 7.5 Privacy
Everything on chain is public: who paid whom, how much, when. A Bill To payment
links the payer's wallet to the merchant forever. Controls: order hash only;
encourage a fresh wallet for paying; claim links travel in the URL fragment; no
handle registry. Shielded payment options (for example privacy pools) are out of
scope for v0.1.

### 7.6 Monitoring and improvement
Quarterly review of the register, after any law change (GENIUS Act rules, FinCEN
guidance), and before adding a new chain, token, or site.

---

## 8. Verification and validation plan (IEEE 1012 structure)

### 8.1 Integrity levels
Integrity level is set by the worst consequence of a failure.

| IL | Meaning here | Components |
|---|---|---|
| 4 | money lost or frozen, cannot be undone | `pay`, settlement, `withdraw`, `refund`, `cancel`, expiry logic |
| 3 | wrong party gets the bill, or a site releases an unpaid order | `createBill` signature check, `claim`, token allowlist, watcher confirmations |
| 2 | wrong status shown, recoverable | widget UI, webhook retries |
| 1 | cosmetic | NFT artwork, metadata text |

### 8.2 V&V tasks by level
| Task | IL 4 | IL 3 | IL 2 | IL 1 |
|---|---|---|---|---|
| Requirements traceability (each F/N to a test) | yes | yes | yes | |
| Unit tests (Foundry) | 100% branch | 100% line | yes | |
| Invariant / fuzz tests | yes | yes | | |
| Static analysis (Slither) | yes | yes | | |
| Formal check of key invariants | recommended | | | |
| Independent review (external audit) | required before mainnet | required | | |
| Testnet run (Base Sepolia, Arbitrum Sepolia) | yes | yes | yes | yes |
| User acceptance with real sites | yes | yes | yes | yes |

### 8.3 Invariants (must always hold)
1. For every token, contract balance == sum of `funded` over OPEN bills + sum of
   withdrawable balances.
2. A bill is paid to the merchant at most once.
3. `funded <= amount` always.
4. A contributor can never withdraw more than they put in (or their pro rata refund).
5. Once PAID, REFUNDED, CANCELLED or EXPIRED, no new `pay` succeeds.
6. Only a valid merchant signature can create a bill for that merchant.

### 8.4 Test scenarios (validation)
- Friend pays: buyer bills a friend by link over SimpleX; friend claims and pays in USDC on Base; site ships.
- Split: four riders on rebu.life each pay 25%; the fourth payment settles.
- Expiry: two of four pay, the bill expires, both withdraw.
- Cancel: buyer cancels after one partial; contributor withdraws.
- Refund: doof.top deposit refunded after gear returns; contributors withdraw.
- Front run: an attacker copies a `claim` transaction; it reverts because the signature names the real payer.
- Freeze simulation: a mock token that blacklists the merchant; settlement reverts; bill expires; contributors withdraw.
- Reentrancy: malicious ERC-20 and ETH receiver.
- Watcher: reorg on testnet, webhook down, duplicate events.

### 8.5 Anomaly reporting
Every failed test or finding gets an entry with IL, status, and fix commit.

---

## 9. Future options
- Hold window (merchant paid after N days, refunds without merchant cooperation).
- Bill passing: payer transfers the NFT to someone else ("not me, ask my dad").
- Recurring bills (co-op dues) via ERC-4337 session keys.
- Card fallback: the same bill page offers a card button through a normal processor.
- Co-op treasury pays: a Safe multisig or DAO vote is just another payer.

## 10. Contract sketches
See [`contracts/bill-to/BillTo.sol`](../contracts/bill-to/BillTo.sol) (about 250 lines).
It compiles clean with solc 0.8.24 and OpenZeppelin 5.0.2 (checked 2026-11-23). It has no tests yet and is not audited. Open TODOs in the file: permit / ERC-3009 pay, tokenURI.

## 11. Decisions for Kenny
1. Build our own or use Request Network as the base layer? (Recommend: our own small contract, it is about 250 lines and fits the NFT bill idea; read Request Network first.)
2. Pay merchant at once on full funding (this draft) or a hold window?
3. ~~Which repo?~~ Answered 2026-11-23: it lives in this co-op repository (happyendings59/coop) as shared code.
4. Which chain first: Base or Arbitrum?
5. Hosted shared watcher (one for all sites) or one per site?
6. Who is the lawyer who reviews section 7 before mainnet?

## 12. Fit with core.md (open, needs a decision)

This spec was written before it moved here, so three points do not yet match the
[core spec](core.md) and the [cooperative spec](cooperative.md). They are listed, not
resolved; nothing above was changed to force a fit.

| Point | This spec | core.md / cooperative.md | Question |
|---|---|---|---|
| Settlement token | DECIDED 2026-11-23: BOLD default; merchant may pick USDC, USDT or ETH; no other tokens (5.5, F11) | BOLD, no freeze function; USDC is not the default (cooperative.md N1, N2) | Resolved. Note: BOLD's native network is Ethereum mainnet (cooperative.md N4), so the chain question below now matters more |
| Release rule | merchant paid the moment the bill is fully funded (5.2) | release by party signatures or a 2-of-3 arbiter (core.md E2) | Is Bill To a pre-payment step that feeds a co-op escrow, or its own settlement path? (Ties to decision 2, hold window.) |
| Chains | Base and Arbitrum One first (N3) | Ethereum mainnet for escrow, L2 for small records (cooperative.md N4) | Which network for co-op bills? |

The rest fits: no admin key moves funds (core.md P2, E6), order data off chain (core.md D1, D2),
fresh addresses encouraged (core.md PV1), and the login in section 6 is specified in
[signature-login.md](signature-login.md).
