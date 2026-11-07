# 5PM Cooperative

**Let's merge, without becoming a monopoly.**

5PM is an open specification for a member-owned network where independent businesses (small farms, shops, trades, restaurants, resale stores and makers) share the back office, sell together and back each other up, while each keeps its own name, customers and prices.

This repository holds the **specification**, not working code yet. Developers are invited to read it, challenge it, and build against it.

- Project page: https://5pm.io/coop/
- Status: **draft, in formation.** Nothing here is audited, deployed or legal advice.

## Principles

- **Non-custodial.** No operator holds or controls other people's money.
- **No admin keys over user funds.** Contracts holding value can't be upgraded, drained or redirected by anyone running the system.
- **Providers keep the full price of their work.** The cooperative runs at cost, like an electric cooperative.
- **One member, one vote.** No lock-in; members sell anywhere and leave freely.
- **Privacy by design.** Collect only what a transaction needs. No tracking.
- **Chain-agnostic.** Today: settlement in BOLD, an immutable USD stablecoin with no freeze function, on Ethereum-compatible networks. Tomorrow: whatever best meets the published criteria.
- **Law by module.** Jurisdictional rules live in versioned modules approved by local attorneys.
- **Off by default.** Anything needing a qualified person or legal sign-off stays switched off until it has one.

## Specifications

| Document | What it covers |
| --- | --- |
| [spec/core.md](spec/core.md) | Shared foundation: data placement, privacy, attestations, status flags and liens, escrow safety powers, jurisdiction modules, encrypted documents, chain selection, governance |
| [spec/cooperative.md](spec/cooperative.md) | The cooperative marketplace: the nine-step transaction engine for products and services, vouchers, side paths, scheduling, pricing, credentials and reviews, finances, roles, roadmap |
| [spec/document-delivery.md](spec/document-delivery.md) | The 2024 NFT-backed legal document delivery platform (Cardano and Monero as candidate networks), published with a 2026 revision note |

Start with `core.md`.

## Getting involved

- **Developers:** read [CONTRIBUTING.md](CONTRIBUTING.md), then pick up an open question in an issue. Test networks only; no real funds.
- **Businesses, attorneys, CPAs and other founding roles:** see https://5pm.io/coop/.

## License

Code is licensed under the **GNU AGPL v3** ([LICENSE](LICENSE)) with an additional attribution term under section 7(b) ([NOTICE](NOTICE)). The specification and documentation are licensed under **CC BY 4.0** ([LICENSE-docs](LICENSE-docs)).

© 2026 Kenneth William Mayle.
