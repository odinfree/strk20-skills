# starknet.js

Source: https://strk20-by-example.org/starknet-wallet-api/starknet-js

> Call the Starknet Wallet API directly with starknet.js WalletAccountV6 for non-React apps or finer control.

The **`starknet.js` `WalletAccountV6` API** is the direct way to reach the
[Starknet Wallet API](/starknet-wallet-api/overview). Use it when you are working
**outside React**, or when you need **finer control over connection and proof
handling** than the React hooks provide.

## Install

```shell
npm install starknet@^10.8.0
```

**Pin the version.** starknet.js `10.8.0` is the current stable release and
includes Wallet API `0.10.4`, including shadow accounts. The `11.x` line is
published on the npm `next` tag; use it only when your app has completed the
[v10 to v11 migration](https://starknet-js.com/docs/guides/migrate/).

## When to use this

Reach for `WalletAccountV6` directly when a React convenience layer does not fit -
for example non-React frontends, scripts, or flows where you manage wallet
connection and proof handling yourself. If you are building a React dapp, the
[starknet-start `useStrk20` hooks](/starknet-wallet-api/starknet-start-hook) wrap
this same API for you.

## How it works

Your app connects to the user's privacy-enabled wallet through `starknet.js`, then
issues STRK20 actions through the Wallet API. The wallet manages the private
state, ZK proof, and signature wallet-side.

`STRK20_ACTION` now has five variants: `deposit`, `withdraw`, `transfer`,
`invoke`, and `shadow_account_invoke`. The last route executes standard
starknet.js `Call` objects through a persistent per-dapp identity. See
[Shadow Accounts](/starknet-wallet-api/shadow-accounts) for the action shape,
commitments, address resolution, and collection policies.

## What to keep in mind

- **Wallet support is required.** The connected wallet must support the STRK20
  wallet API methods, since the ZK proofs and signatures are managed wallet-side.
- **You own the wiring.** Without the hooks, you handle connection and proof
  handling explicitly.
- **Follow the upstream docs.** For connecting with get-starknet v6 and the
  `WalletAccountV6` API, see the
  [starknet.js WalletAccount guide](https://starknet-js.com/docs/guides/account/walletAccount/#with-get-starknet-v6).

## Read next

- [Starknet Wallet API overview](/starknet-wallet-api/overview)
- [starknet-start](/starknet-wallet-api/starknet-start-hook)
- [Shadow Accounts](/starknet-wallet-api/shadow-accounts)
- [Build Privacy Wallets](/sdk/getting-started)

---
