# Register

Source: https://strk20-by-example.org/sdk/register

> Register your viewing key in the privacy pool with the builder or autoRegister

Before an account can receive private transfers it must **register**: publish
its public viewing key on-chain and store the auditor-encrypted private key.
This happens once per account per pool deployment.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

```typescript
const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers.build().register().execute({ provingBlockId })

// Submission tail (explained in Getting Started)
const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })
await provider.waitForTransaction(tx.transaction_hash)
```

## Things to notice

- You never pass the viewing key to `register()`. The builder pulls it from
  the `viewingKeyProvider` you wired into `createPrivateTransfers`.
- The viewing key must be a **`BigInt`** in the range `[1, MAX_VIEWING_KEY]`
  (half the STARK curve order, exported by the SDK). A hex string compiles
  fine but silently derives wrong channel keys - notes sent to you will never
  decrypt.
- Registering twice reverts. Check first, or use `autoRegister` below.

## `autoRegister`

Instead of registering as its own transaction, any build can bundle the
registration in automatically when the account has no viewing key on-chain
yet:

```typescript
const { callAndProof } = await transfers
  .build({ autoRegister: true })
  .with(tokenAddress, (t) => t.deposit({ amount: 100n }))
  .surplusTo(account.address)
  .execute({ provingBlockId })
```

If the account is already registered, `autoRegister` is a no-op - safe to
leave on for first-time-user flows (a claim page, an onboarding deposit).

| Approach             | When to use                                              |
| -------------------- | -------------------------------------------------------- |
| `.register()`        | Explicit onboarding step, dedicated "register" button    |
| `autoRegister: true` | Bundle registration into the user's first real operation |

Next: [Deposit](/sdk/deposit) public ERC-20 tokens into the pool.

---

