---
name: strk20-privacy-sdk
description: "Build privacy wallets and key-holding backends with the Starknet Privacy SDK (@starkware-libs/starknet-privacy-sdk). Covers createPrivateTransfers wiring, register, deposit, transfer, withdraw, multi-op batches, shadow accounts (formerly private sub-accounts), note discovery, setup requirements, and proving configuration. Also use for debugging SDK submissions: provingBlockId, proofFacts, tip 0n, INVALID_NONCE, note maturity, fresh-account sequencing, and AddressMap lookups. If the app talks to the user's wallet instead of holding keys, use strk20-wallet-api. For concepts use strk20-privacy."
---

# STRK20 Privacy SDK: wallets and key-holding backends

The low-level route for teams building the wallet itself, or backends that
manage their own account, viewing key, note discovery, and proving. If you are
building a dapp on top of existing wallets, stop here and use
`strk20-wallet-api`, which keeps viewing keys inside the wallet.

The SDK is TypeScript. A Python or Rust backend that wants STRK20 runs a
Node (>= 24) sidecar service around it (per the official agent-skill repo).
Full doc pages sit in `references/`.

## Install

```sh
npm install @starkware-libs/starknet-privacy-sdk
```

Node.js **>= 24** required (`ohttp-ts` needs modern WebCrypto). If npm returns
404 (a known temporary issue while Starkware restores its npm org), install
from GitHub Packages, which needs a GitHub token even for public packages:

```sh
gh auth refresh -h github.com -s read:packages
export NODE_AUTH_TOKEN="$(gh auth token)"
npm config set @starkware-libs:registry https://npm.pkg.github.com --location=project
npm config set '//npm.pkg.github.com/:_authToken' '${NODE_AUTH_TOKEN}' --location=project
npm install @starkware-libs/starknet-privacy-sdk
unset NODE_AUTH_TOKEN
```

The project `.npmrc` stores an environment-variable placeholder, not the token.
Do not replace it with token text or commit a file containing credentials. Or
pin a commit: `npm install "starkware-libs/starknet-privacy#<commit-sha>"`.
The monorepo's `sdk/README.md` covers what the docs pages don't: transaction
sequencing against finalized state, the `Open` note API, `pre_confirmed`
reads, and `classifyTransaction` for history. A copy sits in
`references/starknet-privacy-sdk-README.md`.

## Wiring

```typescript
import { Account, RpcProvider, constants } from "starknet"
import { createPrivateTransfers } from "@starkware-libs/starknet-privacy-sdk"

const provider = new RpcProvider({ nodeUrl: process.env.RPC_URL! })
const account = new Account({
  provider,
  address: process.env.ACCOUNT_ADDRESS!,
  signer: process.env.ACCOUNT_PRIVATE_KEY!,
  cairoVersion: "1", // required for accounts sending v3 transactions
})

const transfers = createPrivateTransfers({
  account,
  // MUST be a bigint. A hex string silently derives wrong channel keys,
  // and notes sent to you will never decrypt.
  viewingKeyProvider: { getViewingKey: async () => BigInt(process.env.VIEWING_KEY!) },
  provingProvider: { url: process.env.PROVING_SERVICE_URL!, chainId: constants.StarknetChainId.SN_SEPOLIA },
  discoveryProvider: { url: process.env.INDEXER_URL! },
  poolContractAddress: process.env.POOL_ADDRESS!,
})
```

Sepolia pool (v2.0):
`0x0254a6b2997ef52e9f830ce1f543f6b29768295e8d17e2267d672c552cfe0d91`.
Viewing key range: `[1, MAX_VIEWING_KEY]` (half the STARK curve order, exported
by the SDK). Keys and secrets stay in env vars, never in files.

## The submission tail (identical for every operation)

```typescript
// Prove against an older block. Inputs and prior transparent state must
// already exist at this base, and proving at the chain head risks reorgs.
const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers.build()/* ...ops... */.execute({ provingBlockId })

// Omit proof keys entirely when there are no proof facts. Passing
// empty arrays serializes an invalid v3 transaction.
const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}

// tip is mandatory for v3 transactions in starknet.js
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })
await provider.waitForTransaction(tx.transaction_hash)
```

Always pass `provingBlockId = currentBlock - 10`. It buffers L2 reorgs (the
contract accepts proofs up to `proof_validity_blocks` old, default 450 ≈ 15
min, governance-set) and keeps discovery and proving on the same state. The
chosen base must already include every note and transparent state change the
proof reads. Re-fetch it after every `waitForTransaction` when chaining
transactions.

**The transparent-state rule (per the SDK README):** any onchain state the
pool proof reads, including the account's viewing key, depositor token balance,
allowance, and nullifier set, must exist at the chosen proof base. With
`provingBlockId = head - 10`, poll until `head - 10 > receiptBlock` for each
prior state-changing transaction. The prover reads finalized state, never
`pre_confirmed`. Concretely:

- `register()` fails right after the account's deploy-account transaction.
  Wait until the chosen base is later than the deploy receipt block.
- `deposit()` fails when the chosen base predates the ERC-20 funding transfer
  or approval. Wait until the base is later than both receipt blocks, then
  rebuild.
- A prior private transaction's block must be included in the finalized base
  before you can prove the next transaction against its notes.

The bundled `sdk__deposit.md` page re-fetches `provingBlockId` immediately
after the approval. Do not copy that timing literally. Apply the receipt-block
condition above so the selected base includes the approval.

## Operations map

- **register()**: once per account per pool deployment. It publishes the
  public viewing key and stores the auditor-encrypted private key.
  Registering twice reverts. `build({ autoRegister: true })` bundles
  registration into any first operation and no-ops if already registered.
- **deposit**: TWO transactions, never one. The ERC-20 `approve` of the pool
  must land first, because `apply_actions` is reentrancy-guarded against
  sharing a transaction. Then `.with(token, t => t.deposit({ amount }))` with
  `surplusTo(me)`. `autoSetup: true` opens the self-channel and token
  subchannel a first deposit needs.
- **transfer**: `.inputs(note)` picks notes, or `autoSelectNotes: "naive"`
  (smallest covering set) or `"all"` (consolidation). `surplusTo(...)` is
  REQUIRED whenever inputs may exceed outputs, else `execute()` throws
  "no surplus recipient". Change notes mature 10 blocks before reuse.
- **deposit + transfer**: compose in one `.with()` block. Omit `recipient` on
  the deposit and let `surplusTo` take the remainder. Same-transaction
  consumption of the deposit needs no maturity wait.
- **withdraw**: the exit door. `recipient` is a public address, so paying a
  merchant straight from the pool is one withdraw. Token, amount, and
  recipient become public. Which notes funded it stays hidden. Check
  `ExecuteResult.warnings` for `USER_LINKAGE` before submitting.
- **multi-op / multi-token**: chain ops per `.with()` and repeat `.with()`
  per token. Per-token balance sheets, one atomic transaction, at most one
  `invoke()` per transaction. Very large recipient lists can hit proof-size
  limits, so fall back to per-recipient transactions, waiting out change-note
  maturity between them.
- **shadow accounts**, called sub-accounts in RC.4: SDK `0.14.3-rc.5` uses
  `transfers.build().shadowAccounts(dappName).invoke(...)`, the
  `shadowAccountAnonymizerAddress` config field, and the
  `shadow_account_anonymizer` Cairo package. Do not mix the RC.4 and RC.5
  names. RC.5 renamed the views and deployment event, which changed their
  selectors and keys. It requires the upgraded anonymizer. Indexers reading
  across the upgrade must match both the historical `SubAccountDeployed` and
  current `ShadowAccountDeployed` keys. Treat this release candidate as an API
  for teams that control their own accounts and can confirm its current audit
  readiness.

## Setup requirements before transferring

`transfers.discoverRequirement(recipientHex, BigInt(token))` returns
`Register` (a hard stop, only the recipient can publish their viewing key),
`SetupChannel` (fix: `builder.setup(recipient)`), `SetupToken` (fix:
`t.setup(recipient)` inside the token block), or `Ready`. The caller must
itself be registered or it throws with an unhelpful message. Match on
`"not registered"` or `"viewing key"` substrings to distinguish it from RPC
errors. `autoSetup` is fine for single-recipient flows. For batches,
pre-flight each recipient explicitly, because `autoSetup` decides from the
local registry and stale data re-opens already-open channels, which fails
onchain.

## Discovery

`discoverNotes({ tokens: [BigInt(addr)] })` is a query, not a transaction.
Results come as `AddressMap` keyed by **bigint**. `notes.get(tokenAddress)`
with a string never matches, so use `notes.get(BigInt(tokenAddress))`. Notes
are visible on acceptance but spendable only 10 blocks after creation
(`note.created` vs current block, a client-side rule).

The registry is a within-session optimization. Every `execute()` returns an
updated `PrivateRegistry` (the same object mutated in place, unless you pass
`registryConst: true`). Pass it into the next `build({ registry })` with
`autoDiscover: { notes: "missing" }` (`"refresh"` re-scans, `"all"` rebuilds).
Treat it as ephemeral: rebuild from discovery at session start, and move to
persisted cursors only once note counts reach the thousands (per the SDK
README).

Providers: `IndexerDiscoveryProvider` is the production backend, with
server-side pagination and reorg repair. `ContractDiscoveryProvider` exists in
source but is NOT exported from the published package yet. Import providers
from the package root, since deep paths fail with
`ERR_PACKAGE_PATH_NOT_EXPORTED`. Discovery and proving requests carry
viewing-key material, so in production enable OHTTP (`{ ohttp: true }`), pin
`publicKeyConfig` (the default key fetch is trust-on-first-use), use HTTPS,
and consider an OHTTP relay to hide client IPs. The discovery service still
processes the decrypted request content (per the SDK README).

## Screening and self-hosted proving

Any prover can prove any pool action, but a deposit is only accepted with
FPI's screening signature, verified onchain (protocol-level since v0.14.3).
Teams running their own prover typically shield through a privacy-enabled
wallet (Ready or Xverse) and privately transfer to the account their
integration controls. Direct-deposit needs go to the Cairo CoreStars
Telegram (t.me/sncorestars).

## Common failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `register()` fails on a fresh account | Chosen base predates the deploy | Wait until `head - 10 > deployReceiptBlock` |
| Deposit fails right after funding or approval | Chosen base predates the funding or approval | Wait until `head - 10` is later than both receipt blocks, then check screening |
| Spend fails on a recently created note | Note is immature or absent at the chosen base | Wait until the note is at least 10 blocks old and visible at that base |
| `Cannot mix BigInt and other types` | Missing `tip` | Add `tip: 0n` |
| Revert with `INVALID_PROOF_FACTS` | Passed `proofFacts: []` | Conditional spread |
| `INVALID_NONCE` on retry | Stale cached pool nonce | `transfers.invalidateProofNonceCache()` first |
| Recipient's notes never decrypt | Viewing key passed as hex string | `BigInt(...)`, range `[1, MAX_VIEWING_KEY]` |
| `notes.get(token)` returns undefined | String key on `AddressMap` | Key by `BigInt(token)` |
| `shadowAccounts(...)` throws | `shadowAccountAnonymizerAddress` missing from config | Add it to `createPrivateTransfers` |
| Mature-looking deposit still reverts | Screening signature missing or failed | Check the FPI screening path |

## references/

- `sdk__getting-started.md`, install, wiring, first transaction
- `sdk__register.md`, register plus autoRegister
- `sdk__deposit.md`, two-transaction rule, maturity, screening
- `sdk__transfer.md`, inputs, surplusTo, autoSelectNotes
- `sdk__deposit-transfer-surplus.md`, composing ops
- `sdk__withdraw.md`, exits, USER_LINKAGE
- `sdk__multi-op-batch.md`, batches, limits
- `sdk__setup-requirements.md`, discoverRequirement flow
- `sdk__note-discovery.md`, discoverNotes, AddressMap, registry
- `sdk__discovery-providers.md`, Indexer vs Contract provider status
- `sdk__proving-config.md`, provingBlockId, proofDetails, retries
- `starknet-privacy-sdk-README.md`, upstream monorepo SDK README

Snapshot 2026-08-16. Package status, exports, and addresses move. Verify
against https://strk20-by-example.org and `starkware-libs/starknet-privacy`
before relying on them.
