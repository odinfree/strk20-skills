---
name: strk20-anonymizer-contracts
description: Write, review, or audit Cairo anonymizer (helper) contracts for STRK20 private DeFi. Covers the privacy_invoke entry point the pool calls, OpenNoteDeposit returns, the balance-delta idiom, and the swap, Vesu lending, and escrow patterns. Use for the contract side of any STRK20 DeFi integration, or when a privacy_invoke call is being designed or debugged. Pairs with strk20-wallet-api (how a dapp reaches the helper), strk20-privacy (concepts), and cairo-contracts or cairo-security for general Cairo work.
---

# STRK20 anonymizer contracts (`privacy_invoke`)

Anonymizer contracts, also called helper contracts, are how private funds
interact with the outside world (DEXs, lending vaults, escrows) without
revealing who is behind the interaction. Full doc pages with complete Cairo
sources sit in `references/`.

## The pattern: an atomic sandwich

```
withdraw from pool  →  helper does something  →  deposit result to an open note
```

1. The pool **withdraws** input tokens to the helper. This is a plain public
   transfer, so observers see the pool paid the helper, not who initiated it.
2. The pool calls the helper's `privacy_invoke` entry point via the protocol's
   `INVOKE_SELECTOR`.
3. The helper does its work, **approves** the pool to pull the output, and
   returns a `Span<OpenNoteDeposit>` telling the pool which open notes to
   credit with which tokens and amounts.

The output lands in an open note. Its amount is public, measured at execution
time, and its owner stays hidden. Everything happens in one transaction. A
revert anywhere aborts the whole pool transaction and no funds move.

## The contract surface

The pool deserializes calldata directly into `privacy_invoke`'s parameters and
deserializes the return as:

```cairo
/// From privacy::objects
pub struct OpenNoteDeposit {
    pub note_id: felt252,      // the open note to credit
    pub token: ContractAddress,
    pub amount: u128,
}
```

You design the signature. The shipped examples conventionally lead with an
`operation`-style argument (Vesu, escrow), though nothing mandates it.

## The five rules

1. **Return exactly a `Span<OpenNoteDeposit>`.** Anything else, or trailing
   garbage, makes the pool reject the call.
2. **Approve, don't transfer.** The pool executes the pull itself when
   applying the deposits.
3. **An empty span is valid.** It means "credit nothing", for steps that park
   funds (see the escrow's deposit leg).
4. **Measure output by balance delta.** Never trust the external protocol's
   return value:
   ```
   balance_before = out_token.balance_of(helper)
   ...external call...
   out_amount = out_token.balance_of(helper) - balance_before   // u256 → u128, checked
   ```
   This works with any protocol, handles fee-on-transfer tokens, and credits
   exactly what the pool can actually pull.
5. **One external invoke per transaction.** Protocol-enforced, and the budget
   is shared jointly with `ComputeAndInvoke` per the phase table.

## Worked examples. Know the provenance

| Helper | Provenance | What it teaches |
| --- | --- | --- |
| EchoHelper | official monorepo test contract | The minimal surface: calldata in, span out |
| SwapHelper | official monorepo mock (`mock_swap_executor`) | The tutorial DEX template: AMM address and selector pinned at deployment, generic `call_contract_syscall`, balance delta, `u256→u128` overflow guard, `ZERO_OUT_AMOUNT` guard |
| Ekubo swap anonymizer | official reference package (`packages/ekubo_swap_anonymizer`) | The production-grade DEX reference: single-hop Ekubo swap, full-swap-only. Study it when adapting the mock template to a live AMM |
| VesuLendingHelper | official reference package (`vesu_lending_anonymizer`) | ERC-4626/SNIP-22 vaults: deposit and withdraw through one entry point via token roles, stateless and permissionless (approves whoever called, holds nothing across transactions), shares return value ignored in favor of the delta. Reference example only: adoption stays with the app team and the integration is in progress |
| Escrow | unofficial site example, not in the monorepo, not reviewed or audited by Starkware | Stateful helper: commitment `poseidon(ESCROW_COMMITMENT_TAG, secret)`, pinned pool address with a `CALLER_NOT_PRIVACY` check, a `claimed` flag against double-claims, deposit leg returns an empty span |
| Outbound/InboundAnonymizer | `starkware-libs/privacy-bridge` | Cross-chain pair over Circle CCTP. The inbound side pairs `privacy_invoke` with `privacy_compute` to bind the attested message and the private note in one transaction |

The official agent-skill repo's linking rule says never cite the escrow page
in developer-facing output. Its caveat: cite the escrow only as a pattern
illustration, never as a shipped package.

## Security checklist for a new helper

- Stateful helper (holds funds across transactions)? Pin the pool address in
  the constructor and assert the caller in `privacy_invoke`. Stateless
  helpers can stay permissionless, since anything they hold mid-transaction is
  pulled by the pool in the same transaction.
- Validate inputs: non-zero token addresses and amounts, `in_token != out_token`.
- Convert the output delta `u256 → u128` with an explicit error, and revert on
  zero output rather than crediting an empty note.
- Let external reverts propagate. Aborting the pool transaction is the safe
  outcome.
- Note amounts are u128. Vault math in u256 must fit or the call reverts.
- Ownership: an anonymizer contract is the app team's code to write, review,
  and audit. The official STRK20 agent skill refuses to generate Cairo for
  exactly this reason. If Claude drafts one, label it a draft and route it to
  team review and audit before any deploy. Run the `cairo-security` skill over
  it.

## The dapp side

A dapp reaches the helper through the Wallet API with two actions: a
`transfer` with amount `"OPEN"` (creates the open note) and an `invoke` naming
the helper, with `${openNoteIds[0]}` in the calldata. Calldata order must match
the helper's `privacy_invoke` signature. Details and the dry-run flow live in
the `strk20-wallet-api` skill. Swaps alone need no custom helper, since AVNU
ships an executor.

## references/

- `helpers__privacy-invoke.md`, anatomy, rules, EchoHelper source
- `helpers__swap-helper.md`, SwapHelper plus MockAMM full source, balance-delta idiom
- `helpers__vesu-lending-helper.md`, official Vesu reference, full source
- `helpers__escrow.md`, unofficial stateful example, full source

Snapshot 2026-08-16. Contract packages live in
`starkware-libs/starknet-privacy`. Verify current sources there before
adapting.
