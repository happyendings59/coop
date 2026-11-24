# 5PM Open Business Directory Specification

> © 2026 Kenneth William Mayle. This document is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/. You may share and adapt it, including commercially, as long as you give credit.

**Status:** Draft 0.1, November 2026. Builds on [core.md](core.md). Design intent only: not audited, not legal advice. Items marked *attorney review* need qualified counsel before implementation. Requirement words MUST, SHOULD and MAY follow RFC 2119. The layout follows ISO/IEC/IEEE 29148 (requirements) and each requirement names how it is verified, in the spirit of IEEE 1012.

---

## 1. Purpose

A free, open "yellow pages" of businesses: name, address, phone, website, category and opening hours, seeded only from data whose license allows bulk reuse, then corrected and owned by the businesses themselves. It is the starting list for the cooperative marketplace ([cooperative.md](cooperative.md)), rebu.life and other 5PM sites.

## 2. Scope

In scope: (a) the loader that builds a regional extract, (b) public business pages, (c) the owner claim flow, (d) notices inviting owners to claim. Out of scope: reviews and payments (see cooperative.md).

## 3. Definitions

- **Place:** one business location. A chain with ten stores is ten places.
- **Extract:** the loader's output for one region (places.parquet, places.csv, ATTRIBUTION.md, run.json).
- **Claim:** a person proving they control a place, after which they can edit it.
- **Notice:** a message telling a business its page exists and how to claim it.

## 4. Data sources

### 4.1 Allowed

| Source | What it gives | License | Notes |
| --- | --- | --- | --- |
| Overture Maps places | name, address, phone, website, email, socials, category, open/closed, confidence | CDLA-Permissive-2.0 (some rows Apache-2.0 or CC0-1.0) | Public S3, no account. Release 2026-11-18.0 has **no opening hours field** (schema checked 2026-11-24). |
| OpenStreetMap | the same plus **opening_hours** | ODbL 1.0, share-alike | Overpass API for a region, or a Geofabrik extract. Follow the Overpass usage policy. |
| Foursquare Open Source Places | name, address, phone, website, socials, category | Apache-2.0 | Free gated download since 2025; read from a local copy. Overture already contains many of these rows. |

### 4.2 Not allowed

Google Maps, Yelp, Yellow Pages and LinkedIn MUST NOT be scraped. Their terms forbid automated collection, and the Google and Yelp APIs limit how long results may be stored, so they cannot seed a permanent directory. *Attorney review* before any paid API is added (§8).

## 5. Data model

Every source maps into one record: `uid, name, category, street, city, state, postcode, country, lat, lon, phone (E.164), website, email, socials, opening_hours (OSM syntax), status, confidence, sources, licenses, claim_status`. Field notes live in `tools/directory-loader/dirload/schema.py`.

## 6. Requirements

### 6.1 Loader

| ID | Requirement | Verified by |
| --- | --- | --- |
| L1 | The loader MUST read only the sources in §4.1. | Code review; sources list in run.json |
| L2 | Every row MUST keep the ids of every source record merged into it (`sources`) and their licenses (`licenses`). | Unit test `test_cross_source_merge_takes_osm_hours` |
| L3 | Each extract MUST ship an ATTRIBUTION.md naming every source and its license. When OSM rows are present the whole extract MUST be marked ODbL. | Inspect ATTRIBUTION.md |
| L4 | Duplicates across sources MUST be merged; two branches with different house numbers MUST NOT be. | Unit tests in `tests/test_dirload.py` |
| L5 | Opening hours MUST prefer OSM when several sources carry them. | Unit test |
| L6 | Places marked permanently closed SHOULD be dropped unless asked to keep them. | `--keep-closed` flag |
| L7 | Each run MUST report field coverage (share of rows with phone, website, hours and so on). | run.json `coverage` |
| L8 | The loader MUST be rerunnable for any bounding box and MUST NOT need an account for Overture or OSM. | `--bbox` run |

### 6.2 Business pages

| ID | Requirement |
| --- | --- |
| P1 | One public page per place, at a stable URL built from `uid`. |
| P2 | An unclaimed page MUST say so plainly ("This listing was built from open map data and has not been checked by the business") and show a **Claim this business** button. |
| P3 | Each page MUST show its source attribution (for example "© OpenStreetMap contributors"). |
| P4 | Anyone MAY report a page as closed, moved or wrong; reports go to the owner if claimed, else to review. |
| P5 | Pages MUST NOT carry tracking scripts or third party ads (core.md §3). |
| P6 | A business MAY ask for its page to be removed; an unclaimed page is removed on request. |

### 6.3 Owner claim (LinkedIn style)

A person signs in with a signature login ([signature-login.md](signature-login.md): sign a challenge with a wallet, no password), then proves control of the place by one of these, strongest first:

| ID | Method | Notes |
| --- | --- | --- |
| C1 | Code sent to the email address at the website's own domain (for example info@joespizza.com when the listed site is joespizza.com) | Free webmail addresses do not count |
| C2 | A DNS TXT record or a `/.well-known/5pm-claim.txt` file on the listed website | Same idea as domain verification for search consoles |
| C3 | Code read out by an automated call or text to the **listed** phone number | The number on the page, never one the claimant types; *attorney review* for TCPA consent rules |
| C4 | Code on a postcard mailed to the listed address | Slow but works for places with no website |
| C5 | Manual review of documents (business license, utility bill) | Last resort |

| ID | Requirement |
| --- | --- |
| C6 | A claim MUST be tied to the claimant's signing key, so later edits are signed. |
| C7 | A second claim on a claimed place MUST freeze edits and go to review; nobody is silently replaced. |
| C8 | Owners MUST be able to edit hours, phone, website, category, photos by link, and mark the place closed. Every edit is versioned and shown in a public history. |
| C9 | Owners SHOULD be offered a one click option to send their corrected hours back to OpenStreetMap under their own account, so the open map improves for everyone. |
| C10 | Owner edits stay with the owner: owners choose the license of what they add (default CC BY 4.0), separately from the seed data's license. *Attorney review* on mixing with ODbL rows. |

### 6.4 Notices

| ID | Requirement |
| --- | --- |
| N1 | Nothing is sent without the operator approving each batch (who, how many, which channel, the exact text). |
| N2 | Email goes only to the business's **published** business address. Each email MUST carry an honest subject and sender, the operator's postal address, and a working one click opt out honored within 10 business days (CAN-SPAM). *Attorney review.* |
| N3 | Opt outs and "do not contact" requests MUST go on a suppression list checked before every send. |
| N4 | Postcards MAY be mailed to the listed address. |
| N5 | **LinkedIn:** the system MUST NOT send LinkedIn messages, connection requests or posts automatically, and MUST NOT scrape LinkedIn. LinkedIn's terms forbid both. Instead it MAY prepare a ready to paste note and a link to the claim page for a person to send by hand from their own account, one at a time. |
| N6 | No robocalls or bulk texts as notices (TCPA). |
| N7 | Every notice sent is logged: date, channel, place, text version, and outcome (claimed, opted out, no reply). |

## 7. Coverage today (Chicago, measured)

Overture release 2026-11-18.0, Chicago box (-87.94, 41.64, -87.52, 42.03), confidence at least 0.5, closed places dropped: **177,185 places**. Share with street address 98.7%, phone 87.5%, website 78.9%, category 97.5%, socials 44.7%, public email 27.7%, **opening hours 0%** (Overture has no hours field).

With OpenStreetMap added (GitHub Actions run, same day): **187,501 places**, of which 28,185 carry OSM data and about 18,600 are matched across both sources. **Opening hours: 2.95%, about 5,500 places.** Free open data will not supply hours at scale; owner claims (§8.1) must.

## 8. Filling the hours gap, legally

1. **Owners claim and enter hours** (§6.3). This is the main path and the reason for the claim flow.
2. **OpenStreetMap** hours where they exist, and owners sending corrections back (C9).
3. **The business's own website**, reading schema.org `openingHours` markup, one polite fetch, honoring robots.txt, only for places with no hours. Off by default. *Attorney review.*
4. **Paid API with storage rights**, such as Foursquare's paid Places API, only if its terms allow keeping the data. Google Places and Yelp Fusion do not allow keeping it. *Attorney review.*
5. **Volunteers** from member businesses checking hours on the street, entered as signed edits.

## 9. Open questions

1. Which repo hosts the business pages: rebu.life, 5pm.io, or a new one?
2. Does the cooperative publish the merged extract (ODbL) for others to download? Recommended yes.
3. Minimum Overture confidence: 0.5 drops about 31% of raw rows in Chicago; owners can still claim a dropped place by adding it.
