# Notes & Nullifiers

Source: https://strk20-by-example.org/notes-and-nullifiers

> The UTXO note model - how private balances are stored, spent and protected from double-spending

A **note** is the unit of private balance inside the pool. It is an immutable
record of three things:

- **Owner** - a Starknet address, authorized to spend by its account signature
  plus knowledge of its private viewing key
- **Token** - the ERC-20 contract address
- **Amount** - a 128-bit value, stored encrypted on-chain

## Spending is all-or-nothing (UTXO)

Notes cannot be partially spent. To pay 30 out of a 100-token note, you consume
the whole note and create two new ones:

```
        ┌────────────────┐        spend        ┌──────────────────────┐
Alice ──│ note: 100 USDC │──────────────────►  │ note: 30 USDC → Bob  │
        └────────────────┘  publish nullifier  │ note: 70 USDC → Alice│ (change)
                                               └──────────────────────┘
```

This is exactly Bitcoin's UTXO model, but every input and output is encrypted.
A zero-knowledge proof guarantees the amounts balance without revealing them.

## Open notes

An **open note** deliberately skips amount encryption. It uses a
protocol-reserved salt, so the stored payload is plaintext, and its amount can
be filled in _after_ proof generation:

- salt = `OPEN_NOTE_SALT` (= 1); encrypted notes always use salt ≥ 2
- amount is zero while awaiting deposit, then the plaintext filled amount
- token address is stored in the clear

Open notes exist for DeFi: a swap's output amount is only known at execution
time, long after the client proved its transaction. An anonymizer contract fills the
open note with the actual output, which then becomes spendable private balance.

## Where a note lives

Notes are not stored in one global list. Each note's storage location is
derived from the **channel key** (a secret shared by sender and recipient), the
token, and a sequential index inside the channel's per-token subchannel:

```cairo
/// `note_id = h(NOTE_ID_TAG, channel_key, token, index, 0)`
pub(crate) fn compute_note_id(
    channel_key: felt252, token: ContractAddress, index: usize,
) -> felt252 {
    hash([NOTE_ID_TAG, channel_key, token.into(), index.into(), Zero::zero()].span())
}
```

Indices are dense and sequential (0, 1, 2, …), and every note cell is
**WriteOnce** - written once, never mutated. Without the channel key, note
locations are indistinguishable from random storage slots.

## Nullifiers

Spending a note does not delete it. Instead the spender publishes a
**nullifier** - a one-way Poseidon hash bound to the note and to the owner's
private viewing key:

```cairo
/// `nullifier = h(NULLIFIER_TAG, channel_key, token, index, 0, owner_private_key)`
pub(crate) fn compute_nullifier(
    channel_key: felt252, token: ContractAddress, index: usize, owner_private_key: felt252,
) -> felt252 {
    hash(
        [NULLIFIER_TAG, channel_key, token.into(), index.into(), Zero::zero(), owner_private_key]
            .span(),
    )
}
```

Three properties make this work:

| Property      | Meaning                                                                                             |
| ------------- | --------------------------------------------------------------------------------------------------- |
| Deterministic | The same note always produces the same nullifier - no way to spend twice under different nullifiers |
| Unique        | Exactly one valid nullifier per note; the contract rejects any repeat                               |
| Unlinkable    | Without the owner's viewing key, a published nullifier cannot be matched to any note                |

Note the asymmetry: because the nullifier includes the _owner's_ private
viewing key, even the sender who created a note cannot compute its nullifier -
so a sender cannot watch for when their payment gets spent.

Next: how keys encrypt all of this - [Encryption & Viewing Keys](/viewing-keys).

---

