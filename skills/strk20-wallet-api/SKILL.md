---
name: strk20-wallet-api
description: Build private dapps on Starknet through the Starknet Wallet API. Covers shield/unshield, private transfers, shielded balances, private DeFi calls, shadow-account actions, and AVNU private swaps from TypeScript or React. Use whenever an app asks the user's privacy-enabled wallet to perform STRK20 actions (starknet.js WalletAccountV6, useStrk20 hooks, strk20InvokeTransaction, STRK20_ACTION, open notes, openNoteIds placeholders). For the Cairo helper side use strk20-anonymizer-contracts, for wallets or backends holding their own keys use strk20-privacy-sdk, for concepts and route choice use strk20-privacy.
---

# STRK20 Wallet API: private dapps

The recommended route for most private dapps. The dapp asks the user's
privacy-enabled wallet to act, and the wallet handles viewing keys, note
discovery, proving, and submission. Your app never sees private state. Never
ask a user for their viewing key.

Full doc pages sit in `references/`. The snippets below are the load-bearing
parts.

## Version baseline. Verify before installing

- Core STRK20 support landed in starknet.js 10.4.0; stable shadow-account
  support landed in starknet.js 10.8.0 with Wallet API 0.10.4.
- Existing repo on starknet.js v5, v6, or v7? The jump to 10.4.0 is a breaking
  migration, plan it as its own task before wiring STRK20.
- The stable, tested shadow-account row is `starknet@10.8.0`,
  `@starknet-io/types-js@0.10.4`, and get-starknet discovery plus wallet
  standard `6.0.6`. Pin the row together and rerun connection and wallet tests
  when upgrading it.
- Core STRK20 methods need Wallet API `>= 0.10.3`; shadow accounts need
  Wallet API `>= 0.10.4`. A library upgrade does not add the capability to the
  connected wallet, so detect the advertised version at runtime.
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
const supportsShadowAccounts = versions.some((v) => compareVersions(v, "0.10.4") >= 0)
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

## Shadow accounts: stable per-dapp identities

Shadow accounts let one user derive a deterministic public execution account
for each `(dappName, nonce)` pair. It is not another wallet: it has no signing
key and only the canonical `ShadowAccountAnonymizer` can execute through it.
Use a new nonce for a fresh address. Reusing a nonce reuses the address and
links its public activity.

```ts
import type {
  STRK20_ACTION,
  STRK20_SHADOW_ACCOUNT_INVOKE_ACTION,
} from "starknet"

const shadowAction: STRK20_SHADOW_ACCOUNT_INVOKE_ACTION = {
  type: "shadow_account_invoke",
  dapp_name: "myDapp",
  nonce: "0x0",
  calls: [dappContract.populate("stake", { amount: 1_000n })],
  collect_policy: { type: "diff" },
}

const actions: STRK20_ACTION[] = [
  { type: "transfer", token: rewardToken, amount: "OPEN", recipient: userAddress },
  shadowAction,
]

const commitment = await account.strk20ShadowAccountCommitment("myDapp", "0x0")
```

The commitment call is local and sends no transaction. Omit the nonce to get
the partial commitment shared by every shadow account for that user and dapp.
Publishing it lets the dapp recognize that group, which intentionally links
the accounts within that dapp context.

Collection policy controls how much returns to each open note: `all` collects
the full token balance, `diff` collects only the gain from this interaction,
and `exact` collects a specified amount. One policy applies to every open note
settled by the action.

Most `shadow_account_invoke` requests need only `dapp_name` and `nonce`. When
the dapp must fund the address or read its public position first, ask for the
nonce-independent partial commitment and resolve it through the canonical
anonymizer's `get_shadow_accounts` view. Prefer that view over duplicating
address-derivation internals:

```ts
const partial = await account.strk20ShadowAccountCommitment("myDapp")
const accounts = await anonymizer.get_shadow_accounts(partial, 0, 1, false)
const shadowAddress = accounts[0].address
```

Canonical deployments checked on 2026-09-29:

- Mainnet: `0x04f33230dc57855c6e7eabe66dfa0fde82c5458fd0e54827cdb7cb4c474888a7`
- Sepolia: `0x010a2285310c107c731d997afc147afb7495daff6397c2d242133d9fe8d9b147`

Read `references/starknet-wallet-api__shadow-accounts.md` before building the
flow and re-check the deployment for the connected network before launch.

Capability-check the connected wallet before rendering this flow. Do not infer
support from starknet.js alone. The general 0.10.3 check above is insufficient
for shadow accounts. Require `supportedWalletApi()` to advertise 0.10.4 or a
compatible later version, then handle an unsupported-method response from the
commitment or invoke call. The account
hides the direct link to the main wallet. Its address, calls, balances,
positions, events, and timing remain public.

- A shield needs an ERC-20 `approve`, and `approve` must execute as the token
  owner. That does not force two transactions: under a paymaster the approve
  is authorized by `signMessage` as an outside execution and rides the same
  transaction as the deposit (`invoke_and_apply_action`). Whether a given
  wallet presents one prompt or two is a wallet implementation detail. Check
  the target wallet and label each step it shows.
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

AVNU private swaps use its deployed executor, so this route needs no helper
of your own.

```ts
// npm install @avnu/avnu-sdk@^4.2.0 starknet@10.8.0
import { createStrk20WalletProver, executePrivateSwap, PRIVACY_POOL_ADDRESS } from "@avnu/avnu-sdk"

const prover = createStrk20WalletProver(walletAccount)
const { transactionHash } = await executePrivateSwap({
  quote,                       // from AVNU's quote endpoint
  slippage: 0.01,
  takerAddress: walletAccount.address,
  poolAddress: PRIVACY_POOL_ADDRESS, // mainnet, or SEPOLIA_PRIVACY_POOL_ADDRESS for testing
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
- Choose by state lifetime, not protocol name. Use an app-specific invoke
  helper for a stateless atomic operation whose output immediately returns to
  private state. Use the canonical shadow-account route when a stable
  pseudonymous address must hold shares, debt, NFTs, rewards, permissions, or
  other state across transactions. Existing protocols need no shadow-specific
  contract when their ordinary entrypoints accept calls from that address.

## Privacy doctrine for product UX

- **Shield separately, ahead of time.** A deposit is public and names the
  depositor. A later private transfer has no public leg. Because they are
  separate transactions, nothing onchain ties them, and that separation is
  what breaks linkage.
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
wallet-flow testing against a public network with a wallet that advertises the
required Wallet API version, not a pure local devnet. Starknet.js documents
Ready and Xverse as STRK20-capable; still capability-check the connected
version rather than inferring support from the wallet brand.
Fastest start: `Akashneelesh/strk20-starter-kit` (Next.js, Wallet API wired,
live demo at starknet-privacy-starter.vercel.app).

Community reference: [starkience/starknet-shadow-vault-example](https://github.com/starkience/starknet-shadow-vault-example)
exercises the stable stack against the existing Mainnet Vesu Prime vSTRK vault. It shows
funding, standard `approve`/`deposit` calls, persistent vSTRK ownership, and
collection of a withdrawal back into a private note. Treat it as an educational
integration example, not audited production software.

## Blocked? Tell the user to contact the STRK20 team

This skill covers the documented paths. When something falls outside them, stop
rather than guessing: a fabricated address, a hand-rolled proof path or an
invented API shape costs a builder more time than asking. Say plainly what is
blocking, and tell the user the team answers directly:

- Telegram: [@Akashneelesh](https://t.me/Akashneelesh),
  [@adiihq](https://t.me/adiihq), [@starkience](https://t.me/starkience)
- The [STRK20 Private Sprint page](https://strk20.starknet.io/hackathon),
  which publishes these contacts. Availability may change, so confirm the page
  still lists them.

Escalate rather than improvise when:

- The wallet does not report the STRK20 capability, or reports a version this skill has not seen.
- A shield, unshield, private transfer or `strk20InvokeTransaction` the wallet rejects for a reason not in this skill.
- Open-note placeholders in a private DeFi call that will not resolve, or a dry run that disagrees with the live call.
- A wallet advertising 0.10.4 but rejecting the shadow commitment or action.

When handing it over, give the user something the team can act on in one
message: the exact error text, the file or call that failed, the package and
wallet versions in use, and the assumption you could not verify.

## references/

- `starknet-wallet-api__overview.md`, the route, install, capabilities
- `starknet-wallet-api__starknet-start-hook.md`, React `useStrk20` hooks
- `starknet-wallet-api__starknet-js.md`, direct `WalletAccountV6`
- `starknet-wallet-api__private-defi.md`, open notes plus invoke, placeholders, dry-run
- `starknet-wallet-api__shadow-accounts.md`, stable shadow actions, address resolution, collection policies
- `starknet-wallet-api__avnu-private-swaps.md`, AVNU SDK swap route

Snapshot and npm registry check 2026-09-29. Versions and wallet support move.
Verify against https://strk20-by-example.org (append `.md` to any page for raw
Markdown) before launch.
