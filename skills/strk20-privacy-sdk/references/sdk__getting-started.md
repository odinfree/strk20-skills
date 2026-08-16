# Getting Started

Source: https://strk20-by-example.org/sdk/getting-started

> Build privacy wallets on Starknet with the low-level STRK20 SDK and createPrivateTransfers

These pages are for teams building **privacy wallets on Starknet** or advanced
integrations that manage their own account, keys, note discovery, and proving.
If you are building a private dapp on top of an existing wallet, use the
[Starknet Wallet API](/starknet-wallet-api/overview) instead - it keeps viewing
keys inside the wallet. Everything here goes through one factory:
`createPrivateTransfers`.

## Install

```shell
npm install @starkware-libs/starknet-privacy-sdk
```

The SDK requires **Node.js >= 24** (its `ohttp-ts` dependency needs modern WebCrypto).

**Getting a 404?** Known temporary issue - the package is not on npmjs.com yet
while StarkWare restores access to its npm org. Until then it is published to
[GitHub Packages](https://github.com/starkware-libs/starknet-privacy/pkgs/npm/starknet-privacy-sdk),
which needs a GitHub token even for public packages. With the
[GitHub CLI](https://cli.github.com):

```shell
gh auth refresh -h github.com -s read:packages
npm config set @starkware-libs:registry https://npm.pkg.github.com
npm config set '//npm.pkg.github.com/:_authToken' "$(gh auth token)"

npm install @starkware-libs/starknet-privacy-sdk
```

Or skip the registry entirely and install from git at a specific commit:

```shell
npm install "starkware-libs/starknet-privacy#<commit-sha>"
```

## Wire it up

The factory needs a Starknet account plus three things: a **viewing key**
(your privacy key), a **proving service** (generates validity proofs) and a
**discovery service** (finds your notes and channels). Pass the last two as
plain config objects and the SDK constructs the production providers for you.

```typescript
import { Account, RpcProvider, constants } from "starknet"
import { createPrivateTransfers } from "@starkware-libs/starknet-privacy-sdk"

const provider = new RpcProvider({ nodeUrl: process.env.RPC_URL! })

// cairoVersion "1" is required for accounts sending v3 transactions
const account = new Account({
  provider,
  address: process.env.ACCOUNT_ADDRESS!,
  signer: process.env.ACCOUNT_PRIVATE_KEY!,
  cairoVersion: "1",
})

const transfers = createPrivateTransfers({
  account,
  // The viewing key MUST be a bigint. A hex string silently misbehaves
  // downstream (wrong channel-key derivation).
  viewingKeyProvider: {
    getViewingKey: async () => BigInt(process.env.VIEWING_KEY!),
  },
  provingProvider: {
    url: process.env.PROVING_SERVICE_URL!,
    chainId: constants.StarknetChainId.SN_SEPOLIA,
  },
  discoveryProvider: { url: process.env.INDEXER_URL! },
  poolContractAddress: process.env.POOL_ADDRESS!,
})
```

If you need to configure a provider beyond what the config object exposes,
`ProvingServiceProofProvider` and `IndexerDiscoveryProvider` are both exported
from the package root and can be passed as instances instead — see
[Discovery Providers](/sdk/discovery-providers).

On Sepolia, `POOL_ADDRESS` is the privacy pool (v2.0) deployed at
[`0x0254a6b2997ef52e9f830ce1f543f6b29768295e8d17e2267d672c552cfe0d91`](https://sepolia.voyager.online/contract/0x0254a6b2997ef52e9f830ce1f543f6b29768295e8d17e2267d672c552cfe0d91).

## Going deeper

The SDK is open source (Apache 2.0):
[starkware-libs/starknet-privacy](https://github.com/starkware-libs/starknet-privacy).
Its [`sdk/README.md`](https://github.com/starkware-libs/starknet-privacy/blob/main/sdk/README.md)
covers material these pages do not — transaction sequencing against finalized
state, the `Open` note API, and `classifyTransaction` for reading history.

## Your first transaction

Every operation follows the same shape: `build()` a batch of operations, then
`execute()` it and submit the resulting call.

```typescript
// Prove against a slightly older block: notes mature 10 blocks after
// creation, and proving at the chain head risks reorg invalidation.
const provingBlockId = (await provider.getBlockNumber()) - 10

const { callAndProof } = await transfers.build().register().execute({ provingBlockId })

// Omit proof keys entirely when there are no proof facts - passing
// empty arrays serializes an invalid v3 transaction.
const proofDetails = callAndProof.proof.proofFacts?.length
  ? { proofFacts: callAndProof.proof.proofFacts, proof: callAndProof.proof.data }
  : {}

// tip is mandatory for v3 transactions in starknet.js
const tx = await account.execute(callAndProof.call, { tip: 0n, ...proofDetails })

await provider.waitForTransaction(tx.transaction_hash)
console.log(`registered in tx ${tx.transaction_hash}`)
```

This submission tail - back off `provingBlockId`, conditionally spread
`proofDetails`, pass `tip: 0n`, wait - is identical for every operation in the
following pages. We will not repeat the explanation, just the code.

## What each provider does

| Provider             | Role                                                                                                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `viewingKeyProvider` | Supplies the private viewing key `k` used to decrypt notes and derive nullifiers                                                 |
| `provingProvider`    | Sends your signed invocation to a proving service, which executes it in a virtual Starknet environment and returns a STARK proof |
| `discoveryProvider`  | Scans your channels for incoming notes. Backed by `IndexerDiscoveryProvider` (HTTP discovery service)                            |

Next: register your viewing key so you can receive private transfers.

---

