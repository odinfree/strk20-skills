# Actions, Phases & Proofs

Source: https://strk20-by-example.org/actions-and-proofs

> The phased action model, the per-token balance invariant, and how transactions are proven with Stwo

Every pool transaction is a batch of **client actions**. Actions are grouped
into phases with a fixed ordering - a transaction may skip phases, but must
never go backwards:

| Phase | Action                                              | Effect on temp balance |
| ----- | --------------------------------------------------- | ---------------------- |
| 0     | `SetViewingKey`                                     | -                      |
| 1     | `OpenChannel`                                       | -                      |
| 2     | `OpenSubchannel`                                    | -                      |
| 3     | `Deposit`                                           | + amount               |
| 4     | `UseNote`                                           | + note amount          |
| 5     | `CreateEncNote` / `CreateOpenNote`                  | − amount               |
| 6     | `Withdraw`                                          | − amount               |
| 7     | `InvokeExternal` / `ComputeAndInvoke` (at most one) | -                      |

`ComputeAndInvoke` is the sub-account path: it runs `privacy_compute` client-side
and forwards the result as a server-side invoke. It shares phase 7 with
`InvokeExternal`, and the "at most once" rule covers the two jointly.

The fixed ordering removes state-machine ambiguity: there is exactly one way to
encode a given semantic operation, which closes whole classes of ordering bugs.
`InvokeExternal` is the composability hook - it calls an anonymizer contract
(DEX adapter, lending vault) at most once per transaction.

## The balance invariant

Within one transaction, the contract tracks a **temporary balance per token**:
inflows (`Deposit`, `UseNote`) add, outflows (`CreateNote`, `Withdraw`)
subtract. Two rules are enforced:

- The balance may **never go negative** at any point.
- Every token's balance must end at **exactly zero**.

```cairo
fn subtract_balance(ref self: TokenBalances, token: ContractAddress, amount: u128) {
    let (entry, current_balance) = self.entry(key: token.into());
    let new_value = current_balance
        .checked_sub(amount)
        .expect(errors::NEGATIVE_INTERMEDIATE_BALANCE);
    self = entry.finalize(:new_value);
}
fn assert_valid(self: SquashedTokenBalances) {
    for (_token, _, balance) in self.into_entries() {
        assert(balance.is_zero(), errors::FINAL_BALANCE_MUST_BE_ZERO);
    }
}
```

No value is created, destroyed, or left unaccounted - a transfer of 30 from a
100-note _must_ create outputs totaling 100 (30 to the recipient, 70 change).

## From actions to an on-chain transaction

```
client builds actions
        │
        ▼
virtual Starknet execution          ← anchored to a recent block's state
  (dedicated virtual OS,              snapshot; unsupported syscalls fail
   compiles client → server actions)  here, at proving time
        │
        ▼
Stwo proof generation               ← ~29 s (12-core / 46 GiB; machine-dependent)
        │
        ▼
submit tx (directly or via paymaster)
        │
        ▼
sequencer-level verification        ← proof checked before execution;
        │                             contract validates proof facts
        ▼
apply_actions: storage writes, token transfers, events
```

The proof is generated over a **virtual Starknet execution environment**: the
transaction runs against an anchored state snapshot of a recent block, using
the same Cairo logic the chain uses. That gives native storage semantics and
account-abstraction signature checks (`is_valid_signature`) for free.

On submission, the contract checks the **proof facts** before applying anything:

- the proof came from the expected program variant (`VIRTUAL_SNOS`)
- the anchor block is recent - within `proof_validity_blocks` of the tip
- the proven message hash matches the submitted actions exactly

Stale proofs expire; mismatched actions are rejected; only then are storage
writes, ERC-20 transfers and events applied atomically.

Next: the escrowed key that makes all of this auditable -
[Compliance & Auditing](/compliance).

---

