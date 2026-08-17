---
name: strk20-wallet-api
description: Build private dapps on Starknet through the Starknet Wallet API. Covers shield/unshield, private transfers, shielded balances, private DeFi calls, and AVNU private swaps from TypeScript or React. Use whenever an app asks the user's privacy-enabled wallet to perform STRK20 actions (starknet.js WalletAccountV6, useStrk20 hooks, strk20InvokeTransaction, STRK20_ACTION, open notes, openNoteIds placeholders). For the Cairo helper side use strk20-anonymizer-contracts, for wallets or backends holding their own keys use strk20-privacy-sdk, for concepts and route choice use strk20-privacy.
---

# STRK20 Wallet API: private dapps

The recommended route for most private dapps. The dapp asks the user's
privacy-enabled wallet to act, and the wallet handles viewing keys, note
discovery, proving, and submission. Your app never sees private state. Never
ask a user for their viewing key.

Full doc pages sit in `references/`. The snippets below are the load-bearing
parts.

## Version baseline. Verify before installing

- STRK20 support landed in starknet.js 10.4.0. A bare `npm install starknet`
  resolves to the `latest` line, which was 10.0.2 on 2026-08-16 and lacks
  `WalletAccountV6`, `strk20InvokeTransaction`, and `STRK20_ACTION`.
- Existing repo on starknet.js v5, v6, or v7? The jump to 10.4.0 is a breaking
  migration, plan it as its own task before wiring STRK20.
- The connected wallet must support Wallet API `>= 0.10.3` (types from
  `@starknet-io/types-js` 0.10.3).
- The official integration skill tested an exact stack: `starknet@10.4.0`,
  `@starknet-io/get-starknet-discovery@6.0.3`,
  `@starknet-io/get-starknet-wallet-standard@6.0.3`, and
  `@starknet-io/types-js@0.10.3`.
- The npm `next` tags had advanced to starknet.js 10.7.0 and get-starknet
  6.0.4 on 2026-08-16. Do not combine a floating `starknet@^10.4.0` with
  stale hard pins. Either use the tested exact stack or update the connection
  packages together and rerun the WalletAccount guide and wallet tests.
- Wrapper layers: Starkzap's docs do not list STRK20 support, and
  starknet-react or starknetkit may lag starknet.js 10.4.0. Verify current
  compatibility on npm before promising a drop-in. Either way the plug-in
  point is the starknet.js `WalletAccountV6` level (per the official
  agent-skill repo).

## Two ways in

- React dapps: the `useStrk20` hooks from Starknet Start, a convenience
  wrapper that calls a `WalletAccountV6` under the hood.
- Everything else, or when you need finer control over connection and proof
  handling: `WalletAccountV6` directly, connected via get-starknet v6.

## Detect capability with a version query, never a data call

```ts
const versions = await walletV6.supportedWalletApi(wallet)
const supported = versions.some((v) => compareVersions(v, "0.10.3") >= 0)
```

Do not probe `strk20Balances` to feature-detect. It is a balance-reading
method, so wallets gate it behind a user consent prompt for data the app has
no reason to see.

Import the connected-wallet type from its exported feature subpath. Importing
it from the package root fails with TS2459:

```ts
import type { WalletWithStarknetFeatures } from "@starknet-io/get-starknet-wallet-standard/features"
```

## The actions

Build a `STRK20_ACTION[]` and hand it to the wallet:

```ts
// Shield (deposit into the pool)
const actions: STRK20_ACTION[] = [{ type: "deposit", token: tokenAddress, amount }]

// Private transfer. No contract call, no event, no approval step.
const actions: STRK20_ACTION[] = [
  { type: "transfer", token: strkAddress, amount, recipient },
]

const { transaction_hash } = await account.strk20InvokeTransaction(actions)
```

Two submission details prevent silent UI failures:

- Bound `waitForTransaction` with an application timeout. Paymaster-relayed
  hashes can take time to appear at the selected RPC. A timeout means
  "submitted, confirmation not visible yet", so keep the explorer link and
  let the UI resume polling.
- Normalize felt addresses before comparison. Compare
  `BigInt(left) === BigInt(right)`, since padded and unpadded hexadecimal
  strings can name the same token or account.

- A shield is two transactions: the ERC-20 `approve` must land onchain before
  the private deposit, so the wallet prompts twice. Label both steps in the
  UI, or the second prompt reads as a duplicate-transaction bug.
- Private transfers run between registered pool users. The wallet registers
  the sender automatically on first use, but the recipient must also be
  registered, and only they can do it. Design recipient-onboarding UX, and for
  pay-before-they-register flows look at the escrow pattern in
  `strk20-anonymizer-contracts`.
- The literal amount `"OPEN"` on a transfer creates an **open note**, the slot
  a DeFi helper's output gets credited into. Inside invoke calldata the wallet
  resolves two placeholders: `${openNoteIds[N]}` (id of the Nth open note in
  this transaction) and `${poolAddress}` (the privacy pool address).
- A flat pool fee applies per private operation. Read it from the pool's
  `get_fee_amount` rather than hardcoding (4 STRK on mainnet when the official
  agent-skill repo was written). Subtract it when pre-filling a MAX amount, or
  the operation fails after the user has signed. Wallet flows currently
  sponsor gas fees but not pool fees.

## Private DeFi end to end (two actions, one transaction)

```ts
const actions: STRK20_ACTION[] = [
  // 1. Open the note the swap output will be credited into.
  { type: "transfer", token: tokenOut, amount: "OPEN", recipient: userAddress },
  // 2. Call the helper. ${openNoteIds[0]} is the note opened above.
  {
    type: "invoke",
    contract: swapHelperAddress,
    calldata: [tokenIn, tokenOut, amountIn, "${openNoteIds[0]}"],
  },
]
const { transaction_hash } = await account.strk20InvokeTransaction(actions)
```

The pool withdraws `amountIn` to the helper, calls its `privacy_invoke`, and
credits the returned `OpenNoteDeposit` into the open note, atomically.
Calldata order must match the helper's `privacy_invoke` signature exactly (the
pool deserializes it straight into that function's parameters). Observers see
pool, then helper, then AMM, then helper. They never see who initiated it.

- Dry-run before submitting: `await account.strk20PrepareInvoke(actions, true)`
  builds and proves without submitting, the cheapest way to catch a
  calldata-shape mistake.
- Shielded balances are a wallet call too:
  `await account.strk20Balances([tokenIn, tokenOut])` returns
  `[{ token, balance }]`. It triggers a wallet consent prompt for balance
  access, so call it only as a deliberate balance-display feature.

## AVNU private swaps, no Cairo at all

Swapping is the one DeFi action that needs no helper of your own. AVNU
deployed its executor.

```ts
// npm install @avnu/avnu-sdk@^4.2.0 starknet@10.4.0
import { createStrk20WalletProver, executePrivateSwap, PRIVACY_POOL_ADDRESS } from "@avnu/avnu-sdk"

const prover = createStrk20WalletProver(walletAccount)
const { transactionHash } = await executePrivateSwap({
  quote,                       // from AVNU's quote endpoint
  slippage: 0.01,
  takerAddress: walletAccount.address,
  poolAddress: PRIVACY_POOL_ADDRESS, // mainnet; SEPOLIA_PRIVACY_POOL_ADDRESS for testing
  feeMode: { poolFeeToken: quote.sellTokenAddress },
  prover,
})
```

- The sell token must already be shielded. The swap moves value inside the
  pool and cannot shield for you.
- If a paymaster API key is required (`sponsored_private` fee mode), keep that
  call server-side. Browser dapps split the flow: `buildPrivateSwapFee` and
  `submitPrivateSwap` from a server endpoint, only the `prover` step
  client-side with the user's wallet.
- Any non-swap DeFi action still needs your own anonymizer contract
  (`strk20-anonymizer-contracts`) plus the two-action pattern above.

## Privacy doctrine for product UX

- **Shield separately, ahead of time.** A deposit is public and names the
  depositor. A later private transfer has no public leg. Because they are
  separate transactions, nothing onchain ties them, and that separation is
  what breaks linkage (see `references/app__tip-jar.md`).
- New notes mature ~10 blocks before they are spendable. Build the wait into
  the UX.
- Every private transaction is submitted by a relayer, so the transaction
  sender is the relayer's account for all users. Attribute per-user activity
  from the pool's `Deposit` event (first indexed key), never from the
  transaction sender (per the official agent-skill repo).
- Be explicit in-product about what stays public: deposits, withdrawals,
  open-note amounts, timing, and app-side actions.

## Testing

End-to-end flows need the pool, a privacy-enabled wallet, and proving. Plan
wallet-flow testing against a public network with the Ready extension (Xverse
in progress), not a pure local devnet (per the official agent-skill repo).
Fastest start: `Akashneelesh/strk20-starter-kit` (Next.js, Wallet API wired,
live demo at starknet-privacy-starter.vercel.app).

## references/

- `starknet-wallet-api__overview.md`, the route, install, capabilities
- `starknet-wallet-api__starknet-start-hook.md`, React `useStrk20` hooks
- `starknet-wallet-api__starknet-js.md`, direct `WalletAccountV6`
- `starknet-wallet-api__private-defi.md`, open notes plus invoke, placeholders, dry-run
- `starknet-wallet-api__avnu-private-swaps.md`, AVNU SDK swap route
- `app__tip-jar.md`, worked example of adding a private path to a live app

Snapshot and npm registry check 2026-08-16. Versions and wallet support move.
Verify against https://strk20-by-example.org (append `.md` to any page for raw
Markdown) before launch.
