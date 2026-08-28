# Shadow accounts: builder guide and verified status

This is an authored implementation note, not a verbatim source snapshot. It
combines the user-supplied `shadow-accounts_overview.pdf` dated 2026-08-28 with
the `starkware-libs/starknet-privacy` source at commit
`980da8affafb9f8350975ca93c03b2299a31ac9b` and the Wallet API development
spec. The PDF footer identifies the Starknet privacy pool, the shadow-account
anonymizer, and Apache-2.0. Re-check the linked source before launch.

## What a shadow account is

A shadow account is a real Starknet account controlled through the configured
shadow-account anonymizer. The anonymizer maps an identity commitment to the
account, deploys it when needed, executes dapp calls through it, and collects
selected token proceeds into STRK20 open notes.

The configured privacy pool is the only contract allowed to drive the
anonymizer. The user directs the account indirectly through a proved private
action. The shadow account does not expose the user's viewing key.

Its identity is deterministic:

```text
identity_key = compute_identity_key(user, viewing_key, anonymizer)
partial_commitment = hash(identity_key, dapp_name)
commitment = hash(partial_commitment, nonce)
shadow_account = contract_address(commitment, primer_class, anonymizer)
```

One user can therefore have many accounts per dapp. A new nonce selects a new
address. Reusing the same `(dapp_name, nonce)` selects the same account.

## Privacy boundary

Shadow accounts hide the direct onchain link between the main wallet and the
dapp account. They do not hide the shadow account's own public history.

Public and linkable:

- the shadow account address and deployment
- target contracts, entrypoints, calldata, and emitted events
- token balances and other public account state
- DeFi positions or NFTs held by the account
- timing and repeated use of the same `(dapp_name, nonce)` account

Private through STRK20:

- which registered user derived the identity commitment
- which private notes funded the action
- the direct main-wallet link, unless the surrounding flow reveals it
- the owner link of proceeds collected into open notes

Do not describe assets as shielded while they sit in the shadow account. They
are public account state during that interval. Open-note token and amount
remain public. A precise lifecycle is:

```text
encrypted input note
  -> public shadow-account activity
  -> open note with hidden owner link and public token/amount
  -> optional private spend into an encrypted note
```

Publishing the nonce-independent partial commitment lets a dapp recognize the
user's shadow accounts without learning each nonce. That intentionally groups
those accounts inside the dapp's own context. Publish it only when the product
needs that continuity.

## SDK route

SDK `0.14.3-rc.5` uses `shadowAccounts`, not the RC.4 `subaccounts` name.

```ts
const nonce = 0n

const fullCommitment = await transfers
  .build()
  .shadowAccounts("myDapp")
  .commitment(nonce)

const { callAndProof } = await transfers
  .build()
  .with(rewardToken)
  .transfer({ recipient: userAddress, amount: Open })
  .done()
  .shadowAccounts("myDapp")
  .invoke(nonce, {
    calls: [dappContract.populate("claim", [])],
    collectPolicy: { type: "diff" },
  })
  .execute({ provingBlockId })
```

The exact fluent-chain order can move during the release-candidate cycle. Use
the installed TypeScript declarations as the final authority. Configure
`shadowAccountAnonymizerAddress` in `createPrivateTransfers`.

Collection policy selects how much of each token returns to its open note:

| Policy | Amount collected |
| --- | --- |
| `{ type: "all" }` | Entire shadow-account token balance |
| `{ type: "diff" }` | Positive balance gained during this interaction |
| `{ type: "exact", amount }` | The specified amount |

One policy applies to every open note settled by one invocation. `diff` fails
when the post-call balance is below the pre-call balance. `exact` fails when
the account lacks the requested amount.

## Wallet route

The Wallet API 0.10.4-rc.1 development spec defines:

- `wallet_strk20ShadowAccountCommitment`
- `STRK20_SHADOW_ACCOUNT_INVOKE_ACTION`
- `dapp_name`, `nonce`, `calls`, and `collect_policy`

The method computes a commitment locally and sends no transaction. With a
nonce it returns one full account commitment. Without a nonce it returns the
partial commitment shared by that user's accounts for the dapp.

`@starknet-io/types-js@0.10.4-beta.2` and `starknet@10.7.1` on npm `next`
include the new action. Stable types-js 0.10.3 does not. The presence of the
types and `WalletAccountV6.strk20ShadowAccountCommitment()` does not prove a
connected wallet implements the method. Capability-check the wallet at
runtime. Require `supportedWalletApi()` to advertise the 0.10.4-rc.1
shadow-account schema or a compatible later version, handle an
unsupported-method response, and keep a fallback path.

The monorepo's `@starkware-libs/starknet-privacy-client` source includes a
builder and address resolver at version 0.1.0. It was not available from the
configured package registry during the 2026-08-28 check. Treat it as source
code, not a generally installable package, until the registry proves otherwise.

## Long-lived DeFi patterns from the overview

The PDF adds two useful architectural patterns. They are examples, not recipes
verified by this audit:

- A lending account can supply collateral, hold a debt position, shield the
  borrowed token, then reuse the same nonce later to repay and collect the
  released collateral. The PDF names Vesu.
- An unstaking account can hold a withdrawal NFT through its waiting period,
  redeem it later, then collect the redeemed STRK into the pool. The PDF names
  Endur.

These patterns need account continuity, so do not rotate the nonce between
the opening and closing legs. That continuity also links those legs to the
same public shadow account.

## Does it work?

Verified locally on 2026-08-28 against upstream commit
`980da8affafb9f8350975ca93c03b2299a31ac9b`:

- Cairo `shadow_account_anonymizer`: 43 tests passed with Starknet Foundry
  0.63.0
- SDK shadow-account unit file: 7 tests passed
- client shadow-account, prover, and client unit files: 22 tests passed
- the latest relevant upstream devnet workflow before the check completed
  successfully on 2026-08-25

The upstream devnet tests exercise deployment, dapp calls, collection into an
open note, deterministic address lookup, and dapp scoping. They set the
anonymizer policy to `Exempt` because the suite lacks a mock prover that can
attest the shadow account. The intended deployed policy is `Delegated`, where
the pool screens the shadow account. The test therefore proves the core flow,
not the production screening integration.

No public-network anonymizer address, wallet implementation receipt, or
production deployment receipt was established in this check. The defensible
status is:

- contract layer works under tests
- SDK and client plumbing works under unit tests
- relevant upstream devnet workflow passed
- prerelease Wallet API and starknet.js plumbing exists
- production screening, wallet rollout, audits, and public deployment still
  need current receipts

## Launch gate

Before shipping:

1. Pin the SDK, starknet.js, types-js, and Wallet API versions together.
2. Verify the anonymizer address and class hash for the target network.
3. Verify the connected wallet implements both the shadow action and
   commitment method.
4. Test `Delegated` screening with the production proving path.
5. Test fresh and reused nonces, all three collection policies, interrupted
   async positions, and recovery after failed dapp calls.
6. State the public shadow-account history in product copy.
7. Obtain current audit and deployment evidence before describing the route as
   production-ready.

## Primary sources

- <https://github.com/starkware-libs/starknet-privacy/tree/980da8affafb9f8350975ca93c03b2299a31ac9b/packages/shadow_account_anonymizer>
- <https://github.com/starkware-libs/starknet-privacy/blob/980da8affafb9f8350975ca93c03b2299a31ac9b/sdk/src/internal/shadow-accounts.ts>
- <https://github.com/starkware-libs/starknet-privacy/blob/980da8affafb9f8350975ca93c03b2299a31ac9b/client/src/shadow-accounts.ts>
- <https://github.com/starkware-libs/starknet-privacy/blob/980da8affafb9f8350975ca93c03b2299a31ac9b/e2e/tests/devnet/shadow-account-invoke.test.ts>
- <https://github.com/starkware-libs/starknet-specs/blob/master/wallet-api/wallet_rpc.json>
- <https://github.com/starkware-libs/starknet-specs/pull/406>
- <https://github.com/starkware-libs/starknet-privacy/actions/runs/32838588203>
