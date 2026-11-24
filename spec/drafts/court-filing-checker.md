# Court Filing Checker (DRAFT stub)

> © 2026 Kenneth William Mayle. Licensed under CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.

**Status:** DRAFT stub, 2026-11-23. Idea by Kenny (HAPPY). Not a spec yet. Not legal advice.

## The idea as stated (ideas inbox, 2026-11-23)
- A checker loads the assigned judge's standing orders and local rules and **rejects a filing by default** until it passes them all.
- It also flags "common sense" problems and returns the filing with plain comments (for example "weak claim, here's why") before the court sees it.
- Groups recurring issues so similar cases are matched to existing cases, precedent, or a joint or class effort; similar case law with outcomes, verified citations only (for example via CourtListener).
- Toggles: ethics aware strategy options and a detail dial (hard detail, just what you need, explain by analogy, "link me"). Guardrail: toggles may omit or decline to admit, never assert falsehoods (candor to the tribunal, Rule 11).
- **Receiver side:** courts and opposing counsel automatically verify every citation in filings received. Failures are called out on the record; the filer fixes; sanctions only for repeat or deliberate cases.
- Offered as a service: free tier (automated rule check), paid tier (deeper review, human in the loop).

## How it touches existing specs
- core.md §13.3 already permits "completeness checks before a filing is submitted" (JC7) and sets unauthorized practice of law limits (JC9).
- **Possible conflict:** Kenny's idea includes a non binding merits opinion ("weak case", "consider settling"). core.md JC8 prohibits "scoring a party's ... likelihood of success." JC8 reads as aimed at court-side use; whether a filer-side opinion is allowed, and only through a licensed attorney (JC9), needs a decision.
- core.md §13.4 (local AI, logged, replaceable) would apply to the receiver side checker.

## Open questions
1. Resolve the JC8 question above.
2. Where do standing orders and local rules come from, and who keeps them current (a jurisdiction module under core.md §7)?
3. Free tier scope that stays general information under JC9.
