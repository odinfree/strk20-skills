# Builder Privacy Overview

Source: https://strk20-by-example.org/builder-privacy-overview

> Choose the right STRK20 integration path: Starknet Wallet API, anonymizer contracts, building privacy wallets, sub-accounts, or prover infrastructure.

STRK20 is a privacy pool plus a small set of integration surfaces. Start with
the narrowest surface that keeps user keys in the right place and only move to a
lower-level route when your product needs more control.

## Quick decision guide

| If you want to...                                                                           | Use...                                                                                                   | Why                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Build a private dapp anywhere from private DeFi, private consumer apps, private games, etc. | [Anonymizer contracts](/helpers/privacy-invoke) and [Starknet Wallet API](/starknet-wallet-api/overview) | The wallet manages viewing keys, notes, proving, and submission; for DeFi, the pool calls your `privacy_invoke` adapter atomically, then credits the result back into private notes. |
| Build a privacy wallet on Starknet                                                          | [Build Privacy Wallets](/sdk/getting-started)                                                            | Direct access to registration, channels, note discovery, transaction building, and proving configuration.                                                                            |
| Operate proving infrastructure yourself                                                     | Prover backend                                                                                           | For wallets and infrastructure teams that need control over proof generation.                                                                                                        |
| Hide the link between a user's main wallet and app activity                                 | Private sub-accounts (SDK route available; Wallet API pending)                                           | Advanced account-based privacy route; SDK-route teams can start today, dapps relying on the user's wallet must wait.                                                                 |
| Let users fund a private balance from an EVM wallet and withdraw it back to one             | [Privacy Bridge](https://github.com/starkware-libs/privacy-bridge)                                       | Moves USDC between EVM chains and the pool over Circle CCTP, with its own inbound/outbound anonymizer contracts, so the two sides are not linked onchain.                            |

## Core surfaces

### STRK20 pool

The pool is the base contract layer. Deposits move public ERC-20 tokens into the
pool, private transfers spend encrypted notes inside the pool, and withdrawals
move tokens back to a public address. Movement inside the pool hides sender,
receiver, token, amount, and spent notes from public observers.

### Starknet Wallet API

This is the recommended route for most **private dapps**. Your dapp asks the
user's privacy-enabled wallet to perform an action; the wallet handles private
state, proofs, and submission. A normal dapp should not receive the user's
viewing key or manage note discovery directly. See the
[Starknet Wallet API overview](/starknet-wallet-api/overview).

### Anonymizer contracts

Anonymizer contracts, also called helper contracts, are app-specific Cairo
adapters for private DeFi. The pool withdraws tokens to the helper, calls its
`privacy_invoke` entry point, and the helper returns `OpenNoteDeposit`
instructions for whatever should be credited back into private notes. This is the
focus for **core builders shipping private dapps**. See
[Anonymizer Contract Anatomy](/helpers/privacy-invoke).

### Privacy Bridge (EVM to pool)

Most users hold their USDC on an EVM chain, not on Starknet. The
[Privacy Bridge](https://github.com/starkware-libs/privacy-bridge) is a
value-movement engine for exactly that gap: it takes USDC from an EVM wallet and
deposits it into the pool as a private note, and moves value back out to an EVM
chain, using Circle's CCTP for the cross-chain leg. Both directions run through
its own Cairo anonymizer contracts - `OutboundAnonymizer` on the way out,
`InboundAnonymizer` on the way back in - so the deposit side and the withdrawal
side cannot be linked onchain. All client-side key material is derived from a
single wallet signature; only the read-only viewing key may be persisted.

The repository is open source (Apache 2.0) and ships three parts: the
`bridge-anonymizers` Cairo contracts, the framework-agnostic
`@starkware-libs/starknet-privacy-bridge` TypeScript engine with optional React
hooks, and a demo web app. It is early and moving fast - read its README before
planning around it.

### Build Privacy Wallets

The Build Privacy Wallets section is the lower-level SDK route for teams building
**privacy wallets on Starknet**, account-controlled backends, and advanced
integrators. Use it when you need to
manage registration, channels, note discovery, transaction construction, and
proving providers yourself. See [Build Privacy Wallets](/sdk/getting-started).

### Private sub-accounts

Private sub-accounts are for account-based app activity where the user does not
want a public onchain link to their main wallet.

**Status is split.** The **SDK route is available** as of Privacy SDK
`0.14.3-rc.4`: `transfers.build().subaccounts(dappName).invoke(...)`, backed by
the `sub_account_anonymizer` contract package. The **Wallet API route is not** —
no sub-account method is exposed by `@starknet-io/types-js` 0.10.3 or
starknet.js, so a dapp relying on the user's wallet cannot use them yet.

If you build the account yourself (a wallet, or a backend holding its own keys),
you can start now. If you rely on the user's wallet, wait for the Wallet API
call. Confirm audit readiness either way.

### Prover backend

Most dapps do not need to operate proving infrastructure. Wallets,
infrastructure teams, and advanced integrators may run their own prover when
they need operational control over proof generation. Deposit screening applies
regardless of proving route: FPI screens shielding addresses and signs each
deposit, and the pool verifies the signature onchain, so a self-hosted prover
meets the same deposit-screening requirement as hosted services.

## Builder rules of thumb

- Use the Starknet Wallet API first for user-facing private dapps.
- Use Build Privacy Wallets when you are building the wallet itself or need low-level SDK control.
- Do not ask a normal dapp user for their viewing key.
- For private DeFi integrations, expect both a Starknet Wallet API flow and an app-specific anonymizer contract.
- Deposits are screened on every route - self-hosted proving does not bypass onchain screening.
- Be explicit about what remains public: deposits, withdrawals, timing, and some app-side activity may still be visible.
- Verify wallet support, API versions, contract addresses, and compliance assumptions before launch.

## Read next

- [What is STRK20?](/what-is-strk20)
- [Starknet Wallet API](/starknet-wallet-api/overview)
- [Anonymizer Contract Anatomy](/helpers/privacy-invoke)
- [Build Privacy Wallets](/sdk/getting-started)

---

