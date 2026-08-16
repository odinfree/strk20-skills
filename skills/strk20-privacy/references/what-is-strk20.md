# What is STRK20?

Source: https://strk20-by-example.org/what-is-strk20

> An introduction to Starknet Privacy - confidential token transfers on a public chain

The foundation for all privacy on Starknet: the layer everything above reads from
and writes to. STRK20 brings shielded balances, private transfers, and private
DeFi to any ERC-20 on Starknet, built on the wallets and liquidity that already
exist rather than a separate ecosystem.

### How it works at a high level

- **Note-based pool: not a mixer.** Shielding deposits an ERC-20 into the pool,
  where the balance is held as an encrypted note (a UTXO). Private transfers
  spend existing notes and generate new ones.
- **Registration first:** An account must register in the pool (set a viewing key)
  before it can hold or receive private balances; both sender and recipient must
  be registered before private transfers between them. Wallets handle registration
  on first use, and channel setup between counterparties is automatic after that.
- **Onchain proof verification:** Every private transaction carries a
  zero-knowledge (STARK) proof confirming the spent notes exist, belong to the
  spender, haven't been double-spent, and that value is conserved. Starknet
  verifies the proof in-protocol before updating the pool's state.
- **Hidden vs. visible:** Inside the pool, the sender, receiver, amounts, token
  type, and which notes were spent are all private. What stays visible: deposit
  and withdrawal amounts (the public ERC-20 legs), that someone is interacting
  with the pool, and timing. A Paymaster can decouple the submitter's address
  from the transaction.
- **Shielding:** Users shield assets when they want privacy and unshield them when
  transparency is required, moving value between public and confidential states on
  the same underlying token.

## The lifecycle: public → private → public

1. **Deposit** - move public ERC-20 tokens into the pool. The deposit itself is
   visible on-chain (depositor and amount), but the resulting note is encrypted.
2. **Private transfers** - transfer value inside the pool by spending notes and
   creating new ones. Nobody watching the chain can tell who paid whom, or how much.
3. **DeFi** - if your flow calls for it, notes can fund DeFi actions through an
   anonymizer contract, with results credited back as private notes. This leg
   is confidential rather than fully private: the link to the user is hidden,
   but the app-side action and amounts can still be public.
4. **Withdraw** - move tokens back out of the pool to a public address.

**Private sub-accounts** widen the DeFi leg: account-based flows such as
borrowing and staking run through real Starknet accounts that carry no public
onchain link back to the user's main wallet, and using fresh sub-accounts per
app fragments the trail further. The same caveat applies - app-side activity
and amounts can still be public. The SDK route ships as of Privacy SDK
`0.14.3-rc.4`; the Wallet API route is still pending, so dapps relying on the
user's wallet cannot use them yet.

## What makes it different

- **Native to Starknet** - no separate chain or bridge. It runs as a contract on
  Starknet and composes with existing accounts and DeFi.
- **Variable amounts, reusable notes** - unlike fixed-denomination mixers, notes
  carry arbitrary amounts and change is handled automatically.
- **Scalable discovery** - recipients find their incoming funds by scanning only
  their own channels, so cost scales with your activity, not total pool volume.
- **Selective disclosure** - at registration every user encrypts their private
  viewing key to an auditor's public key, so the system can disclose the
  information needed to respond to a legitimate regulatory request without
  exposing unrelated users.

## The building blocks

| Concept             | What it is                                                                           |
| ------------------- | ------------------------------------------------------------------------------------ |
| Note                | Immutable record of ownership of an amount of a token                                |
| Nullifier           | One-time value revealed when spending a note (prevents double-spend)                 |
| Viewing key         | Keypair used to encrypt/decrypt note data and derive nullifiers                      |
| Channel             | Unidirectional sender → recipient lane where notes are stored                        |
| Anonymizer contract | Small adapter that lets pool funds interact with external DeFi                       |
| Deposit screening   | Every deposit is screened and signed by FPI; the pool verifies the signature onchain |

Each of these has its own page in the Concepts section - read them in order and
you will have the full mental model.

## Who this site is for

- **Private dapp developers** integrating with existing wallets - see the
  Starknet Wallet API section.
- **Core dapp builders** writing private DeFi integrations - see the
  Anonymizer Contracts section.
- **Wallet builders** implementing privacy flows directly - see Build Privacy
  Wallets.
- **Anyone** who wants to understand how private payments work on Starknet - start
  with the Concepts pages.

Have a coding agent? It can run this integration for you - see
[Agent Skill](/agent-skill).

---

