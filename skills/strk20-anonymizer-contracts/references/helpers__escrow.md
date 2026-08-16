# Escrow

Source: https://strk20-by-example.org/helpers/escrow

> A deferred-delivery escrow anonymizer contract - send privately to someone who has not registered yet

The escrow helper solves a real problem: you cannot privately transfer to someone
who has not registered a viewing key yet. Instead, you **escrow the funds behind a
secret**, share the secret off-chain (a claim link), and the recipient claims the
funds into their own note once they are registered.

> **Unofficial example.** Unlike the Ekubo and Vesu helpers, this contract is
> not shipped in the
> [starknet-privacy](https://github.com/starkware-libs/starknet-privacy) monorepo
> and has no SDK helper functions. It is a worked illustration of a stateful
> `privacy_invoke` helper - read it for the pattern, and own the review and audit
> if you build on it.

It is a two-operation state machine driven by `privacy_invoke`:

- **Deposit** - the pool withdraws tokens to the escrow, which stores a
  `CommitmentEntry` keyed by `poseidon(ESCROW_COMMITMENT_TAG, secret)`. Only the
  hash goes on-chain; the secret never does.
- **Claim** - the claimer proves knowledge of the secret preimage. The escrow marks
  the commitment claimed, approves the pool to pull the tokens, and returns an
  `OpenNoteDeposit` instructing the pool to credit the claimer's open note.

```cairo
// Original example written for strk20-by-example. Unlike the other helpers here,
// this is NOT adapted from the starknet-privacy monorepo - that repo ships no
// escrow package. Unofficial, and not reviewed or audited by StarkWare.
use privacy::objects::OpenNoteDeposit;
use starknet::ContractAddress;

/// Entry stored per commitment in the escrow.
#[derive(Serde, Copy, Drop, PartialEq, Debug, starknet::Store)]
pub struct CommitmentEntry {
    pub token: ContractAddress,
    pub amount: u128,
    pub claimed: bool,
}

/// Operation to perform on the escrow.
#[derive(Serde, Copy, Drop, PartialEq, Debug)]
pub enum EscrowOperation {
    Deposit,
    Claim,
}

#[starknet::interface]
pub trait IEscrow<T> {
    /// Returns the commitment entry for a given hash. All fields are zero if it does not exist.
    fn get_commitment(self: @T, commitment_hash: felt252) -> CommitmentEntry;

    /// Called by the privacy contract via the `INVOKE_SELECTOR`.
    ///
    /// Dispatches on `operation`:
    ///
    /// **Deposit** - Stores a commitment backed by tokens the pool already transferred to this
    /// contract. Returns an empty span (tokens stay in escrow).
    /// - `commitment_hash` - `poseidon(ESCROW_COMMITMENT_TAG, secret)` computed off-chain.
    /// - `token` - ERC-20 token address.
    /// - `amount` - Token amount to escrow.
    /// - `secret`, `note_id` - ignored.
    ///
    /// **Claim** - Verifies `hash(secret)` matches a stored commitment, marks it claimed,
    /// approves the caller (privacy contract) to pull tokens, and returns the deposit instruction.
    /// - `secret` - The preimage whose hash matches the stored commitment.
    /// - `note_id` - The open note identifier (computed by the SDK and passed in calldata).
    /// - `commitment_hash`, `token`, `amount` - ignored.
    fn privacy_invoke(
        ref self: T,
        operation: EscrowOperation,
        commitment_hash: felt252,
        token: ContractAddress,
        amount: u128,
        secret: felt252,
        note_id: felt252,
    ) -> Span<OpenNoteDeposit>;
}

/// Domain-separation tag for escrow commitment hashes.
pub const ESCROW_COMMITMENT_TAG: felt252 = 'ESCROW_COMMITMENT_TAG:V1';

pub mod errors {
    pub const ZERO_COMMITMENT_HASH: felt252 = 'ZERO_COMMITMENT_HASH';
    pub const ZERO_TOKEN: felt252 = 'ZERO_TOKEN';
    pub const ZERO_AMOUNT: felt252 = 'ZERO_AMOUNT';
    pub const COMMITMENT_EXISTS: felt252 = 'COMMITMENT_EXISTS';
    pub const COMMITMENT_NOT_FOUND: felt252 = 'COMMITMENT_NOT_FOUND';
    pub const ALREADY_CLAIMED: felt252 = 'ALREADY_CLAIMED';
    pub const CALLER_NOT_PRIVACY: felt252 = 'CALLER_NOT_PRIVACY';
}

/// Computes the commitment hash from a secret using domain-separated Poseidon.
pub fn compute_commitment_hash(secret: felt252) -> felt252 {
    core::poseidon::poseidon_hash_span([ESCROW_COMMITMENT_TAG, secret].span())
}

#[starknet::contract]
pub mod Escrow {
    use core::num::traits::Zero;
    use openzeppelin::interfaces::token::erc20::{IERC20Dispatcher, IERC20DispatcherTrait};
    use privacy::objects::OpenNoteDeposit;
    use starknet::storage::{
        StorageMapReadAccess, StorageMapWriteAccess, StoragePointerReadAccess,
        StoragePointerWriteAccess,
    };
    use starknet::{ContractAddress, get_caller_address};
    use super::{CommitmentEntry, EscrowOperation, IEscrow, compute_commitment_hash, errors};

    #[storage]
    struct Storage {
        privacy_contract: ContractAddress,
        commitments: starknet::storage::Map<felt252, CommitmentEntry>,
    }

    #[constructor]
    fn constructor(ref self: ContractState, privacy_contract: ContractAddress) {
        self.privacy_contract.write(privacy_contract);
    }

    #[abi(embed_v0)]
    pub impl EscrowImpl of IEscrow<ContractState> {
        fn get_commitment(self: @ContractState, commitment_hash: felt252) -> CommitmentEntry {
            self.commitments.read(commitment_hash)
        }

        fn privacy_invoke(
            ref self: ContractState,
            operation: EscrowOperation,
            commitment_hash: felt252,
            token: ContractAddress,
            amount: u128,
            secret: felt252,
            note_id: felt252,
        ) -> Span<OpenNoteDeposit> {
            let privacy_addr = self.privacy_contract.read();
            assert(get_caller_address() == privacy_addr, errors::CALLER_NOT_PRIVACY);

            match operation {
                EscrowOperation::Deposit => {
                    assert(commitment_hash.is_non_zero(), errors::ZERO_COMMITMENT_HASH);
                    assert(token.is_non_zero(), errors::ZERO_TOKEN);
                    assert(amount.is_non_zero(), errors::ZERO_AMOUNT);

                    let existing = self.commitments.read(commitment_hash);
                    assert(existing.token.is_zero(), errors::COMMITMENT_EXISTS);

                    self
                        .commitments
                        .write(
                            commitment_hash,
                            CommitmentEntry { token, amount, claimed: false },
                        );

                    // Tokens already transferred by the pool via Withdraw. Return empty span.
                    [].span()
                },
                EscrowOperation::Claim => {
                    let commitment_hash = compute_commitment_hash(secret);
                    let entry = self.commitments.read(commitment_hash);
                    assert(entry.token.is_non_zero(), errors::COMMITMENT_NOT_FOUND);
                    assert(!entry.claimed, errors::ALREADY_CLAIMED);

                    self
                        .commitments
                        .write(
                            commitment_hash,
                            CommitmentEntry { claimed: true, ..entry },
                        );

                    // Approve the privacy contract to pull the escrowed tokens.
                    IERC20Dispatcher { contract_address: entry.token }
                        .approve(spender: privacy_addr, amount: entry.amount.into());

                    [OpenNoteDeposit { note_id, token: entry.token, amount: entry.amount }].span()
                },
            }
        }
    }
}

```

## Things to notice

- **Access control** - `privacy_invoke` asserts the caller is the privacy pool.
  Nobody can drive the escrow directly.
- **Commitment hash is domain-separated** - `ESCROW_COMMITMENT_TAG` prevents the
  secret's hash from colliding with hashes used elsewhere.
- **Deposit returns an empty span** - tokens stay parked in the escrow, so there is
  nothing for the pool to credit yet.
- **Claim recomputes the hash from the secret** - the passed-in `commitment_hash`
  parameter is ignored on claim; only the preimage matters.
- **Double-claim protection** - the `claimed` flag flips exactly once; a second
  claim hits `ALREADY_CLAIMED`.

---

