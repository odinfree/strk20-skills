# Starknet Wallet API

Source: https://strk20-by-example.org/starknet-wallet-api/overview

> The standard route for private dapps on Starknet: ask a privacy-enabled wallet to shield, transfer, and withdraw via starknet.js.

The **Starknet Wallet API** is the recommended route for most **private dapps**.
Instead of managing private state yourself, your dapp asks the user's
privacy-enabled wallet
to perform a private action, and the wallet handles keys, notes, proving, and
submission.

Use this route when you are building an app **on top of** existing privacy
wallets. If you are building the wallet itself, use the
[Build Privacy Wallets](/sdk/getting-started). If your app needs private DeFi,
pair this route with an [Anonymizer Contract](/helpers/privacy-invoke).

## Install

```shell
npm install starknet@^10.4.0
```

**Pin the version.** STRK20 support landed in starknet.js 10.4.0 and ships on the
npm `next` tag. A bare `npm install starknet` resolves to `latest`, which is
still 10.0.x and contains none of the STRK20 API — `WalletAccountV6`,
`strk20InvokeTransaction`, and `STRK20_ACTION` will all be missing.

## Why most dapps want this route

- **No viewing keys in your app.** The wallet holds the user's viewing key; your
  dapp never sees it.
- **No note or proof management.** The wallet discovers notes, builds the
  transaction, generates the proof, and submits it.
- **Standard Starknet integration.** You connect and call through `starknet.js`
  and the user's wallet, the same way you already integrate other Starknet
  actions.

## How it fits together

Your dapp talks to `starknet.js`, which reaches the user's privacy-enabled wallet
through the Starknet Wallet API. The wallet runs the STRK20 SDK internally and
settles against the privacy pool. For private DeFi, the same call path also triggers your app-specific
[anonymizer contract](/helpers/privacy-invoke).

## React hooks or direct WalletAccountV6?

There are two practical ways to use the Starknet Wallet API from a dapp, each with
its own page in this section:

- **React dapps:** use the
  [starknet-start `useStrk20` hooks](/starknet-wallet-api/starknet-start-hook), a
  convenience wrapper that calls into a `WalletAccountV6` (or equivalent) under the
  hood.
- **Outside React, or when you need finer control** over connection and proof
  handling: use
  [starknet.js `WalletAccountV6`](/starknet-wallet-api/starknet-js) directly.

In both cases the wallet itself must support the STRK20 wallet API methods, since
the ZK proofs and signatures are managed wallet-side.

## What you can do through the wallet

Without writing any privacy cryptography, a dapp can ask the wallet to:

- **Shield** - deposit public ERC-20 tokens into the pool.
- **Private transfer** - move value privately between registered users.
- **Withdraw (unshield)** - move tokens back out to a public address.
- **Swap** - where the connected wallet supports it.

Broader DeFi actions (lending, staking, custom flows) pair the Starknet Wallet
API with an app-specific anonymizer contract that the pool invokes atomically —
see [Private DeFi End to End](/starknet-wallet-api/private-defi) for the wiring.

## What to keep in mind

- **Wallet support varies.** Available actions depend on the connected wallet;
  detect capabilities before offering an action.
- **Edges stay public.** Deposits and withdrawals expose public ERC-20 legs and
  timing, even though in-pool movement is private.
- **Verify versions and addresses.** Confirm wallet, `starknet.js`, and pool
  contract details for your target network before launch.

## Choose your route

| You are building...                                                                   | Start here                                                                          |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| A private dapp anywhere from private DeFi, private consumer apps, private games, etc. | [Anonymizer Contracts](/helpers/privacy-invoke) and Starknet Wallet API (this page) |
| A Starknet privacy wallet                                                             | [Build Privacy Wallets](/sdk/getting-started)                                       |

## Read next

- [starknet-start](/starknet-wallet-api/starknet-start-hook)
- [starknet.js](/starknet-wallet-api/starknet-js)
- [Anonymizer Contract Anatomy](/helpers/privacy-invoke)
- [Build Privacy Wallets](/sdk/getting-started)

---

