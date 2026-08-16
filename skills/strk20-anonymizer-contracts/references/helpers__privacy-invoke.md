# Anonymizer Contract Anatomy

Source: https://strk20-by-example.org/helpers/privacy-invoke

> The privacy_invoke pattern - how the pool calls external contracts and credits open notes

Anonymizer contracts (also called **helper contracts**) are how private funds
interact with the outside world - DEXs, lending vaults, escrows - without
revealing who is behind the interaction.

The pattern is a sandwich, executed atomically in one transaction:

```
withdraw from pool  →  helper does something  →  deposit result to an open note
```

1. The pool **withdraws** input tokens to the helper (a plain public transfer -
   observers see the pool paid the helper, not who initiated it).
2. The pool calls the helper's `privacy_invoke` entry point via the protocol's
   `INVOKE_SELECTOR`.
3. The helper does its work, approves the pool to pull the output tokens, and
   **returns a `Span<OpenNoteDeposit>`** - instructions telling the pool which
   open notes to credit with which tokens and amounts.

The output lands in an **open note**: its amount is public (it was measured
on-chain, so it could not be fixed at proof time), but its owner is still hidden.

## The contract every helper must satisfy

The pool deserializes your calldata into `privacy_invoke`'s parameters - you are
free to design the signature after the first `operation`-style arguments - and it
deserializes your return value as `Span<OpenNoteDeposit>`:

```cairo
/// From privacy::objects
pub struct OpenNoteDeposit {
    /// The identifier of the open note to deposit to.
    pub note_id: felt252,
    /// The ERC20 token contract to deposit.
    pub token: ContractAddress,
    /// The amount of tokens to deposit.
    pub amount: u128,
}
```

Here is the smallest possible helper - it simply echoes the deposit instructions
it is given back to the pool:

```cairo
// Adapted from starknet-privacy packages/privacy/src/tests/mock_invoke_returns.cairo
// (Apache-2.0, StarkWare). The smallest possible anonymizer contract: it echoes the
// deposit instructions it is given back to the privacy pool.
use privacy::objects::OpenNoteDeposit;

#[starknet::interface]
pub trait IEchoHelper<T> {
    /// The entry point every anonymizer contract must expose.
    /// The privacy pool calls it via the `INVOKE_SELECTOR` during `InvokeExternal`.
    /// Calldata after the selector is deserialized into this function's parameters;
    /// the return value tells the pool which open notes to credit.
    fn privacy_invoke(ref self: T, deposits: Span<OpenNoteDeposit>) -> Span<OpenNoteDeposit>;
}

#[starknet::contract]
pub mod EchoHelper {
    use privacy::objects::OpenNoteDeposit;
    use super::IEchoHelper;

    #[storage]
    struct Storage {}

    #[constructor]
    fn constructor(ref self: ContractState) {}

    #[abi(embed_v0)]
    pub impl EchoHelperImpl of IEchoHelper<ContractState> {
        fn privacy_invoke(
            ref self: ContractState, deposits: Span<OpenNoteDeposit>,
        ) -> Span<OpenNoteDeposit> {
            deposits
        }
    }
}

```

Useless in production, but it shows the full contract surface: one entry point,
calldata in, `Span<OpenNoteDeposit>` out.

## Rules of the pattern

- **Return exactly a `Span<OpenNoteDeposit>`** - returning anything else (or
  trailing garbage) makes the pool reject the call.
- **Approve, don't transfer** - the helper approves the pool to pull the output;
  the pool executes the pull itself when applying the deposits.
- **An empty span is valid** - it means "credit nothing" for a step that should
  not release funds yet, such as a stateful helper parking funds until a later
  claim (see [Escrow](/helpers/escrow)).
- **Measure output by balance delta** - real helpers record the output token
  balance before and after the external call, so the credited amount is exactly
  what arrived, whatever the external protocol did.
- **One `invoke` per transaction** - the protocol allows at most one external
  invoke per pool transaction.

The next two pages build real helpers on this skeleton: a DEX swap and a Vesu
lending integration. To call one of them from a dapp, see
[Private DeFi End to End](/starknet-wallet-api/private-defi).

For a helper pair that crosses chains rather than protocols, read the
`OutboundAnonymizer` and `InboundAnonymizer` contracts in
[starkware-libs/privacy-bridge](https://github.com/starkware-libs/privacy-bridge):
they move USDC between the pool and EVM chains over Circle's CCTP, and the
inbound side pairs `privacy_invoke` with the pool's `privacy_compute` mechanism
so the attested cross-chain message and the private note are bound in a single
transaction.

---

