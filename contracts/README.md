# Contracts

Smart contract sketches for the specs in `spec/`. Each folder pairs with one spec.

**None of these are tested, audited or deployed. Test networks only** (see CONTRIBUTING.md).

| Folder | Spec | State |
|---|---|---|
| [bill-to/](bill-to/) | [spec/bill-to.md](../spec/bill-to.md) | sketch with 22 passing tests (payer picks coin, escrow mode) (`cd contracts/bill-to && npm install && npm test`, Node 18+, local in-process chain, no network); TODOs: permit / ERC-3009 pay, tokenURI |

Licensed under the GNU AGPL v3 with the attribution term in `NOTICE`.
