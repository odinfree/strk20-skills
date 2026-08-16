# Proving Configuration

Source: https://strk20-by-example.org/sdk/proving-config

> Configure ProvingServiceProofProvider, pick provingBlockId, and submit proofs correctly

The proving provider sends your signed invocation to a proving service,
which executes it in a virtual Starknet environment and returns a STARK
proof. Three small conventions around it account for most submission
failures.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

```typescript
import { constants } from "starknet"
import { ProvingServiceProofProvider } from "@starkware-libs/starknet-privacy-sdk"

const provingProvider = new ProvingServiceProofProvider(
  process.env.PROVING_SERVICE_URL!,
  constants.StarknetChainId.SN_SEPOLIA,
)
```

## `provingBlockId` - always `currentBlock - 10`

```typescript
const provingBlockId = (await provider.getBlockNumber()) - 10
const result = await transfers.build()./* ... */.execute({ provingBlockId })
```

The proof is generated against the state at `provingBlockId`. Three reasons to
back off from the head:

1. **Note maturity** - notes mature 10 blocks after creation. Proving at
   `currentBlock - 10` guarantees every unspent note in your registry has
   matured at the proof base.
2. **Reorg buffer** - a proof based on the chain head can be invalidated by
   an L2 reorg before the transaction lands. The contract allows proofs up to
   `proof_validity_blocks` old (default 450, ~15 min at 2s/block; it is
   governance-settable), so ten blocks back is a comfortable, still-fresh
   margin.
3. **Consistent state** - the SDK forwards `provingBlockId` to `discoverNotes`
   and `discoverChannels`, so discovery and proving see the same block. Without
   it the two can disagree, and a note selected from a newer state can fail to
   prove.

Omitting it works _most_ of the time - with intermittent failures on
insufficiently mature notes and worse proving-service cache hits. Just always
pass it. And when
chaining transactions (approve then deposit), re-fetch it after each
`waitForTransaction`.

## `proofDetails` - conditional, never empty

```typescript
const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })
```

Some providers (the mock/no-validate ones used in development) return empty
proof facts. Passing `proofFacts: []` through to `account.execute` makes
starknet.js serialize an invalid v3 transaction - the keys must be **omitted
entirely**, hence the conditional spread. `tip: 0n` is mandatory for v3
transactions; forgetting it fails with the cryptic
`Cannot mix BigInt and other types`.

## Retry hygiene: `invalidateProofNonceCache()`

The proving provider caches the pool nonce. After any failed submission -
a revert, `INVALID_NONCE`, `Replacement transaction underpriced` - the cache
is stale, and retrying loops on proofs the chain keeps rejecting:

```typescript
transfers.invalidateProofNonceCache()
// ...then rebuild and resubmit
```

## Deposits are screened on every proving route

A custom or self-hosted proving backend can prove every pool action, but a
deposit is only accepted with a screening signature: FPI screens the
depositing address and signs the deposit, and the pool verifies that
signature onchain. Self-hosting is not a route around screening.

Teams running their own prover typically shield through a privacy-enabled
wallet (Ready or Xverse) and then transfer privately to the account their
integration controls. If your production flow needs direct deposits, raise it
in the [Cairo CoreStars Telegram](https://t.me/sncorestars).

## Common failures

| Symptom                                | Cause                           | Fix                                 |
| -------------------------------------- | ------------------------------- | ----------------------------------- |
| Spend fails on a recently created note | `provingBlockId` not backed off | Use `currentBlock - 10`             |
| `Cannot mix BigInt and other types`    | Missing `tip`                   | Add `tip: 0n`                       |
| Revert with `INVALID_PROOF_FACTS`      | Passed `proofFacts: []`         | Conditional spread                  |
| `INVALID_NONCE` on retry               | Stale cached pool nonce         | `invalidateProofNonceCache()` first |

This is the last page of the series - head back to
[Getting Started](/sdk/getting-started) to revisit the wiring.

---

