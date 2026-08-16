# Transfer

Source: https://strk20-by-example.org/sdk/transfer

> Spend private notes and transfer an amount to a recipient, with change back to you

A private transfer spends one or more of your notes and creates a new note
for the recipient. Notes are UTXOs: consumed whole. If the inputs total more
than the transfer amount, the difference becomes a **change note** - and the
builder must be told who owns it.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

```typescript
const bob = "0x05a1..."

// Find a note to spend (see Discovering Notes).
const { notes } = await transfers.discoverNotes({
  tokens: [BigInt(tokenAddress)],
})
const note = notes.get(BigInt(tokenAddress))![0] // e.g. a 100n note

const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers
  .build({ autoSetup: true })
  .surplusTo(account.address) // 50n change comes back to me as a new note
  .with(tokenAddress, (t) => t.inputs(note).transfer({ recipient: bob, amount: 50n }))
  .execute({ provingBlockId })

const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })
await provider.waitForTransaction(tx.transaction_hash)
```

## Things to notice

- `.inputs(note)` selects exactly which notes to spend. Without it, set
  `autoSelectNotes` in `build()` and let the SDK choose.
- `surplusTo(...)` is **required whenever inputs may exceed outputs**.
  Spending a `100n` note to send `50n` without it throws
  "no surplus recipient" at `execute()` time.
- The change note belongs to whoever `surplusTo` names - and like every new
  note, it matures 10 blocks after creation. Back-to-back transfers that
  reuse change must wait out the maturity window.
- The recipient must be registered and reachable - see
  [Channels & Setup Requirements](/sdk/setup-requirements). `autoSetup: true`
  opens the channel and token subchannel if missing.

## Automatic note selection

| `autoSelectNotes` | Behavior                                                     |
| ----------------- | ------------------------------------------------------------ |
| `"naive"`         | Smallest set of notes that covers the amount                 |
| `"all"`           | Consume every note (consolidation) - always produces surplus |

```typescript
const { callAndProof } = await transfers
  .build({ autoSelectNotes: "naive", autoDiscover: { notes: "refresh" } })
  .surplusTo(account.address)
  .with(tokenAddress, (t) => t.transfer({ recipient: bob, amount: 50n }))
  .execute({ provingBlockId })
```

With `"all"`, `surplusTo` is effectively mandatory: it only avoids surplus
when the amounts match your balance exactly.

Next: [Deposit + Transfer](/sdk/deposit-transfer-surplus) in a single transaction.

---

