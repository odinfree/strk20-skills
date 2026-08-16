# Deposit + Transfer

Source: https://strk20-by-example.org/sdk/deposit-transfer-surplus

> Deposit and transfer in one transaction, with surplusTo directing the remainder

Operations on the same token compose inside one `.with(...)` block, and the
whole batch settles atomically in one transaction. The classic case: deposit
100 and immediately transfer 60 to Bob. Omit the `recipient` on the deposit
and let `surplusTo` direct whatever is left - the SDK resolves the
intermediate steps.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started). The ERC-20 `approve` is still a
separate transaction first (see [Deposit](/sdk/deposit)).

```typescript
// Transaction 1 - approve (identical to the Deposit page).
const approveTx = await account.execute(
  {
    contractAddress: tokenAddress,
    entrypoint: "approve",
    calldata: [poolAddress, 100n.toString(), "0"],
  },
  { tip: 0n },
)
await provider.waitForTransaction(approveTx.transaction_hash)

// Transaction 2 - deposit 100, transfer 60, keep 40.
const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers
  .build({ autoSetup: true })
  .surplusTo(account.address) // the 40n remainder becomes my note
  .with(tokenAddress, (t) =>
    t.deposit({ amount: 100n }).transfer({ recipient: bob, amount: 60n }),
  )
  .execute({ provingBlockId })

const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })
await provider.waitForTransaction(tx.transaction_hash)
```

## Things to notice

- The deposit has **no `recipient`**. Its 100n enters the token's balance
  sheet for this transaction; the transfer takes 60n; `surplusTo` claims the
  remaining 40n. Pinning `recipient` on the deposit would instead lock the
  full 100n into a note and force the transfer to find other inputs.
- Bob's 60n note is spendable by Bob after 10 blocks; your 40n surplus note
  likewise. The transfer itself needs **no** maturity wait - the deposited
  funds are consumed within the same transaction, never as a note.
- Everything is atomic: if the transfer cannot be resolved, no deposit
  happens either.
- Balance-sheet rule per token: deposits + inputs must cover transfers +
  withdrawals, with `surplusTo` absorbing any remainder.

Next: [Withdraw](/sdk/withdraw) private funds back to a public address.

---

