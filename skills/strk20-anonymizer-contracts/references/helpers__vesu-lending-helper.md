# Vesu Lending Helper

Source: https://strk20-by-example.org/helpers/vesu-lending-helper

> Earn lending yield privately - the official reference helper for Vesu ERC-4626 vaults

The Vesu lending helper connects the privacy pool to
[Vesu](https://vesu.xyz), a permissionless lending protocol whose pools are
ERC-4626 / SNIP-22 tokenized vaults: deposit underlying assets, receive vToken
shares; withdraw by burning shares. This is the reference anonymizer contract used in
the official Starknet Privacy docs. It is a reference example: review and
adoption of the Vesu route remain with the app team, and the integration is
in progress.

Two operations, one entry point:

- **Deposit** - underlying → vToken shares. `out_token` is the vault; the helper
  approves it, calls `deposit`, and the minted shares land in an open note.
- **Withdraw** - vToken shares → underlying. `in_token` is the vault; the helper
  calls `withdraw` and the returned assets land in an open note.

Your position in the vault is itself a private note holding vTokens - the yield
accrues to a position nobody can attribute to you.

```cairo
// Adapted from starknet-privacy packages/vesu_lending_anonymizer/src/vesu_lending_anonymizer.cairo
// (Apache-2.0, StarkWare)
use privacy::objects::OpenNoteDeposit;
use starknet::ContractAddress;

/// Interface for a Vesu vToken vault (ERC-4626 / SNIP-22 compatible).
#[starknet::interface]
pub trait IVToken<T> {
    /// Deposits assets into the pool and mints vTokens (shares) to the receiver.
    fn deposit(ref self: T, assets: u256, receiver: ContractAddress) -> u256;
    /// Withdraws assets from the pool and burns vTokens (shares) from the owner.
    fn withdraw(
        ref self: T, assets: u256, receiver: ContractAddress, owner: ContractAddress,
    ) -> u256;
}

/// Lending operation to perform on a Vesu vault.
#[derive(Serde, Copy, Drop, PartialEq, Debug)]
pub enum LendingOperation {
    Deposit,
    Withdraw,
}

#[starknet::interface]
pub trait IVesuLendingHelper<T> {
    /// Executes a lending operation on the Vesu lending pool.
    ///
    /// Called by the privacy contract via the `INVOKE_SELECTOR`.
    ///
    /// - `operation` - The lending operation to perform.
    /// - `in_token` - The token address of the input funds (on withdraw: the vToken).
    /// - `out_token` - The token address of the output funds (on deposit: the vToken).
    /// - `assets` - Amount of assets to deposit/withdraw.
    /// - `note_id` - The identifier of the open note to deposit the output to.
    fn privacy_invoke(
        ref self: T,
        operation: LendingOperation,
        in_token: ContractAddress,
        out_token: ContractAddress,
        assets: u256,
        note_id: felt252,
    ) -> Span<OpenNoteDeposit>;
}

/// Error codes for Vesu lending operations.
pub mod errors {
    pub const ZERO_IN_TOKEN: felt252 = 'ZERO_IN_TOKEN';
    pub const ZERO_OUT_TOKEN: felt252 = 'ZERO_OUT_TOKEN';
    pub const ZERO_ASSETS: felt252 = 'ZERO_ASSETS';
    pub const TOKENS_EQUAL: felt252 = 'TOKENS_EQUAL';
    pub const RECEIVED_AMOUNT_OVERFLOW: felt252 = 'RECEIVED_AMOUNT_OVERFLOW';
    pub const ZERO_OUT_AMOUNT: felt252 = 'ZERO_OUT_AMOUNT';
}

/// Vesu lending anonymizer contract that performs Vesu deposit/withdraw on behalf of the privacy
/// contract.
#[starknet::contract]
pub mod VesuLendingHelper {
    use core::num::traits::Zero;
    use openzeppelin::interfaces::token::erc20::{IERC20Dispatcher, IERC20DispatcherTrait};
    use privacy::objects::OpenNoteDeposit;
    use starknet::{ContractAddress, get_caller_address, get_contract_address};
    use super::{
        IVTokenDispatcher, IVTokenDispatcherTrait, IVesuLendingHelper, LendingOperation, errors,
    };

    #[storage]
    struct Storage {}

    #[constructor]
    fn constructor(ref self: ContractState) {}

    #[abi(embed_v0)]
    pub impl VesuLendingHelperImpl of IVesuLendingHelper<ContractState> {
        fn privacy_invoke(
            ref self: ContractState,
            operation: LendingOperation,
            in_token: ContractAddress,
            out_token: ContractAddress,
            assets: u256,
            note_id: felt252,
        ) -> Span<OpenNoteDeposit> {
            assert(in_token.is_non_zero(), errors::ZERO_IN_TOKEN);
            assert(out_token.is_non_zero(), errors::ZERO_OUT_TOKEN);
            assert(assets.is_non_zero(), errors::ZERO_ASSETS);
            assert(in_token != out_token, errors::TOKENS_EQUAL);

            let self_addr = get_contract_address();
            let privacy_addr = get_caller_address();
            let in_erc20 = IERC20Dispatcher { contract_address: in_token };
            let out_erc20 = IERC20Dispatcher { contract_address: out_token };

            // Get output token balance before operation.
            let balance_before = out_erc20.balance_of(account: self_addr);

            // Execute operation.
            // Return value (minted/burned shares) is ignored.
            match operation {
                LendingOperation::Deposit => {
                    // Approve Vesu Token contract to spend `assets` of `in_token`.
                    in_erc20.approve(spender: out_token, amount: assets);
                    IVTokenDispatcher { contract_address: out_token }
                        .deposit(:assets, receiver: self_addr)
                },
                LendingOperation::Withdraw => {
                    IVTokenDispatcher { contract_address: in_token }
                        .withdraw(:assets, receiver: self_addr, owner: self_addr)
                },
            }

            // Assert output amount is correct.
            let balance_after = out_erc20.balance_of(account: self_addr);
            let out_amount: u128 = (balance_after - balance_before)
                .try_into()
                .expect(errors::RECEIVED_AMOUNT_OVERFLOW);
            assert(out_amount.is_non_zero(), errors::ZERO_OUT_AMOUNT);

            // Approve caller (privacy contract) to transfer received output funds.
            out_erc20.approve(spender: privacy_addr, amount: out_amount.into());

            // Returns deposit to open note input.
            [OpenNoteDeposit { note_id, token: out_token, amount: out_amount }].span()
        }
    }
}

```

## Things to notice

- **Same skeleton as the swap helper** - validate inputs, snapshot the output
  balance, do the external call, credit the delta. Only the middle differs.
- **Stateless and permissionless** - unlike the escrow, this helper has no
  storage and no pinned pool address; it trusts only the balance delta and
  approves whoever called it. Anything it holds mid-transaction is pulled by the
  pool in the same transaction.
- **Directionality via token roles** - deposit puts the vault at `out_token`,
  withdraw puts it at `in_token`. One signature covers both directions.
- **Shares return value ignored** - the ERC-4626 return value is discarded in
  favor of the measured delta, for the same reasons as the swap helper.
- **`u256` assets, `u128` note amounts** - vault math is `u256`; the credited
  delta must fit a note's 128-bit amount or the call reverts.

Next: [Escrow](/helpers/escrow) - an unofficial worked example of a _stateful_
helper with its own commitment scheme.

---

