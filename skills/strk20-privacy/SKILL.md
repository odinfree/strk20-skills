---
name: strk20-privacy
description: Router and mental model for STRK20, the Starknet privacy pool. Use when choosing an integration route, answering questions about how STRK20 works (notes, nullifiers, viewing keys, channels, actions, proofs, deposit screening), stating what is hidden vs public, handling compliance and auditing questions, or mapping the ecosystem (shadow accounts, formerly private sub-accounts, the EVM Privacy Bridge, starter kit, RFPs, incubator, brand kit). Implementation work fires the sibling skills directly, strk20-wallet-api for private dapps in TS/React, strk20-anonymizer-contracts for Cairo helpers, strk20-privacy-sdk for wallets and key-holding backends.
---

# STRK20, Starknet privacy: router and mental model

STRK20 is a live-on-mainnet, note-based (UTXO) privacy pool for any ERC-20 on
Starknet. It runs as a contract on Starknet itself, on existing wallets and
existing liquidity, with a built-in compliance path. Unlike a fixed-denomination
mixer, notes carry arbitrary amounts and change is handled automatically. Users
shield tokens into the pool as encrypted notes, transact privately with onchain
STARK-proof verification, and unshield when they want transparency.

Full doc pages sit verbatim in `references/`. The sections below are a
condensed map. When a detail is load-bearing (an address, a version, an API
shape), open the reference page.

## Pick the route first

| Goal | Route | Skill |
| --- | --- | --- |
| Private dapp (DeFi, consumer, games) on top of users' wallets | Starknet Wallet API, plus an anonymizer contract for protocol-specific DeFi | `strk20-wallet-api` |
| The Cairo adapter a private DeFi flow calls | Anonymizer contract (`privacy_invoke`) | `strk20-anonymizer-contracts` |
| A privacy wallet, or a backend holding its own keys | Privacy SDK (`createPrivateTransfers`) | `strk20-privacy-sdk` |
| Embedded-wallet or AA product (Privy, Cartridge, chipi, cavos, Dynamic) | These manage user keys and are not privacy-enabled today. Treat the product as the key-holder and take the SDK route | `strk20-privacy-sdk` |
| Hide the main-wallet link during account-based app activity | Shadow accounts, called private sub-accounts before SDK RC.5. SDK route shipped, Wallet API route pending | `strk20-privacy-sdk` |
| Fund from or withdraw to an EVM wallet (USDC) | Privacy Bridge over Circle CCTP | see Ecosystem below |
| Operate proof generation yourself | Prover backend, screening still applies | `strk20-privacy-sdk` |

Rules of thumb from the docs. Start with the narrowest surface that keeps user
keys in the right place. Wallet API first for user-facing dapps. Never ask a
normal dapp user for their viewing key. For private DeFi, expect both a Wallet
API flow and an app-specific anonymizer contract, and check for a first-party
private path before routing anyone to an anonymizer: AVNU ships private swaps,
so that flow needs no Cairo of your own.

## Map the trust boundary before coding

For the selected route, state who holds the signing key and viewing key, who
discovers notes, who constructs the private action, who proves it, and who
submits it. Name the wallet, RPC, relayer, prover, screening service, and app
operators that can observe the request. End with a hidden-versus-visible table
and list the wallet versions, package versions, addresses, audits, and network
assumptions that still need live verification.

## The mental model, one screen

- **Note**: an immutable record of (owner, token, u128 amount), stored
  encrypted. UTXO semantics, spent whole, change comes back as a new note.
  **Open notes** skip amount encryption (protocol salt `OPEN_NOTE_SALT` = 1,
  encrypted notes use salt ≥ 2) so a DeFi output amount can be filled in after
  proving.
- **Nullifier**: a Poseidon hash bound to the note and the owner's private
  viewing key, published on spend. Deterministic, unique, unlinkable. The
  sender cannot compute it, so senders cannot watch for their payment being
  spent.
- **Viewing keypair** `K = k·G` on the STARK curve, registered once via
  `SetViewingKey` and treated as immutable. Registration is a prerequisite:
  both sender and recipient must be registered before a private transfer, and
  only the recipient can register themselves (wallets do it on first use).
  Note data is hidden with domain-separated Poseidon masking, channel secrets
  come from ephemeral ECDH, and at registration `k` is also encrypted to the
  auditor's public key (the compliance escrow).
- **Channels** are directional sender-to-recipient lanes with per-token
  subchannels and dense, WriteOnce note indices. Recipients discover funds by
  scanning only their own channels, so cost scales with your own activity, not
  pool volume. A deposit is a channel from yourself to yourself.
- **Transactions** are batches of actions in fixed phases 0 to 7:
  `SetViewingKey`, `OpenChannel`, `OpenSubchannel`, `Deposit`, `UseNote`,
  `CreateEncNote`/`CreateOpenNote`, `Withdraw`, `InvokeExternal`/
  `ComputeAndInvoke` (phase 7 jointly limited to at most one). Per-token
  temporary balance may never go negative and must end exactly zero.
- **Proofs**: the transaction executes in a virtual Starknet environment
  anchored to a recent block, then Stwo generates a STARK proof (~29 s on a
  12-core / 46 GiB machine, hardware-dependent). Onchain checks before
  applying: program variant (`VIRTUAL_SNOS`), anchor within
  `proof_validity_blocks` of the tip (default 450 ≈ 15 min, governance-set),
  and the proven message hash must match the submitted actions.
- **Deposit screening**: FPI screens the shielding address and signs every
  deposit, and the pool verifies that signature onchain. Protocol-level since
  the v0.14.3 upgrade, so it applies on every route, self-hosted provers
  included.

## Hidden vs visible. Always be explicit

Hidden inside the pool: sender, receiver, token, amount, which notes were
spent. Visible to everyone: registration events, deposits (depositor, token,
amount), withdrawals (recipient, token, amount), published nullifiers
(unlinkable without a viewing key), open-note token and amount in plaintext,
and timing. A paymaster can decouple the submitting address from the user.

Per the official agent-skill repo: never attribute pool activity to a
transaction's sender. Private transactions are relayed, so the sender is the
relayer's account for every user. Read per-user activity from the pool's
`Deposit` event (first indexed key), never from the transaction envelope.

Known limitations the docs state outright. Repeat them in anything you build
or write:

- Channel-open linkability. Opening a channel and moving funds in the same
  transaction or in tight succession can link a recipient to public activity.
  Spread setup and movement over time.
- Distinctive amounts or rapid in-and-out patterns shrink the anonymity set.
- The edges are public by design. Only movement inside the pool is encrypted.

## Compliance model (get this exactly right)

- Screening at the door: every deposit is FPI-screened and
  signature-verified onchain. No proving route bypasses it.
- Selective disclosure after the fact: the user's private viewing key is
  escrowed to the auditor's public key at registration, using the same
  ephemeral ECDH scheme as channels. The auditor key is set by governance and
  supports threshold keys. Disclosure targets only users under a lawful
  request. There is no bulk-surveillance mode.
- A viewing key can read, never spend. Auditor-key compromise would break
  confidentiality, never custody.
- For public copy, the framing is "private by default, disclosable when
  required". Do not call the escrow a backdoor, and do not oversell. The
  edges (deposits, withdrawals, timing) are public.

## Route status (snapshot 2026-08-16, verify before relying on it)

- Wallet API version 0.10.3. The official integration skill uses Ready as the
  tested dapp baseline and still marks Xverse's dapp-facing Wallet API in
  progress. Product docs also list Xverse for user privacy flows, so detect
  the connected wallet's capability instead of inferring it from the brand.
  Braavos and embedded-wallet providers are not privacy-enabled in the cited
  integration sources.
- Shadow accounts, called private sub-accounts in RC.4 and older docs, hide the
  main-wallet link during account activity. Privacy SDK `0.14.3-rc.5` renamed
  the builder to `build().shadowAccounts(dappName)`, the config key to
  `shadowAccountAnonymizerAddress`, and the Cairo package to
  `shadow_account_anonymizer`. The renamed views and event use new selectors,
  so RC.5 requires the upgraded anonymizer and an indexer spanning the upgrade
  must match both event keys. The Wallet API route remains pending. No shadow
  account method exists in `@starknet-io/types-js` 0.10.3 or starknet.js, so
  dapps relying on the user's wallet must wait. This is still a release
  candidate. Confirm its current API and audit readiness before shipping.
- Privacy Bridge (EVM USDC to and from the pool over Circle CCTP) is open
  source and early. Read its README before planning around it.
- The docs' own launch checklist: verify wallet support, API versions,
  contract addresses, and compliance assumptions before launch.

## Ecosystem

- Docs: https://strk20-by-example.org (agent-readable at `/llms.txt` and
  `/llms-full.txt`, any page as raw Markdown by appending `.md`). Product
  site: https://strk20.starknet.io.
- Code: `starkware-libs/starknet-privacy` (Apache-2.0 monorepo with the
  TypeScript SDK, pool contracts, and anonymizer reference packages),
  `starkware-libs/privacy-bridge`, `Akashneelesh/strk20-starter-kit` (Next.js
  starter with the Wallet API pre-wired), `Akashneelesh/awesome-strk20`.
- Official integration agent skill: `npx skills add starkience/strk20-agent-skills`.
  It scans a repo, interviews the developer, picks a route, writes
  `STRK20_INTEGRATION_PLAN.md`, and executes on approval. It never writes
  Cairo and never touches key material.
- Request for Startups: https://strk20.starknet.io/rfp (26 open problem
  statements). Incubator: https://proof.starknet.io. Brand kit:
  https://strk20.starknet.io/brand.md plus `/brand/tokens.json`.

## Refresh fast-moving facts

Run the bundled checker from this skill directory before quoting a version,
package path, Wallet API status, or pool address:

```sh
python3 scripts/check_freshness.py
```

Add `--quick` to skip the 30 per-page liveness requests. Exit code 1 means a
checked fact moved. Exit code 2 means a lookup failed and the result is
incomplete. The checker is adapted from the official integration skill. It
cannot verify wallet rollout or contract audit status, so check those sources
manually.

## references/

- `what-is-strk20.md`, intro, lifecycle, building blocks
- `builder-privacy-overview.md`, decision guide, all surfaces, rules of thumb
- `overview.md`, condensed route chooser plus starter kit
- `notes-and-nullifiers.md`, UTXO model, open notes, note_id and nullifier derivations
- `viewing-keys.md`, masking, ECDH, auditor escrow
- `channels-and-subchannels.md`, channels, subchannels, discovery scan
- `actions-and-proofs.md`, phase table, balance invariant, proving pipeline
- `compliance.md`, screening, escrowed key, visibility table, limitations
- `agent-skill.md`, the official integration agent skill
