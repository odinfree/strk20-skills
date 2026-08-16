# Multi-Operation Batches

Source: https://strk20-by-example.org/sdk/multi-op-batch

> Chain several operations on one token and several tokens in a single transaction

One build = one transaction = one proof. Inside it you can chain any number
of operations on a token, and any number of tokens via repeated `.with(...)`
blocks. Everything settles atomically.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

## Several operations, one token

Spend a 100n note: 40n to Alice, 30n withdrawn to public, 30n change.

```typescript
const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers
  .build({ autoSetup: true })
  .surplusTo(account.address) // absorbs the 30n remainder
  .with(tokenAddress, (t) =>
    t
      .inputs(note100)
      .transfer({ recipient: alice, amount: 40n })
      .withdraw({ amount: 30n, recipient: account.address }),
  )
  .execute({ provingBlockId })

const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })
await provider.waitForTransaction(tx.transaction_hash)
```

## Several tokens, one transaction

Each token gets its own `.with(...)` block with its own inputs and outputs.
The per-token balance sheets are independent; `surplusTo` at the top level
covers all of them.

```typescript
const { callAndProof } = await transfers
  .build({ autoSetup: true, autoDiscover: { notes: "refresh" } })
  .surplusTo(account.address)
  .with(STRK, (t) => t.inputs(strkNote).transfer({ recipient: alice, amount: 40n }))
  .with(ETH, (t) =>
    t.inputs(ethNote).withdraw({ amount: 10n, recipient: account.address }),
  )
  .execute({ provingBlockId })
```

## Things to notice

- Balance-sheet rule holds **per token**: inputs + deposits must cover
  transfers + withdrawals; `surplusTo` takes each token's remainder. A
  per-token override exists too: `t.surplusTo(...)` inside the block.
- At most **one `invoke()` per transaction** - the pool contract enforces a
  single external call per `apply_actions`. The builder errors if you chain
  two.
- Larger batches mean larger proofs. Very large recipient lists can hit
  proof-size limits; wrap the batch in a try/catch and fall back to
  per-recipient transactions, waiting out the 10-block change-note maturity
  between them.
- For batches to recipients who may lack channels, do not rely on
  `autoSetup` - pre-flight each recipient instead, as shown on the next page.

Next: [Channels & Setup Requirements](/sdk/setup-requirements) - knowing what
setup a recipient needs.

---

