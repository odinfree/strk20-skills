# Deployed Contract Addresses

Source: https://strk20-by-example.org/contract-addresses

> Current Starknet Mainnet and Sepolia addresses for the STRK20 privacy pool, shadow accounts, and deployed anonymizer contracts

These are the public STRK20 pool and anonymizer deployments checked against
their current package configuration or integration documentation on **29
September 2026**. Use the address for the network your wallet or backend is
connected to; Mainnet and Sepolia contracts are not interchangeable.

## Starknet Mainnet

| Contract                                        | Purpose                                                       | Address                                                                                                                                                                    |
| ----------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| STRK20 Privacy Pool                             | Holds shielded ERC-20 notes and verifies private actions      | [`0x040337b1af3c663e86e333bab5a4b28da8d4652a15a69beee2b677776ffe812a`](https://voyager.online/contract/0x040337b1af3c663e86e333bab5a4b28da8d4652a15a69beee2b677776ffe812a) |
| `ShadowAccountAnonymizer`                       | Deploys and drives per-dapp shadow accounts through the pool  | [`0x04f33230dc57855c6e7eabe66dfa0fde82c5458fd0e54827cdb7cb4c474888a7`](https://voyager.online/contract/0x04f33230dc57855c6e7eabe66dfa0fde82c5458fd0e54827cdb7cb4c474888a7) |
| AVNU `PrivacySwapHelper`                        | Executes private AVNU swaps                                   | [`0x0426dcd1ab5fa2f852f138d07cb37708b00a4db999677fe2d0c9a440702dbe5e`](https://voyager.online/contract/0x0426dcd1ab5fa2f852f138d07cb37708b00a4db999677fe2d0c9a440702dbe5e) |
| Privacy Bridge / OFFMARKET `OutboundAnonymizer` | Moves shielded USDC from the pool into the outbound CCTP flow | [`0x009067f35d2cab3cb933f3d78793660402026f8fa31e041ca2cab4a8e9a49092`](https://voyager.online/contract/0x009067f35d2cab3cb933f3d78793660402026f8fa31e041ca2cab4a8e9a49092) |
| Privacy Bridge / OFFMARKET `InboundAnonymizer`  | Binds returning CCTP funds to a private note                  | [`0x03a7e7f34e530f8ec00b1ff7eaca90a136311d9da7cb17a73203f813b56c86cb`](https://voyager.online/contract/0x03a7e7f34e530f8ec00b1ff7eaca90a136311d9da7cb17a73203f813b56c86cb) |
| Endur `EndurDepositAnonymizer`                  | Deposits into Endur from shielded funds                       | [`0x030dee638065962eb3642ca54aa48e9e2cd98536bc90b64b99bb306c1db30698`](https://voyager.online/contract/0x030dee638065962eb3642ca54aa48e9e2cd98536bc90b64b99bb306c1db30698) |

AVNU returns its current `executorAddress` when a private quote is built. Use
that response at runtime rather than assuming the address above will never
change.

## Starknet Sepolia

| Contract                                        | Purpose                                      | Address                                                                                                                                                                            |
| ----------------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| STRK20 Privacy Pool                             | Testnet pool for SDK and integration testing | [`0x0254a6b2997ef52e9f830ce1f543f6b29768295e8d17e2267d672c552cfe0d91`](https://sepolia.voyager.online/contract/0x0254a6b2997ef52e9f830ce1f543f6b29768295e8d17e2267d672c552cfe0d91) |
| `ShadowAccountAnonymizer`                       | Testnet shadow-account infrastructure        | [`0x010a2285310c107c731d997afc147afb7495daff6397c2d242133d9fe8d9b147`](https://sepolia.voyager.online/contract/0x010a2285310c107c731d997afc147afb7495daff6397c2d242133d9fe8d9b147) |
| Privacy Bridge / OFFMARKET `OutboundAnonymizer` | Testnet outbound CCTP helper                 | [`0x05b85f2ae4d47c1e661533d5832fe3e4afd4c6a9b52e54b7f873a00c9b285f4e`](https://sepolia.voyager.online/contract/0x05b85f2ae4d47c1e661533d5832fe3e4afd4c6a9b52e54b7f873a00c9b285f4e) |
| Privacy Bridge / OFFMARKET `InboundAnonymizer`  | Testnet inbound CCTP helper                  | [`0x00d2a07c657d8c70f6eeddb7c8125e39b0955a40a608f63ca8a88d3ebbf72117`](https://sepolia.voyager.online/contract/0x00d2a07c657d8c70f6eeddb7c8125e39b0955a40a608f63ca8a88d3ebbf72117) |

No public Sepolia deployment was confirmed for the AVNU or Endur helpers, so
their Mainnet addresses must not be reused on Sepolia.

## What is not in the list

`EkuboSwapAnonymizer` and `VesuLendingAnonymizer` are reference packages in the
[starknet-privacy monorepo](https://github.com/starkware-libs/starknet-privacy),
but that repository does not currently publish canonical Mainnet or Sepolia
deployment addresses for them. The swap helper and escrow elsewhere on this
site are worked examples, not public deployments. Devnet and end-to-end test
addresses are intentionally excluded.

## Sources and verification

- The pool addresses are exported by
  [`@avnu/avnu-sdk`](https://www.npmjs.com/package/@avnu/avnu-sdk) as
  `PRIVACY_POOL_ADDRESS` and `SEPOLIA_PRIVACY_POOL_ADDRESS`.
- The pool and Privacy Bridge defaults are pinned per network in the
  [bridge-core configuration](https://github.com/starkware-libs/privacy-bridge/blob/main/packages/bridge-core/src/core/config.ts).
- The shadow-account deployments are published in the current
  [starknet.js WalletAccount guide](https://starknet-js.com/docs/guides/account/walletAccount/#address-of-a-shadow-account).
- The previously listed helper addresses were checked against their network's
  on-chain classes. Their ABIs identify `PrivacySwapHelperImpl`,
  `OutboundAnonymizerImpl`, `InboundAnonymizerImpl`, and
  `EndurDepositAnonymizerImpl` respectively.

Contract addresses and implementations can change. Re-check this page and the
linked explorer before shipping a production integration.
