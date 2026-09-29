# Shadow Accounts

Source: https://strk20-by-example.org/starknet-wallet-api/shadow-accounts

> Use persistent, pseudonymous per-dapp accounts through the Starknet Wallet API

A **shadow account** is a persistent, pseudonymous identity for one user and
one dapp. It lets a protocol recognize a returning user and hold positions over
time without exposing the public link to that user's main wallet.

A shadow account is not a wallet account: it has no keys and cannot sign. The
`ShadowAccountAnonymizer` deploys it lazily at a deterministic address and is
the only contract that can execute calls through it.

Requires `starknet@^10.8.0`, Wallet API `0.10.4`, and a connected wallet that
supports the STRK20 shadow-account methods.

## What is private

The link to the user's main wallet is hidden. The shadow account itself is
public: its ERC-20 balances, calls, and protocol positions are visible onchain.
Use it for **unlinkability and stable per-dapp identity**, not to hide the
contents of the account.

Each `(user, dapp_name, nonce)` tuple resolves to a different address. Keep the
`dapp_name` stable, and use another nonce when the user wants a separate
identity for the same dapp.

## Get the commitment

`WalletAccountV6` asks the wallet to derive commitments from the user's private
state. No transaction is sent and the dapp never receives the viewing key.

```typescript
// Shared by every shadow account this user derives for this dapp.
const partial = await account.strk20ShadowAccountCommitment("myDapp")

// Selects the shadow account at nonce 0.
const commitment = await account.strk20ShadowAccountCommitment("myDapp", "0x0")
```

Omitting the nonce returns the **partial commitment**. Passing `"0x0"` returns
the **full commitment for nonce 0**; the two calls are not equivalent.

## Resolve the address

Use the anonymizer's `get_shadow_accounts` view when the dapp needs an address
before invoking - for example, to fund it from the shielded balance. The view
also reports whether each address has already been deployed. This snippet
assumes `anonymizer` is a starknet.js `Contract` created with the current
`ShadowAccountAnonymizerABI`.

```typescript
import { num } from "starknet"

const shadowAccounts = await anonymizer.get_shadow_accounts(partial, 0, 5, false)

// [{ nonce, address, is_deployed }, ...]
const shadowAccountAddress = num.toHex(shadowAccounts[0].address)
```

The range is `[start, end)` and is limited to 1,024 nonces. Set the final
argument to `true` to stop at the first undeployed nonce and return only the
contiguous deployed prefix.

For offline derivation, use the Privacy SDK's `shadowAccountAddress` helper.
The current anonymizer implementation uses the fixed `PRIMER_CLASS_HASH`; do
not substitute the value returned by `get_shadow_account_class_hash`, because
that is the class installed _after_ the deterministic address is chosen.

## Invoke through the shadow account

The Wallet API action takes normal starknet.js `Call` objects. A common flow is:

1. Withdraw an input token from the shielded balance to the shadow address.
2. Create one open note for each token that should return to the pool.
3. Run the calls through `shadow_account_invoke`.

```typescript
import type { STRK20_ACTION } from "starknet"

const actions: STRK20_ACTION[] = [
  {
    type: "withdraw",
    token: STRK,
    amount: "0x4563918244f40000",
    recipient: shadowAccountAddress,
  },
  {
    type: "transfer",
    token: STRK,
    amount: "OPEN",
    recipient: userAddress,
  },
  {
    type: "shadow_account_invoke",
    dapp_name: "myDapp",
    nonce: "0x0",
    calls: [stakingContract.populate("stake", { amount: 1000n })],
    collect_policy: { type: "all" },
  },
]

const { transaction_hash } = await account.strk20InvokeTransaction(actions)
```

The exported
[`STRK20_SHADOW_ACCOUNT_INVOKE_ACTION`](https://starknet-js.com/docs/API/type-aliases/STRK20_SHADOW_ACCOUNT_INVOKE_ACTION/)
type is also available when an action is built separately.

## Collection policies

One policy applies to every open note settled by the action:

| `collect_policy`            | Amount collected from the shadow account        |
| --------------------------- | ----------------------------------------------- |
| `{ type: "all" }`           | The token's entire balance                      |
| `{ type: "diff" }`          | Only the balance gained during this interaction |
| `{ type: "exact", amount }` | Exactly `amount` in the token's smallest unit   |

## Things to notice

- `calls` must contain at least one standard starknet.js `Call`.
- The number of open notes created in the transaction must match the number
  the shadow-account call fills.
- A transaction has one invoke-phase slot. `invoke` and
  `shadow_account_invoke` are mutually exclusive in the same transaction.
- Deployment is lazy: the address can receive funds before the first
  `shadow_account_invoke` deploys it.
- Use the anonymizer address for the connected network from
  [Deployed Contract Addresses](/contract-addresses).

## Read next

- [starknet.js](/starknet-wallet-api/starknet-js)
- [Private DeFi End to End](/starknet-wallet-api/private-defi)
- [Shadow Accounts with the Privacy SDK](/sdk/shadow-accounts)
