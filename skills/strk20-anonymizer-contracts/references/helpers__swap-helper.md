# Swap Helper

Source: https://strk20-by-example.org/helpers/swap-helper

> A DEX swap anonymizer contract - trade privately through any AMM using the balance-delta idiom

The swap helper lets pool funds trade on an external AMM without revealing the
trader. The pool withdraws the input token to the helper, the helper swaps on the
AMM, and the received amount is credited to an open note - all in one atomic
transaction.

This is the canonical template for **any** DEX integration: only the AMM call in
the middle changes.

```cairo
// Adapted from starknet-privacy packages/privacy/src/test_contracts/mock_swap_executor.cairo
// (Apache-2.0, StarkWare). Renamed MockSwapExecutor -> SwapHelper for the tutorial.
use privacy::objects::OpenNoteDeposit;
use starknet::ContractAddress;

#[starknet::interface]
pub trait ISwapHelper<T> {
    /// Executes a swap on an external AMM/DEX and deposits the result to an open note.
    ///
    /// Called by the privacy contract via the `INVOKE_SELECTOR`.
    ///
    /// - `in_token` - The token address of the input funds.
    /// - `out_token` - The token address of the output funds.
    /// - `in_amount` - The amount of input funds to swap.
    /// - `note_id` - The identifier of the open note to deposit the output to.
    ///
    /// #### Flow
    /// 1. Approves swap contract to spend `in_amount` of in tokens.
    /// 2. Records output token balance, executes the swap, calculates received amount.
    /// 3. Approves the caller (privacy contract) to transfer the received output funds.
    /// 4. Returns a span of `OpenNoteDeposit` for the privacy contract to apply.
    fn privacy_invoke(
        ref self: T,
        in_token: ContractAddress,
        out_token: ContractAddress,
        in_amount: u128,
        note_id: felt252,
    ) -> Span<OpenNoteDeposit>;
}

pub mod errors {
    pub const ZERO_IN_TOKEN: felt252 = 'ZERO_IN_TOKEN';
    pub const ZERO_OUT_TOKEN: felt252 = 'ZERO_OUT_TOKEN';
    pub const ZERO_IN_AMOUNT: felt252 = 'ZERO_IN_AMOUNT';
    pub const IN_TOKEN_EQUAL_TO_OUT_TOKEN: felt252 = 'IN_TOKEN_EQUAL_TO_OUT_TOKEN';
    pub const INSUFFICIENT_BALANCE: felt252 = 'INSUFFICIENT_BALANCE';
    pub const ZERO_AMM_ADDRESS: felt252 = 'ZERO_AMM_ADDRESS';
    pub const ZERO_SELECTOR: felt252 = 'ZERO_SELECTOR';
    pub const RECEIVED_AMOUNT_OVERFLOW: felt252 = 'RECEIVED_AMOUNT_OVERFLOW';
    pub const ZERO_OUT_AMOUNT: felt252 = 'ZERO_OUT_AMOUNT';
}

#[starknet::contract]
pub mod SwapHelper {
    use core::num::traits::Zero;
    use openzeppelin::interfaces::token::erc20::{IERC20Dispatcher, IERC20DispatcherTrait};
    use privacy::objects::OpenNoteDeposit;
    use starknet::storage::{StoragePointerReadAccess, StoragePointerWriteAccess};
    use starknet::syscalls::call_contract_syscall;
    use starknet::{ContractAddress, SyscallResultTrait, get_caller_address, get_contract_address};
    use super::{ISwapHelper, errors};

    #[storage]
    struct Storage {
        amm_address: ContractAddress,
        selector: felt252,
    }

    #[constructor]
    fn constructor(ref self: ContractState, amm_address: ContractAddress, selector: felt252) {
        assert(amm_address.is_non_zero(), errors::ZERO_AMM_ADDRESS);
        assert(selector.is_non_zero(), errors::ZERO_SELECTOR);
        self.amm_address.write(amm_address);
        self.selector.write(selector);
    }

    #[abi(embed_v0)]
    pub impl SwapHelperImpl of ISwapHelper<ContractState> {
        fn privacy_invoke(
            ref self: ContractState,
            in_token: ContractAddress,
            out_token: ContractAddress,
            in_amount: u128,
            note_id: felt252,
        ) -> Span<OpenNoteDeposit> {
            assert(in_token.is_non_zero(), errors::ZERO_IN_TOKEN);
            assert(out_token.is_non_zero(), errors::ZERO_OUT_TOKEN);
            assert(in_amount.is_non_zero(), errors::ZERO_IN_AMOUNT);
            assert(in_token != out_token, errors::IN_TOKEN_EQUAL_TO_OUT_TOKEN);

            let self_addr = get_contract_address();
            let privacy_addr = get_caller_address();
            let in_erc20 = IERC20Dispatcher { contract_address: in_token };
            let out_erc20 = IERC20Dispatcher { contract_address: out_token };

            // Approve AMM to spend `in_amount` of `in_token`.
            assert(
                in_erc20.balance_of(account: self_addr) >= in_amount.into(),
                errors::INSUFFICIENT_BALANCE,
            );
            let amm_address = self.amm_address.read();
            in_erc20.approve(spender: amm_address, amount: in_amount.into());

            // Get output token balance before swap.
            let balance_before = out_erc20.balance_of(account: self_addr);

            // Execute swap (propagates error from AMM if it fails).
            call_contract_syscall(
                address: amm_address,
                entry_point_selector: self.selector.read(),
                calldata: [in_token.into(), out_token.into(), in_amount.into(), 0].span(),
            )
                .unwrap_syscall();

            // Calculate output amount.
            let balance_after = out_erc20.balance_of(account: self_addr);
            let out_amount: u128 = (balance_after - balance_before)
                .try_into()
                .expect(errors::RECEIVED_AMOUNT_OVERFLOW);
            assert(out_amount.is_non_zero(), errors::ZERO_OUT_AMOUNT);

            // Approve caller (privacy contract) to transfer received output funds.
            out_erc20.approve(spender: privacy_addr, amount: out_amount.into());

            // Return the open note deposit struct.
            [OpenNoteDeposit { note_id, token: out_token, amount: out_amount }].span()
        }
    }
}

```

The demo AMM it targets is a trivial 1:1 exchange - in production this would be
Ekubo, JediSwap, or any other DEX:

```cairo
// Adapted from starknet-privacy packages/privacy/src/test_contracts/mock_amm.cairo
// (Apache-2.0, StarkWare). Test-only entry points removed.
use starknet::ContractAddress;

/// Interface for the mock AMM.
#[starknet::interface]
pub trait IMockAMM<T> {
    fn swap(ref self: T, in_token: ContractAddress, out_token: ContractAddress, amount: u256);
}

/// Mock AMM contract used to demo the swap helper.
/// Implements a simple 1:1 swap.
#[starknet::contract]
pub mod MockAMM {
    use openzeppelin::interfaces::token::erc20::{IERC20Dispatcher, IERC20DispatcherTrait};
    use starknet::{ContractAddress, get_caller_address, get_contract_address};
    use super::IMockAMM;

    #[storage]
    struct Storage {}

    #[constructor]
    fn constructor(ref self: ContractState) {}

    #[abi(embed_v0)]
    impl MockAMMImpl of IMockAMM<ContractState> {
        fn swap(
            ref self: ContractState,
            in_token: ContractAddress,
            out_token: ContractAddress,
            amount: u256,
        ) {
            let caller = get_caller_address();

            // Transfer input tokens from caller.
            IERC20Dispatcher { contract_address: in_token }
                .transfer_from(sender: caller, recipient: get_contract_address(), :amount);

            // Transfer output tokens (1:1 exchange).
            IERC20Dispatcher { contract_address: out_token }.transfer(recipient: caller, :amount);
        }
    }
}

```

## The balance-delta idiom

The helper never trusts the AMM's return value. It measures what actually
arrived:

```
balance_before = out_token.balance_of(helper)
...swap...
out_amount = out_token.balance_of(helper) - balance_before
```

This is what makes the pattern universal - it works with any external protocol
regardless of its interface, handles fees-on-transfer, and guarantees the open
note is credited with exactly the tokens the pool can actually pull.

## Things to notice

- **The AMM is pinned at deployment** - `amm_address` and the swap `selector` are
  constructor parameters, so a deployed helper is a fixed, auditable route.
- **`call_contract_syscall`** invokes the AMM generically; an AMM revert
  propagates and aborts the whole pool transaction - no funds move.
- **Overflow guard** - the delta is `u256 → u128` converted with an explicit
  error; a manipulated token cannot smuggle an oversized amount into a note.
- **`ZERO_OUT_AMOUNT` guard** - a swap that returns nothing reverts instead of
  crediting an empty note.
- **The trader is never on-chain** - observers see pool → helper → AMM → helper.
  The open note's owner stays hidden.

Next: the same pattern pointed at a real lending protocol - the Vesu helper.

---

