# Owner-Controlled Contacts (DRAFT stub)

> © 2026 Kenneth William Mayle. Licensed under CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.

**Status:** DRAFT stub, 2026-11-23. Idea by Kenny (HAPPY). Not a spec yet.

## The idea as stated
From the project ideas inbox, 2026-11-23: "Owner-controlled contacts (QR/NFC, per-field sharing, emergency-only medical access, no police access without permission)."

Related published ideas: https://kwm59.io/phone-number-dying-identity/ (retire the phone number as ID) and https://kwm59.io/privacy-server/ (a home box with its own key chip).

## How it touches existing specs
- core.md §3 (privacy: owner first, data minimization) and §8 (encrypted documents released only to named recipients).
- [signature-login.md](../signature-login.md): the same account key could control who sees which field.

## Open questions
1. What does "per-field sharing" cover (name, address, SimpleX link, medical notes)?
2. Who counts as an emergency reader for medical fields, and how do they prove it (an attestation under core.md §4)?
3. "No police access without permission" versus valid legal process: core.md PV3 answers process only for data the operator holds. Where is the data held?
