# Contributing to 5PM

Thanks for helping. This project builds systems that will eventually hold other people's money and records, so a few rules are firm.

## Ground rules

1. **Test networks only.** Never deploy anything from this repository with real funds until an independent security audit is complete and the project has approved a mainnet release.
2. **Never commit secrets.** No private keys, seed phrases, wallet files, API keys or `.env` files. The `.gitignore` blocks common cases; it is not a guarantee. If you commit a secret by mistake, treat it as compromised and rotate it.
3. **No custody, no admin keys over user funds, no mixing.** Contributions that give any operator the ability to hold, redirect or obscure user funds will not be accepted. See `spec/core.md` §1, §3 and §6.
4. **No personal data on-chain.** See `spec/core.md` §2.
5. **Keep it honest.** Don't describe a feature as legally valid, compliant or "verified" unless it has been checked. Use "designed to support."

## How to contribute

- **Spec changes:** open an issue describing the problem first, then a pull request editing the relevant file under `spec/`. Reference requirement IDs (for example `core.md E4`).
- **Open questions:** each spec ends with open questions; issues for these are welcome.
- **Code:** when implementation begins, each component will live in its own folder with tests. Every contract change needs tests covering the refund-only safety power and the no-admin-key rule.

## Testing

- Use public test networks and test tokens.
- Include tests for the side paths, not just the happy path: refunds, no-shows, disputes, expired windows, sanctions blocks and valid-in rejections.
- Security findings: please report privately to the maintainer through the contact on https://5pm.io/cooperate/ rather than opening a public issue. A paid bug bounty will follow once the project is funded.

## Licensing of contributions

By submitting a contribution, you agree that:

- code you contribute is licensed under the GNU AGPL v3 with the additional attribution term in `NOTICE`;
- documentation you contribute is licensed under CC BY 4.0;
- you have the right to submit it; and
- you grant Kenneth William Mayle a perpetual, worldwide, royalty-free license to relicense your contribution under other open-source or proprietary terms, so the project's licensing can change in the future without tracking down every contributor. You keep the copyright in your contribution.

Sign off each commit (`git commit -s`) to confirm you agree.

## Conduct

Be direct and respectful. Disagree about designs, not people. Harassment isn't tolerated.
