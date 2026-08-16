# Private DeFi End to End

Source: https://strk20-by-example.org/starknet-wallet-api/private-defi

> Connect an anonymizer contract to a dapp through the Starknet Wallet API using open notes and calldata placeholders

The [anonymizer contract pages](/helpers/privacy-invoke) cover the Cairo side.
This page covers the other half: how a dapp actually reaches that contract
through the [Starknet Wallet API](/starknet-wallet-api/overview), without ever
touching a viewing key.

Requires `starknet@^10.4.0` and a wallet supporting Wallet API `0.10.3`.

## The two actions

A private DeFi call is **one** STRK20 transaction carrying two actions:

1. A `transfer` with the literal amount `"OPEN"` — this creates an **open note**,
   the slot your helper's output gets credited into. Its amount is only known
   after the helper runs on-chain.
2. An `invoke` naming your helper contract and its calldata.

The wallet resolves two placeholders inside the invoke calldata:

| Placeholder         | Resolves to                                     |
| ------------------- | ----------------------------------------------- |
| `${openNoteIds[N]}` | The id of the Nth open note in this transaction |
| `${poolAddress}`    | The privacy pool contract address               |

That indirection is what lets you reference a note that does not exist yet at
the time you build the calldata.

## A private swap

```ts
import type { STRK20_ACTION } from "@starknet-io/types-js"

const actions: STRK20_ACTION[] = [
  // 1. Open the note the swap output will be credited into.
  { type: "transfer", token: tokenOut, amount: "OPEN", recipient: userAddress },

  // 2. Call the helper. ${openNoteIds[0]} is the note opened above.
  {
    type: "invoke",
    contract: swapHelperAddress,
    calldata: [tokenIn, tokenOut, amountIn, "${openNoteIds[0]}"],
  },
]

const { transaction_hash } = await account.strk20InvokeTransaction(actions)
```

The pool withdraws `amountIn` to your helper, calls its `privacy_invoke`
entry point, and credits the returned `OpenNoteDeposit` into the open note —
atomically. Observers see pool → helper → AMM → helper. They do not see who
initiated it.

Match the calldata order to your helper's `privacy_invoke` signature; the pool
deserializes it directly into that function's parameters.

## Dry-run first

`strk20PrepareInvoke` builds and proves the same actions without submitting,
which is the cheapest way to catch a calldata-shape mistake:

```ts
const prepared = await account.strk20PrepareInvoke(actions, true) // simulate
```

## Show the shielded balance

Reading private balances is a wallet call too — no viewing key in your app:

```ts
const balances = await account.strk20Balances([tokenIn, tokenOut])
// [{ token, balance }, ...]
```

## What stays public

The helper's on-chain action and the amounts it moves are visible; the link back
to the user is not. Open-note amounts are plaintext by design — they are
measured at execution time. Deposits and withdrawals remain public legs.

## Read next

- [Anonymizer Contract Anatomy](/helpers/privacy-invoke)
- [Swap Helper](/helpers/swap-helper)
- [AVNU Private Swaps](/starknet-wallet-api/avnu-private-swaps) - swaps without writing a helper at all

---

