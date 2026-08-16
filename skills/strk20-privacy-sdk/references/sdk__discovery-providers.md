# Discovery Providers

Source: https://strk20-by-example.org/sdk/discovery-providers

> IndexerDiscoveryProvider is the discovery backend the SDK exports; ContractDiscoveryProvider exists in source but is not yet reachable

Everything on the previous page - `discoverNotes`, `discoverChannels`,
`discoverRequirement`, the `autoDiscover` options - is served by the
`discoveryProvider` you wired into `createPrivateTransfers`. The SDK source
contains two implementations, but only one is currently reachable from the
published package.

| Provider                    | Backend                        | Use for                                                         |
| --------------------------- | ------------------------------ | --------------------------------------------------------------- |
| `IndexerDiscoveryProvider`  | Discovery service over HTTP    | Production - pagination and reorg detection handled server-side |
| `ContractDiscoveryProvider` | Pool contract via Starknet RPC | Not yet exported from the published package - see below         |

## IndexerDiscoveryProvider

The default. Passing a config object to `createPrivateTransfers` constructs one
for you:

```typescript
discoveryProvider: {
  url: process.env.INDEXER_URL!
}
```

Construct it directly only when you need constructor options the config object
does not expose — for example OHTTP envelope encryption:

```typescript
import { IndexerDiscoveryProvider } from "@starkware-libs/starknet-privacy-sdk"

const discoveryProvider = new IndexerDiscoveryProvider(
  process.env.INDEXER_URL!,
  process.env.POOL_ADDRESS!, // hex string, like everywhere else
  { ohttp: true },
)
```

Import it from the package root. Deep paths into `dist/internal/` are blocked by
the package's `exports` map and fail at runtime with
`ERR_PACKAGE_PATH_NOT_EXPORTED`.

## ContractDiscoveryProvider

Replays pool events by querying the contract over RPC, with no indexer to run.
It exists in the SDK source but is **not currently reachable from the published
package** — it is not exported from the package root, and the `exports` map
blocks every deep path, so `import { ContractDiscoveryProvider } from
"@starkware-libs/starknet-privacy-sdk"` fails with
`TS2305: has no exported member`.

Until it is exported, use `IndexerDiscoveryProvider` against a development
indexer. Track
[starkware-libs/starknet-privacy](https://github.com/starkware-libs/starknet-privacy)
for the export.

## Things to notice

- Reorg handling: the indexer detects L2 reorgs and repairs its cursor
  automatically. You do not need to write reorg-handling logic against
  `IndexerDiscoveryProvider`.
- Discovery cost does not grow with pool history from your app's
  perspective - the indexer scans the pool once, server-side, for every
  consumer.

Next: [Proving Configuration](/sdk/proving-config) - the proving side of the
same wiring.

---

