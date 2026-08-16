# starknet-start

Source: https://strk20-by-example.org/starknet-wallet-api/starknet-start-hook

> Use the starknet-start useStrk20 React hooks as a convenience wrapper over the Starknet Wallet API.

The **`useStrk20` hooks** from
[Starknet Start](https://starknet-innovation.github.io/starknet-start/docs/hooks/use-strk20/#hooks)
are a convenience wrapper over the [Starknet Wallet API](/starknet-wallet-api/overview).
They are the recommended starting point for **React dapps**.

## Install

```shell
npm install starknet@^10.4.0
```

**Pin the version.** STRK20 support landed in starknet.js 10.4.0 and ships on the
npm `next` tag. A bare `npm install starknet` resolves to `latest`, which is
still 10.0.x and contains none of the STRK20 API — `WalletAccountV6`,
`strk20InvokeTransaction`, and `STRK20_ACTION` will all be missing.

## When to use this

Use the hooks when you are building a **React dapp** on top of an existing
privacy-enabled wallet and want to request STRK20 actions without wiring each
wallet call by hand. If you are working outside React, or need finer control over
connection and proof handling, use
[starknet.js `WalletAccountV6`](/starknet-wallet-api/starknet-js) directly.

## How it works

The hooks call into a `WalletAccountV6` (or equivalent) under the hood. Your React
components ask for a private action; the connected wallet manages the private
state, ZK proof, and signature wallet-side.

## What to keep in mind

- **Wallet support is required.** The connected wallet must support the STRK20
  wallet API methods, since the ZK proofs and signatures are managed wallet-side.
- **React only.** The hooks are a React convenience layer; non-React apps should
  use the [starknet.js](/starknet-wallet-api/starknet-js) route.
- **Follow the upstream docs.** For hook names, parameters, and return values, see
  the
  [Starknet Start `useStrk20` reference](https://starknet-innovation.github.io/starknet-start/docs/hooks/use-strk20/#hooks).

## Read next

- [Starknet Wallet API overview](/starknet-wallet-api/overview)
- [starknet.js](/starknet-wallet-api/starknet-js)
- [Private DeFi End to End](/starknet-wallet-api/private-defi)
- [Anonymizer Contract Anatomy](/helpers/privacy-invoke)

---

