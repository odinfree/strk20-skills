# Withdraw

Source: https://strk20-by-example.org/sdk/withdraw

> Withdraw private notes back to a public Starknet address as ERC-20 tokens

A withdrawal spends private notes and sends plain ERC-20 tokens to a public
Starknet address. It is the exit door of the pool - and the one place where
an amount and a recipient become publicly visible again.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

```typescript
const { notes } = await transfers.discoverNotes({
  tokens: [BigInt(tokenAddress)],
})
const note = notes.get(BigInt(tokenAddress))![0] // e.g. a 100n note

const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers
  .build()
  .surplusTo(account.address) // 70n stays private as a change note
  .with(tokenAddress, (t) =>
    t.inputs(note).withdraw({ amount: 30n, recipient: account.address }),
  )
  .execute({ provingBlockId })

const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })
await provider.waitForTransaction(tx.transaction_hash)
```

## Things to notice

- `recipient` is the **public address** that receives the ERC-20 transfer.
  It can be anyone, not just yourself - paying a merchant directly from the
  pool is a single withdraw.
- **Note maturity applies to the inputs.** A note created fewer than 10
  blocks ago cannot be spent; the SDK will happily build the proof, but the
  transaction fails. Maturity is a client-side rule — compare `note.created`
  against the current block. Proving against
  `currentBlock - 10` guarantees every note in your registry has matured at
  the proof base.
- The change (`70n` here) stays in the pool as a fresh private note via
  `surplusTo` - withdrawing does not force you to exit a whole note.
- Privacy consideration: the contract's public `transfer` call reveals token,
  amount and recipient. What stays hidden is _which_ notes funded it. Check
  `ExecuteResult.warnings` for `USER_LINKAGE` before submitting.

Next: [Multi-Operation Batches](/sdk/multi-op-batch) - many operations and
many tokens in one transaction.

---

