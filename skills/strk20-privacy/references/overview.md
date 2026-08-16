# Overview

Source: https://strk20-by-example.org/overview

> A concise builder overview for choosing the right STRK20 integration route

Here's everything about getting started with building private applications.

Starknet privacy has a small set of builder surfaces. Start with the highest-level
route that fits your product, and only move lower when you need more control.

## Choose your integration route

| Builder goal                                                                                | Start with                                                                                               |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Build a private dapp anywhere from private DeFi, private consumer apps, private games, etc. | [Anonymizer Contracts](/helpers/privacy-invoke) and [Starknet Wallet API](/starknet-wallet-api/overview) |
| Build a privacy wallet or advanced backend                                                  | [Build Privacy Wallets](/sdk/getting-started)                                                            |
| Run proof infrastructure yourself                                                           | Prover backend                                                                                           |
| Hide a user's main-wallet link during account-based app activity                            | Private sub-accounts (SDK route available; Wallet API pending)                                           |
| Fund a private balance from an EVM wallet, or withdraw it back to one                       | [Privacy Bridge](https://github.com/starkware-libs/privacy-bridge)                                       |

## Core pieces

- **STRK20 Pool:** the live Starknet mainnet pool that holds ERC-20s as encrypted
  notes and enables shielded balances, private transfers, and private DeFi.
- **Starknet Wallet API / starknet.js:** the standard route for private dapps. The
  app asks the wallet to act; the wallet manages viewing keys, notes, proofs, and
  signatures.
- **Anonymizer contracts:** app-specific `privacy_invoke` adapters for DeFi. The pool
  calls the helper atomically, then credits the result back into private notes.
- **Privacy SDK:** the low-level route for wallets and advanced integrations that
  need direct control over registration, channels, note discovery, and proving.
  Open source (Apache 2.0): [starkware-libs/starknet-privacy](https://github.com/starkware-libs/starknet-privacy),
  quickstart in [`sdk/README.md`](https://github.com/starkware-libs/starknet-privacy/blob/main/sdk/README.md).
- **Privacy Bridge:** a value-movement engine that moves USDC between EVM
  wallets/chains and the pool over Circle CCTP, so the funding side and the
  withdrawal side are not linked onchain. It ships its own `OutboundAnonymizer`
  and `InboundAnonymizer` Cairo contracts plus a TypeScript engine with React
  hooks. Open source (Apache 2.0), early:
  [starkware-libs/privacy-bridge](https://github.com/starkware-libs/privacy-bridge).
- **Private sub-accounts:** an advanced account-privacy route for hiding the
  public link between a user's main wallet and app activity. The SDK route ships
  in Privacy SDK `0.14.3-rc.4`; the Wallet API route is still pending, so dapps
  relying on the user's wallet cannot use them yet.
- **Prover backend:** infrastructure for teams that need to operate their own proof
  generation.

## What stays visible

Inside the pool, sender, receiver, token, amount, and spent notes are private.
Deposits, withdrawals, timing, and some app-side activity may still be public.

## Start from a template

The [STRK20 starter kit](https://github.com/Akashneelesh/strk20-starter-kit) is a
lean Next.js app with the Wallet API route already wired: wallet picker,
shield / unshield / private transfer, shielded balances, and a deployable
`privacy_invoke` helper. [Try the live demo](https://starknet-privacy-starter.vercel.app/),
then swap the `DEMO`-labelled defaults for your own token and helper.

## Read next

- [Anonymizer Contracts](/helpers/privacy-invoke)
- [Starknet Wallet API](/starknet-wallet-api/overview)
- [Private DeFi End to End](/starknet-wallet-api/private-defi)
- [AVNU Private Swaps](/starknet-wallet-api/avnu-private-swaps)
- [Build Privacy Wallets](/sdk/getting-started)

---

