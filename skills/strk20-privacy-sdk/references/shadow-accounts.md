# Shadow Accounts

Source: https://strk20-by-example.org/sdk/shadow-accounts

> Build and invoke deterministic per-dapp shadow accounts with the Starknet Privacy SDK

Shadow accounts give one user a persistent, pseudonymous identity for one
dapp. They are useful for positions that live across transactions - staking,
lending, rewards, and any protocol that needs to recognize a returning caller.

This page follows Privacy SDK `0.14.3-rc.8`. The old `subaccounts(...)` API was
renamed and is not compatible with the current anonymizer. Use
`shadowAccounts(...)` throughout.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

## Configure the anonymizer

Pass the deployment for the connected network when creating `transfers`:

```typescript
const transfers = createPrivateTransfers({
  account,
  viewingKeyProvider,
  provingProvider,
  discoveryProvider,
  poolContractAddress: process.env.POOL_ADDRESS!,
  shadowAccountAnonymizerAddress: process.env.SHADOW_ACCOUNT_ANONYMIZER_ADDRESS!,
})
```

Calling `shadowAccounts(...)` without `shadowAccountAnonymizerAddress` throws.
Use the current Mainnet or Sepolia value from
[Deployed Contract Addresses](/contract-addresses).

## Commitments and addresses

The builder derives the partial and full commitments locally from the user,
viewing key, anonymizer, dapp name, and nonce:

```typescript
import { shadowAccountAddress } from "@starkware-libs/starknet-privacy-sdk"

const shadow = transfers.build().shadowAccounts("myDapp")
const partial = await shadow.partialCommitment()
const commitment = await shadow.commitment(0n)

const address = shadowAccountAddress(
  commitment,
  BigInt(process.env.SHADOW_ACCOUNT_ANONYMIZER_ADDRESS!),
)
```

`shadowAccountAddress` uses the exported, fixed `PRIMER_CLASS_HASH`, matching
the current Cairo deployment pattern. It works before the account is deployed
and does not require an RPC call. The package also exports the lower-level
`shadowAccountPartialCommitment` and `shadowAccountCommitment` helpers when you
already hold the raw felts.

## Invoke through the shadow account

Fund the shadow address, create an open note for each expected output token,
then queue the calls. The SDK translates this into one `ComputeAndInvoke`
against the `ShadowAccountAnonymizer`.

```typescript
import { Open } from "@starkware-libs/starknet-privacy-sdk"

const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers
  .build({ autoDiscover: { notes: "refresh" } })
  .with(STRK)
  .withdraw({ recipient: address, amount: 5n * 10n ** 18n })
  .surplusTo(account.address, false)
  .with(STRK)
  .transfer({ recipient: account.address, amount: Open })
  .done()
  .shadowAccounts("myDapp")
  .invoke(0n, {
    calls: [stakingContract.populate("stake", { amount: 1000n })],
    collectPolicy: { type: "all" },
  })
  .execute({ provingBlockId })

// Submit callAndProof with the usual proofDetails + tip: 0n tail.
```

`collectPolicy` is optional in the SDK and defaults to `{ type: "all" }`.

| `collectPolicy`             | Amount collected into each open note            |
| --------------------------- | ----------------------------------------------- |
| `{ type: "all" }`           | The token's entire shadow-account balance       |
| `{ type: "diff" }`          | Only the balance gained during this interaction |
| `{ type: "exact", amount }` | Exactly `amount`                                |

## Read deployed and undeployed accounts

The exported `ShadowAccountAnonymizerABI` includes these views:

- `get_shadow_accounts(partial, start, end, until_undeployed)` resolves a nonce
  range and returns `{ nonce, address, is_deployed }` for each entry.
- `get_shadow_account(commitment)` returns the stored address of an already
  deployed account, or zero when it has not been deployed.
- `get_shadow_account_class_hash()` returns the class installed after the
  primer deployment. It is not the class hash used for address derivation.

The scan range is limited to 1,024 nonces. With `until_undeployed: true`, the
range stops at the first address that has not been deployed.

## Things to notice

- A shadow account's balances, calls, and positions are public. Privacy comes
  from hiding the link to the user's main account.
- A shadow account has no keys. Only the anonymizer can execute through it.
- One transaction can contain at most one invoke-phase action, whether it is a
  normal `invoke` or a shadow-account invocation.
- One collection policy applies to every open note settled by the invocation.
- The current anonymizer returns the shadow-account address used by deposits so
  the pool can apply its screening policy to that address.

Next: [Proving Configuration](/sdk/proving-config) - prepare and submit the
resulting call safely.
