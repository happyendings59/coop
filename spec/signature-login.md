# Signature Login: Sign a Challenge, No Passwords

> © 2026 Kenneth William Mayle. This document is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/.

**Status:** DRAFT v0.1, 2026-11-23 (Chicago). Idea by Kenny (HAPPY). Spec written by Claude.
Not built, not audited, not security advice. Do not protect anything important with it until an independent security engineer has reviewed it.

**Sources for this spec:** Kenny's design as published at https://kwm59.io/wallet-simplex-login/ (Nov 18, 2026, R2), his idea lines of 2026-11-23 (project ideas inbox), and section 6 of [bill-to.md](bill-to.md). This spec only restates and structures that design. Anything those sources leave open is listed in section 9, not invented.

Document structure follows Kenny's standing rule for technical docs: IEEE 1012 (verification and validation, integrity levels) for section 7 and ISO 37301 (compliance management) for section 8. Section numbers are this document's own. The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119.

---

## 1. Purpose and scope

### 1.1 The problem
Passwords fail in ordinary use. Kenny's lines (2026-11-23): reset loops, a password "saved wrong 3 times, saved without the user ID, just the password. A mess." Phones are the other weak spot: a phone number is how sites find you and where they send the code that proves you are you (see https://kwm59.io/phone-number-dying-identity/).

### 1.2 What this spec defines
One shared login for every 5PM system and Kenny site (co-op, doof.top, rebu.life, nonprofitwebsites templates, Bill To):

- **No password and no phone number.** The account is a public key. You prove it is you by signing a one time challenge with the matching private key.
- **Optional SimpleX delivery.** The challenge can be pushed to you over SimpleX Chat, and you approve it on any of your SimpleX devices (phone, desktop or laptop).

Kenny's description of the flow (2026-11-23): "browser button pastes your public address into the login field; site pings your phone over SimpleX; you approve/sign there. Done."

### 1.3 Out of scope (v0.1)
Account recovery mechanics beyond the requirement in L10, key storage hardware (see the Privacy Server idea, https://kwm59.io/privacy-server/), and payments (see [bill-to.md](bill-to.md)).

---

## 2. Terms

| Term | Meaning |
|---|---|
| Account key | the user's wallet keypair. The public address is the account name |
| Challenge | a message from the service naming the service, a nonce, an issue time and an expiry |
| Nonce | a one time random number; used once, then burned |
| Signing device | the device holding the private key (today, usually the phone) |
| Login device | the device where the user is trying to sign in (for example a laptop browser) |
| SimpleX connection | a SimpleX Chat contact between the user and the service, made once at enrollment by a one time link or QR code |
| Match number | a short number shown on both the login device and the signing device, so the user can see they are approving the login in front of them |

---

## 3. Existing work to build on (do not reinvent)

Found in a GitHub and standards search on 2026-11-23. Licenses are as GitHub reports them; confirm before copying code.

| Work | What we take from it |
|---|---|
| EIP-4361, Sign In with Ethereum (SIWE) | the challenge format: domain, nonce, issued at, expiration time |
| spruceid/siwe (Apache-2.0) and spruceid/siwe-py (Apache-2.0) | reference libraries for building and checking SIWE messages |
| spruceid/siwe-oidc (Apache-2.0) | an OpenID Connect provider for SIWE, so existing sites can add the login without custom code |
| SimpleX Chat | identifier free messaging; first connection by one time link or QR, with a security code to compare (v4.4 release notes) |
| SimpleX bot SDKs, for example a1akris/simploxide (Rust, AGPL-3.0) and reply2future/simplex-chat-gateway (AGPL-3.0) | candidates for the service side bot that sends challenges |
| Number matching in push MFA (Microsoft Authenticator, enforced May 8, 2023; CISA fact sheet) | the match number defense against push fatigue |
| Passkeys (WebAuthn) | the comparison point: the browser binds a passkey to the site's domain, which this design does not get for free |
| twooffive.io | already uses wallet login with 2FA by a second wallet or hardware key; this spec is a variant |

---

## 4. Flows

### 4.1 Enrollment (once per service)
1. The user's wallet signs an enrollment challenge from the service. The service records the public address as the account.
2. Optional: the user gives the service a SimpleX one time link (or scans the service's QR). The user SHOULD make this first connection through a separate channel and compare the SimpleX security code.

### 4.2 Login, same device
1. The user clicks the login button; the wallet fills in the public address.
2. The service issues a challenge; the wallet shows it and signs.
3. The service checks the signature, the domain and the expiry, and burns the nonce.

### 4.3 Login, pushed over SimpleX
1. On the login device, the user's public address is entered (button paste).
2. The service sends the challenge over the enrolled SimpleX connection. The login device shows a match number.
3. On any of the user's SimpleX devices, the user sees who is asking and the same match number, approves, and the wallet signs.
4. The signature returns to the service, which checks it as in 4.2 and logs the login device in.

---

## 5. Requirements

Each line traces to the source design. IL = integrity level (section 7.1).

| ID | Requirement | Source | IL |
|---|---|---|---|
| L1 | A service MUST NOT require a password or a phone number to create or use an account | inbox 2026-11-23; phone number post | 3 |
| L2 | The account identifier MUST be a public key / address; proof of control MUST be a signature over a service issued challenge | kwm59 post; bill-to.md §6 | 4 |
| L3 | The challenge MUST name the service's domain and carry a nonce, issue time and expiry (EIP-4361 fields for Ethereum keys) | kwm59 post; bill-to.md §6 | 4 |
| L4 | The service MUST check the signature and the domain, reject expired challenges, and burn each nonce after one use | bill-to.md §6 | 4 |
| L5 | The signing wallet MUST show the user who is asking before signing | kwm59 post | 3 |
| L6 | Pushed approvals MUST show a match number on both the login device and the signing device | kwm59 post (number matching) | 3 |
| L7 | SimpleX delivery is OPTIONAL; same device signing (4.2) MUST work without it | kwm59 post; bill-to.md §6 | 2 |
| L8 | Enrollment over SimpleX SHOULD use an out of band link and a compared security code | kwm59 post | 3 |
| L9 | The service MUST NOT store anything beyond the public address and, if enrolled, the SimpleX connection; no email or phone is required | kwm59 post; core.md P4 | 3 |
| L10 | Every service MUST offer a recovery path for a lost key (a backup key or a person who can vouch); the method is open (section 9) | kwm59 post | 3 |
| L11 | The same key MAY be the account on every 5PM site and the wallet that pays a Bill To bill | bill-to.md §6 | 2 |
| L12 | Biometrics MUST NOT be collected by the service (any fingerprint or face unlock stays on the user's own device) | core.md PV4 | 3 |

---

## 6. Threats and limits (from the source design)

| Threat | Effect | Control |
|---|---|---|
| Push fatigue (attacker spams approvals) | user taps yes | L6 match number; no password exists to steal first, but a known address still allows spam |
| Man in the middle at enrollment | attacker swaps keys on the first connection | L8 out of band link and security code |
| Relayed challenge (phishing site forwards a real challenge) | user signs for the real site while on a fake one | L3, L4 domain in the signed message; L5 wallet shows the asker. Weaker than a passkey: no browser enforces the domain |
| Lost key | user locked out | L10 |
| Compromised login device | can start logins, cannot sign | design assumes the signing device is separate |
| Compromised signing device | worst case, the key lives there | out of scope; hardware key storage is a future option |

Kenny's assumption, kept as stated: it holds "long as you have control of both devices." And: "people do stupid things." These layers reduce the ways to fail; they do not remove them.

---

## 7. Verification and validation plan (IEEE 1012 structure)

### 7.1 Integrity levels
| IL | Meaning here | Components |
|---|---|---|
| 4 | account takeover | signature check, domain check, nonce burn, expiry |
| 3 | wrong account approved or user misled | match number, wallet display, enrollment, recovery |
| 2 | login fails, recoverable | SimpleX delivery, retries |
| 1 | cosmetic | button text, styling |

### 7.2 V&V tasks
| Task | IL 4 | IL 3 | IL 2 | IL 1 |
|---|---|---|---|---|
| Requirements traceability (each L to a test) | yes | yes | yes | |
| Unit tests | 100% branch | 100% line | yes | |
| Negative tests (wrong domain, reused nonce, expired, wrong key, malformed message) | yes | yes | | |
| Independent security review | required before real use | required | | |
| User acceptance on each consuming site | yes | yes | yes | yes |

### 7.3 Validation scenarios
- Laptop login approved on phone over SimpleX; match numbers agree.
- Same login approved from SimpleX desktop instead of phone.
- Replayed signature: rejected (nonce burned).
- Signature for another domain: rejected.
- Challenge approved after expiry: rejected.
- Spam approvals: user can see each one names an unknown login device and number.
- Lost phone: recovery path completes without a password or phone number.

### 7.4 Anomaly reporting
Every failed test or finding is logged with IL, status and fix commit.

---

## 8. Compliance management (ISO 37301 structure)

Not legal advice. Questions for counsel before real use.

| ID | Obligation (area) | Why it may apply | Initial position | Owner |
|---|---|---|---|---|
| CL1 | Privacy (state privacy laws, GDPR for EU visitors) | a wallet address can be linked to a person | store only L9 data; privacy notice; no linking (core.md PV2) | site operator |
| CL2 | Biometric privacy (Illinois BIPA) | heavy statutory penalties | L12: no biometrics collected | site operator |
| CL3 | Accessibility (ADA, WCAG) | users who cannot run a wallet or SimpleX | a recovery or assisted path must exist (L10); which one is open | site operator |
| CL4 | Security representations (FTC Act, state UDAP) | calling it "secure" overclaims | label as reduced risk, never "safe"; CONTRIBUTING.md rule 5 | Kenny |
| CL5 | Third party terms (SimpleX, wallet apps) | bots and message signing depend on their terms | check before launch | Kenny |

Review the register at each new site launch and after any change to the source design.

---

## 9. Open questions (not decided by the source design)

1. Which key types beyond Ethereum? Kenny named a "SimpleX/Monero signature login"; Monero wallets such as Cake Wallet can sign messages, but the challenge format for Monero is not defined here.
2. Recovery method: backup key, a vouching person, or both (L10)?
3. Does wallet message signing work on desktop wallets (Cake Wallet desktop was not confirmed)? Until then the phone is assumed to sign.
4. Build our own SimpleX bot, or use one of the SDKs in section 3?
5. Use siwe-oidc so sites get standard OpenID Connect, or check SIWE in each site?
