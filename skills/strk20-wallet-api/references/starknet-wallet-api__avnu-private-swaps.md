# AVNU Private Swaps

Source: https://strk20-by-example.org/starknet-wallet-api/avnu-private-swaps

> Add private swaps to a dapp with the AVNU SDK, without writing or deploying an anonymizer contract

Most private DeFi needs an app-specific
[anonymizer contract](/helpers/privacy-invoke). Swapping is the exception:
[AVNU](https://docs.avnu.fi/docs/privacy) has deployed its own executor, so a
dapp can offer private swaps with **no Cairo to write, review, or audit**.

## Install

```shell
npm install @avnu/avnu-sdk@^4.2.0 starknet@^10.4.0
```

## What you need

- A STRK20-capable wallet (Wallet API `>= 0.10.3`).
- The sell token **already shielded** — the swap moves value inside the pool, so
  it cannot shield for you.

## The call

```ts
import {
  createStrk20WalletProver,
  executePrivateSwap,
  PRIVACY_POOL_ADDRESS,
} from "@avnu/avnu-sdk"

const prover = createStrk20WalletProver(walletAccount)

const { transactionHash } = await executePrivateSwap({
  quote, // from AVNU's quote endpoint
  slippage: 0.01, // 1%
  takerAddress: walletAccount.address,
  poolAddress: PRIVACY_POOL_ADDRESS,
  feeMode: { poolFeeToken: quote.sellTokenAddress }, // tip?: "slow" | "normal" | "fast", defaults to "normal"
  prover,
})
```

`PRIVACY_POOL_ADDRESS` targets **mainnet**; for Sepolia testing, AVNU also
exports `SEPOLIA_PRIVACY_POOL_ADDRESS`.

AVNU's paymaster relays the transaction, so the submitting address is not the
user's.

If a paymaster API key is required (the `sponsored_private` fee mode), keep
that call server-side — passing the key from a browser leaks it. Browser
dapps should split the flow instead: call `buildPrivateSwapFee` and
`submitPrivateSwap` from a server endpoint, and run only the `prover` step
client-side with the user's wallet.

## When to use a helper instead

Reach for your own anonymizer contract when the action is not a swap — lending,
staking, or any app-specific flow. Those still need the pattern in
[Private DeFi End to End](/starknet-wallet-api/private-defi).

## Read next

- [Private DeFi End to End](/starknet-wallet-api/private-defi)
- [Swap Helper](/helpers/swap-helper) - the do-it-yourself route

---

