# 5PM Cooperative Marketplace Specification

> © 2026 Kenneth William Mayle. This document is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/. You may share and adapt it, including commercially, as long as you give credit.

**Status:** Draft 0.1, November 2026. Builds on [core.md](core.md); read that first. Design intent only: not audited, not legal advice. Items marked *attorney review* need qualified counsel before implementation.

---

## 1. Purpose

A member-owned network where independent businesses (farms, shops, trades, restaurants, resale stores, makers) share the back office, sell together and back each other up, while keeping their own names, customers and prices.

**Pitch:** let's merge, without becoming a monopoly.

### 1.1 Goals

- Providers keep the full price of their work.
- The cooperative runs at cost, like an electric cooperative.
- One member, one vote, regardless of size.
- No lock-in: members sell anywhere else and leave freely.
- Small businesses gain the ordering, scheduling, overflow, buying power and safety net that only large companies usually have.

### 1.2 Non-goals

- The cooperative does not set members' prices (antitrust; see §9).
- No investment token, tokenized equity, or profit-sharing token (securities law).
- No custody of customer funds (core §6).
- No pooled insurance-like fund (see §11).

---

## 2. Actors

| Actor | Role |
| --- | --- |
| Customer | Buys products or services. Needs no membership. |
| Provider | A member business or independent member selling through the marketplace. |
| Worker member | Works shifts at member businesses through the shift board. Paid wages in dollars. |
| Estimator | Member who quotes jobs so the laborer can focus on the work. |
| Arbiter | Neutral third signer for disputes, independent of the co-op (core §4.3). |
| Attestor | Verifies credentials and other facts (core §4). |
| Cooperative | The legal entity: runs the platform at cost, publishes its books, holds only its own operating money. |

---

## 3. Settlement asset and networks

- **N1. Settlement in BOLD** (Liquity V2): a USD-pegged stablecoin with immutable contracts and no freeze, pause or blacklist function. All prices, escrows, refunds and payouts are denominated in BOLD.
- **N2. Freezable stablecoins** (USDC, USDT, USDS) are not the default settlement asset.
- **N3. BOLD only inside the system.** Anyone holding BTC, XMR or anything else converts to BOLD themselves, in their own wallet or exchange, before paying, and converts back out the same way. **The cooperative prices and verifies; it never swaps** (swapping on someone's behalf risks money-transmitter treatment and fiduciary duties).
- **N4. Networks.** Ethereum-compatible and chain-agnostic (core §9). Start with Ethereum mainnet for escrow and settlement, especially large jobs. A lower-cost network (for example Polygon, Base or Arbitrum) MAY carry small, frequent records such as check-ins and reviews. BOLD on non-native networks is a bridged copy carrying bridge risk; large escrows settle where BOLD is native.
- **N5. Replaceable asset.** The settlement asset is a charter setting, not hard-coded. If BOLD fails or weakens, a vote can switch the default; open escrows finish in BOLD.
- **N6. Risk disclosure.** Terms state that BOLD's value against the dollar is not guaranteed; whoever holds BOLD carries depeg and inflation risk. Refunds return the BOLD amount paid.
- **N7. Regional assets.** Members abroad MAY price in a local-currency stablecoin meeting the same unfreezable standard, with the customer's currency shown.

---

## 4. The transaction engine

Every sale runs through the same nine steps. **Products** differ in source and delivery. **Services** add scheduling and check-in. Time-based work (a massage) is a service; a job with parts is a service that includes products. Each business type is a **template** that switches steps and options on or off.

| Step | Products | Services |
| --- | --- | --- |
| 1. Offer | Listing, quote, or buyer bid on a listed item | Listing, quote request, or sealed bids |
| 2. Purchase | Voucher minted; BOLD into escrow | Same |
| 3. Schedule | Delivery date or pickup window | Appointment record for a time slot, with its own chat thread; booking deposit |
| 4. Handoff | Shipped, picked up, or delivered by the source | Check-in scan at drop-off or arrival; voucher becomes *in progress* |
| 5. Fulfill | Product delivered | Work done or time spent |
| 6. Confirm | Buyer signs on receipt | Customer and provider sign; voucher becomes a *completed-job record* (receipt, warranty, review right) |
| 7. Claim window | Inspection or return period | Set period (for example 7 days) to report a problem; provider gets a chance to cure |
| 8. Settle | Escrow releases to the source | Escrow releases to the provider; estimator and referral shares split by formula |
| 9. Review | Verified review tied to the purchase | Verified review tied to the job |

### 4.1 Vouchers

- **V1.** A voucher is a prepaid claim on a product or service, sold for use and never as an investment. Marketing MUST NOT promise appreciation or resale profit ("lock your spot," never "lock today's price").
- **V2.** Vouchers are treated as gift certificates unless counsel says otherwise. In Illinois: no expiration earlier than 5 years after issue and no post-purchase fees. *Attorney review:* whether service NFTs are gift certificates, and whether multi-member credit is exempt.
- **V3. Appointment vs. voucher.** The voucher does not expire; an appointment can. A missed appointment leaves the voucher valid for rebooking.
- **V4. Voucher types:** fixed product or service; custom quote (doubles as the written estimate); dollar-value store credit usable at any opted-in member; *forever* service voucher (redeemable for a precisely defined job at any future price; refund value is still the amount paid).
- **V5. Valid-in rules** are carried on every voucher and checked at purchase and redemption (core §7.4).
- **V6.** Unredeemed vouchers are a liability; their funds are never spent on operations.

### 4.2 Fulfillment profiles (products)

Each product voucher carries its handoff terms: carrier shipping, or a pickup location and window (for example, a person selling a used fixture). Only the general area is shown before purchase; the exact location unlocks for the buyer once paid. Return and inspection terms ride in the same profile.

### 4.3 Templates

| Template | Examples | Notable options |
| --- | --- | --- |
| Product, retail | Resale and thrift, makers | Fulfillment profile, AI-drafted listings, donation routing for unsold items |
| Product, by weight or grade | Farms | Declared quantity (minimum vs. net), certified scale, lab certificate per lot |
| Service, standard | Brakes, haircuts | Fixed vouchers, booking deposit, check-in |
| Service, quoted | Roofing, tree care, concrete | Estimator, sealed bids, staged escrow release, written contract |
| Service, emergency | Plumbing, towing | Dispatch board, rush rate shown upfront |
| Time-based | Massage, lessons | Appointment is the product |
| Large equipment | Excavators | Bid, inspection period, lien search, theft check |

---

## 5. Side paths

| Path | Rule |
| --- | --- |
| Transfer setting | Customer chooses at purchase: **allow**, **ask me first**, or **don't allow** reassignment to another qualified member. |
| Locked terms | A transfer never changes price (or its cap), pickup and drop-off location, time window or warranty. Anything else needs new consent. |
| Check-in | Rotating QR code from the customer's wallet, scanned by the provider. Provider override with a reason; the customer confirms later; frequent overrides are reviewed; mediation only on disagreement. |
| Customer no-show | No scan in the window forfeits the booking deposit to the provider for held labor. Free cancel or reschedule until a set time (for example 24 hours) before. |
| Provider no-show | Customer gets the deposit back plus a credit. |
| Refund | Recorded against the voucher ID wherever requested. Voucher burned first, then funds returned, ideally in one transaction. Cash back only to the original buyer; a gift recipient may take store credit. Minting cost absorbed, never deducted. |
| Issuer cancellation | A co-op cancel power (permanent burn delegate) MAY exist for refunds; every burn publicly logged with a reason code; large vouchers need two signers; disclosed in terms. *Attorney review:* whether this power affects non-custodial status; the conservative alternative is refunds signed by customer and provider. |
| Claim and cure | A claim in the window goes to the provider to fix first; still disputed, to the arbiter. |
| Payout release | Automatic when the claim window closes with no claim. No peer approval of individual payouts. |
| Staged release | Large jobs release in stages (materials, mid-job, final inspection). |
| Contact | Only the provider holding a job messages the customer, in that job's thread. System reminders only if the customer opts in. |
| Monero refunds | Not applicable inside the system (BOLD only); conversion is the customer's own. |

---

## 6. Scheduling and capacity

- **Overflow routing.** With the customer's transfer consent, a job can move to another certified member; transport is free to the customer.
- **Referral credit.** The handoff button records origin; the sending member gets a small share and keeps the customer relationship. Untracked verbal referrals are allowed.
- **Local-first dispatch.** The nearest member gets first chance; independents fill gaps rather than undercut.
- **Emergency board.** "Need it in 4 hours": an alert to members open for urgent work; first to accept wins; rush rate shown upfront; member tow partner. Rush rates obey emergency price-gouging rules in the region's module.
- **Estimators.** Quote in person or by video over Signal or Session. Paid a share; accuracy tracked.
- **Shift board.** Worker members pick hours. Wages paid in dollars on regular paydays (Illinois: at least semi-monthly); crypto optional afterward. *Attorney review:* staffing-agency and employer status.
- **Off-peak.** Cheaper off-peak vouchers, labeled as off-peak. Overtime, zoning and overnight security checked per site.

---

## 7. Pricing and marketplace

- **PR1. Members set their own prices** in their settings and sign changes with their wallet; only their signature changes them.
- **PR2.** New prices apply only to new vouchers. Quotes hold for a stated period (for example 14 days).
- **PR3.** Price changes are timestamped and visible. Every change is checked against the region's caps; over-cap updates are rejected.
- **PR4. Discount codes** are created by each member for itself.
- **PR5. Cross-acceptance.** A member MAY opt in to honor other members' vouchers at face value. Funds in escrow go to whoever does the work; the original seller MAY receive a small share.
- **PR6. Rescheduling elsewhere** is customer-initiated only ("find sooner"). Providers cannot contact other providers' customers. This is a platform design rule, not an agreement among competitors to divide customers.
- **PR7. Bids.** Off-chain until accepted. Sealed: no member sees another's bid until the customer chooses. Optional commit-reveal fingerprints prove no bid changed. Bid coordination is prohibited.
- **PR8. Subcontracting (business-only).** A member MAY offer its job contract to qualified members (credentials and insurance checked), who accept or decline. The customer's price and locked terms never change; the customer is told who does the work; the warranty follows the work. Enabled per region by module.
- **PR9. Co-op-branded services** (optional lane): the co-op sells its own product under its name and warranty, sets its price, and pays members a set rate to perform it. *Attorney review:* joint-venture structure.

---

## 8. Trust: credentials and reviews

### 8.1 Credential tiers

| Tier | Meaning |
| --- | --- |
| Self-reported | Provider entered it and affirmed it is true. Shown as self-reported. |
| Document on file | License or certificate uploaded; expiration tracked; badge drops on expiry, with reminders. |
| Verified | Checked against the issuing authority's public lookup (for example IDFPR), re-checked on a schedule. |

- **C1. Live re-check.** On page load the badge shows *pending* until re-verified. If verification fails: "unknown — treat as NO until resolved with the provider." The system never claims more than it checked.
- **C2. Wording.** "License not required" where none exists (Illinois does not license mechanics); "unlicensed" only for trades that require one (plumbing, electrical, Chicago HVAC).
- **C3. Disclosure labels on every listing:** where work happens (shop, home garage, mobile), insurance and insurer, certifications, warranty.
- **C4.** Insurance arrangements covering more than one party need written confirmation from the insurer.
- **C5. High-volume product sellers** (INFORM Consumers Act thresholds) are verified automatically: tax ID, bank or payment details and contact, recertified yearly. *Attorney review:* applicability to service vouchers.

### 8.2 Reviews

- **RV1.** Verified reviews come only from a completed, redeemed transaction and are tied to it.
- **RV2.** Personal recommendations are allowed but labeled *personal*.
- **RV3.** Review content is never altered by the co-op; removal only for law (for example, defamation findings) and logged.

### 8.3 Quality claims

- Quantity is declared as **minimum** ("no less than 1 kg") or **net**.
- Quality limits ("no more than X ppm") link an accredited lab's certificate of analysis tied to the lot; a seller's claim may be stricter than law, never looser.
- Buyers may weigh or test in the claim window. A failed claim refunds the shortfall or the purchase; the seller covers testing; results go on the seller's record.

---

## 9. Antitrust guardrails

- Members never vote on, discuss or coordinate each other's prices or bids.
- Joint selling and bargaining are protected for agricultural producers (Capper-Volstead). Non-farm joint selling happens only where the co-op is the genuine seller. *Attorney review.*
- No exclusivity. Open membership on equal terms. The charter MAY cap the co-op's share of a local market or require review past a threshold.

---

## 10. Shared services

- **Equipment booking:** large equipment (alignment racks, A/C recovery machines, scanners, forklifts, sewer cameras, tractors) booked through the same engine, with checkout, return and deposit records. Personal hand tools stay personal.
- **Bay sharing:** closed shops rent bays to members.
- **Parts and inventory:** shared visibility of members' stock for emergency jobs.
- **Group purchasing:** insurance, parts and supplies at volume rates.

---

## 11. Mutual support

- **No pooled fund.** Pledge model: the co-op posts a member's need; members give directly or lend labor, case by case. No payout is promised.
- **Real coverage is off-chain** from licensed insurers, promoted through group buying. The co-op takes no commissions or referral fees. Any industry donation is unrelated to sales, never decides recommendations, and is published in the books.
- **Penalties with a way back:** suspension paired with training or counseling; health details stay confidential; only membership status is recorded.

---

## 12. Cooperative finances

- **Running at cost.** Providers keep the full price. The co-op publishes its costs (the "rate case"); members approve them; approved costs are billed as a quarterly assessment in proportion to use; surplus returns as credit or patronage dividends.
- **The co-op's own money** is ordinary business money in a business bank account, kept in standard bookkeeping, with published books. Assessments may be paid by transfer, card or BOLD.
- **Cost-recovery method is a charter setting** (assessment vs. a capped fee at checkout), changed only by vote.
- **Paid roles.** Any role taking real time is a defined, paid role in the budget. Unpaid work for the co-op is avoided (labor law); volunteering belongs in a separate charity with a public purpose.
- **Startup reserve** from founding members covers costs until the first assessment.

*Attorney and CPA review:* Subchapter T treatment, marketplace-facilitator sales tax, 1099 reporting, unclaimed-property treatment of long-unredeemed vouchers.

---

## 13. Launch rule and roles

Functions that need a qualified person stay off until that role is filled and paid (core P8). At launch:

- payments go customer to member escrow, settled in BOLD;
- credentials show as self-reported or on file;
- disputes resolve as refunds until arbiters are in place.

| Role | Until filled | If they leave |
| --- | --- | --- |
| Founder / steward | Holds platform, sales, admin | Founder sunset clause (for example 10 members or 18 months) hands roles to elected members |
| Tech lead | Founder | Code in the shared repo; admin access by multisig; a second admin named |
| Treasurer and signers | 2-of-3 with founder plus co-signers | Remaining signers rotate in a replacement; keys rotated |
| Co-op attorney | Escrow and attestation features off | Engagement names the firm |
| Attestors | Attestation off | Network reassigns |
| Arbiter panel | Disputes resolve as refunds | Panel of at least 3; random assignment |
| Board (business and worker seats) | Founder | Alternates elected with each seat |
| Credential reviewer | Self-reported labels only | Second reviewer trained |
| Bookkeeper / CPA | Simple records | Books in shared software |

Any departure: revoke access, rotate shared secrets, appoint the named backup, log the handover publicly.

---

## 14. Roadmap

1. **Foundation:** attorney, bylaws, Illinois co-op entity, 3–5 founding members in one trade and one area.
2. **Core engine:** vouchers, escrow, check-in, completion, claim window, settlement, refunds, verified reviews, sanctions screening. Test networks only until audited.
3. **Network features:** overflow and referrals, emergency dispatch, estimators, member pricing and discounts, sealed bids, credential tiers.
4. **Second template:** a products vertical such as resale and used goods.
5. **Shared services:** equipment booking, worker shift board, pledge-based support.
6. **Expansion:** parts network, item registry, personal records vault, attestor network, new regions as attorneys sign off.

## 15. Open questions

- Which network(s) at launch, and whether small records go on a lower-cost network.
- Whether the issuer cancel power survives non-custodial review, or refunds require party signatures.
- Exact Illinois treatment of service vouchers as gift certificates.
- Marketplace-facilitator sales tax under the direct-escrow model.
- A self-hosted BOLD payment service for StartOS: watch-only, fresh addresses per invoice, notifies the marketplace; needs an Ethereum node or RPC.
- Wallet onboarding for customers who have never held crypto.
