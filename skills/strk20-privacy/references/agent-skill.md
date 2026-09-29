# Agent Skill

Source: https://strk20-by-example.org/agent-skill

> Give your coding agent working knowledge of STRK20 - concepts, Wallet API, anonymizer contracts, and the Privacy SDK

Everything on this site can be loaded into a coding agent. The STRK20 skills
give Claude Code, Codex, Cursor, and other agents that read the skills format
the working knowledge behind these pages - how the pool works, how a dapp asks
a wallet to act, how to write the Cairo adapter, and how to drive the SDK:

```sh
npx skills add welttowelt/strk20-skills
```

Then work normally. The skills fire on their own when a task touches STRK20 -
you do not invoke them by name.

### The four skills

- **`strk20-privacy`** - the router and mental model. Notes, nullifiers,
  viewing keys, channels, actions and proofs, deposit screening, what is
  hidden versus public, compliance and auditing, and the ecosystem map. Fires
  when an agent is choosing an integration route or answering how STRK20
  works.
- **`strk20-wallet-api`** - private dapps in TypeScript or React through the
  Starknet Wallet API: shield and unshield, private transfers, shielded
  balances, private DeFi calls, and AVNU private swaps. The recommended route
  for most dapps, where the wallet keeps the viewing keys.
- **`strk20-anonymizer-contracts`** - the Cairo side of private DeFi: the
  `privacy_invoke` entry point the pool calls, `OpenNoteDeposit` returns, the
  balance-delta idiom, and the swap, Vesu lending, and escrow patterns.
- **`strk20-privacy-sdk`** - for teams building the wallet itself, or backends
  that hold their own keys: `createPrivateTransfers` wiring, register, deposit,
  transfer, withdraw, multi-op batches, shadow accounts, note discovery, and
  proving configuration.

Each skill is a distilled `SKILL.md` plus the relevant pages from this site
bundled verbatim under `references/`, so the agent opens the source instead of
reconstructing it from memory. Codex metadata ships under `agents/openai.yaml`.

### What they never do

- **Generate or edit Cairo contracts for you.** An anonymizer contract stays
  your team's code to write, review, and audit; the skills carry the reference
  patterns and the public packages. Learn more about Cairo at
  [cairo-lang.org](https://www.cairo-lang.org/) and about anonymizer contracts
  in [Anonymizer Contract Anatomy](/helpers/privacy-invoke).
- **Touch key material.** Viewing keys, private keys, and secrets belong in
  env vars, never in files, and never in a prompt.

### Check anything load-bearing

The skills bundle a snapshot, and versions, wallet support, and feature status
all move. Verify against this site before you rely on a version pin or a
support claim.

### This site is agent-readable

Agents don't need to parse the app bundle: every page on this site is mirrored
as raw Markdown. Start from [/llms.txt](/llms.txt) (index of all pages as `.md`
URLs) or fetch the whole site in one file at [/llms-full.txt](/llms-full.txt).

Source, docs, and issues:
[github.com/welttowelt/strk20-skills](https://github.com/welttowelt/strk20-skills)
(Apache 2.0).
