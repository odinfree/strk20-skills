# Channels & Setup Requirements

Source: https://strk20-by-example.org/sdk/setup-requirements

> Check what setup a recipient needs with discoverRequirement and open channels explicitly

Notes travel over **channels**. Before you can transfer token X to Bob, three
things must exist: Bob's registration, a channel from you to Bob, and a
subchannel for token X inside that channel. `discoverRequirement` tells you
which of these is still missing.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

```typescript
import { SetupRequirement } from "@starkware-libs/starknet-privacy-sdk"

// recipient is a hex string; token must be a bigint.
const requirement = await transfers.discoverRequirement(bob, BigInt(tokenAddress))
```

| `SetupRequirement` | Meaning                                          | Fix                                            |
| ------------------ | ------------------------------------------------ | ---------------------------------------------- |
| `Register`         | Recipient has no viewing key on-chain            | They must register - you cannot do it for them |
| `SetupChannel`     | No channel from you to the recipient             | `builder.setup(recipient)`                     |
| `SetupToken`       | Channel exists, this token's subchannel does not | `t.setup(recipient)`                           |
| `Ready`            | Transfer will go through                         | Nothing                                        |

## Opening channels explicitly

`setup()` on the **main builder** opens the channel; `setup()` on the
**token builder** opens the token subchannel. Bundle them with the transfer
they unblock:

```typescript
const provingBlockId = (await provider.getBlockNumber()) - 10
const builder = transfers.build({ autoDiscover: { notes: "refresh" } })
builder.surplusTo(account.address)

if (requirement === SetupRequirement.SetupChannel) {
  builder.setup(bob) // channel
  builder.with(tokenAddress, (t) => t.setup(bob)) // + token subchannel
} else if (requirement === SetupRequirement.SetupToken) {
  builder.with(tokenAddress, (t) => t.setup(bob)) // subchannel only
}

builder.with(tokenAddress, (t) => t.transfer({ recipient: bob, amount: 50n }))
const { callAndProof } = await builder.execute({ provingBlockId })
// ... submission tail as usual
```

## `autoSetup`

`build({ autoSetup: true })` adds the missing setup actions automatically -
convenient for single-recipient flows. For batches, prefer the explicit
pattern above: `autoSetup` decides from the **local registry**, and stale
registry data makes it re-open already-open channels, which fails on-chain.

## Things to notice

- **The caller must be registered** before calling `discoverRequirement` -
  it derives your channel keys from your on-chain viewing key. If you are
  not registered it throws, with an unhelpful message; match on
  `"not registered"` / `"viewing key"` substrings to distinguish it from
  RPC errors.
- `SetupRequirement.Register` is a hard stop: only the recipient can publish
  their own viewing key. Show "ask them to register" UX.
- Opening a channel is a proved pool action like any other - it rides the
  same build/execute/submit cycle, alone or alongside transfers.

Next: [Discovering Notes](/sdk/note-discovery) - reading your private balance.

---

