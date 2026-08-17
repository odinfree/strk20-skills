# strk20-skills

Agent skills for building on [STRK20](https://strk20.starknet.io), the privacy
pool on Starknet. Four skills give a coding agent the working knowledge: how
the pool works, how a dapp asks a privacy-enabled wallet to act, how to write
the Cairo adapter for private DeFi, and how to drive the low-level SDK.

Each skill is a distilled `SKILL.md` plus relevant upstream source pages
bundled verbatim under `references/`, so the agent can open the source instead
of reconstructing it from memory. The skill body labels source status and
community examples. Each skill also includes Codex UI metadata under
`agents/openai.yaml`.

## Install

For Claude Code, Cursor, Codex, and other agents that read the skills format:

```sh
npx skills add welttowelt/strk20-skills
```

Manual install for Claude Code, global:

```sh
git clone https://github.com/welttowelt/strk20-skills
mkdir -p ~/.claude/skills
cp -R strk20-skills/skills/* ~/.claude/skills/
```

Manual install for Codex, global:

```sh
git clone https://github.com/welttowelt/strk20-skills
mkdir -p ~/.agents/skills
cp -R strk20-skills/skills/* ~/.agents/skills/
```

For one project only, copy into the repo's `.claude/skills/` or
`.agents/skills/` directory instead. The `.agents/skills` paths follow the
[official Codex skill locations](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).

## The skills

| Skill | Fires when | Bundled references |
| --- | --- | --- |
| `strk20-privacy` | Route choice, pool concepts, hidden vs public, compliance questions | 9 pages: concepts, builder overview, compliance, the official agent skill |
| `strk20-wallet-api` | Private dapps in TypeScript or React, acting through the user's wallet | 6 pages: Wallet API, private DeFi end to end, AVNU swaps, tip-jar example |
| `strk20-anonymizer-contracts` | Cairo `privacy_invoke` helper contracts for private DeFi | 4 pages: anatomy, swap helper, Vesu lending, escrow |
| `strk20-privacy-sdk` | Privacy wallets and backends holding their own keys, SDK debugging | 11 SDK pages plus the upstream SDK README |

## Contributing

If you hit an STRK20 edge case that this repository misses, send the fix back.
Pull requests are welcome for new flows, corrected moving facts, sharper failure
tables, and clearer skill routing.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before editing. Files under
`references/` are verbatim upstream snapshots. Refresh them from their source
instead of rewriting them.

## What they carry

A sample of the load-bearing details, so you know the level:

- The version boundary: STRK20 support starts at starknet.js 10.4.0. A bare
  install still gets the npm `latest` line, which does not carry the API.
- A shield needs an ERC-20 approve, and approve must execute as the token
  owner — which does not force a second transaction, since a paymaster can
  carry it as a signed outside execution.
- The SDK submission tail: `provingBlockId = currentBlock - 10`, conditional
  `proofFacts` spread, `tip: 0n`.
- The RC.5 shadow-account rename, including the new builder, config key,
  Cairo package, and event-key migration warning.
- The proof base must include every prior onchain state change the proof reads.
  With `provingBlockId = head - 10`, wait until `head - 10 > receiptBlock`
  before proving against a deployment, funding transfer, or approval.
- The anonymizer balance-delta idiom, and why helpers approve rather than
  transfer.
- What stays public on every route: deposits, withdrawals, open-note amounts,
  timing.
- A bundled freshness checker for npm tags, monorepo paths, the Wallet API
  development version, the Sepolia pool address, and all 30 tutorial pages.

## Relationship to the official agent skill

The [`STRK20 Integration Agent Skill`](https://strk20-by-example.org/agent-skill),
maintained in
[`starkience/strk20-agent-skills`](https://github.com/starkience/strk20-agent-skills),
is the official integration planner. It scans your repo, interviews you,
writes `STRK20_INTEGRATION_PLAN.md`, and executes it phase by phase. The four
skills here are the knowledge layer underneath: concepts, API surfaces, and
failure tables an agent can pull into any task, planned or not. They compose.
Install both.

## Freshness

Built from the agent-readable export of
[strk20-by-example.org](https://strk20-by-example.org) (snapshot 2026-08-16),
with a few facts drawn from the official agent-skill repo and marked as such
in the text. Versions, wallet support, and feature status change. Verify
anything load-bearing against the live docs: every page is raw Markdown when
you append `.md` to its URL, and the whole site is one file at
[`/llms-full.txt`](https://strk20-by-example.org/llms-full.txt).

The bundled `skills/strk20-privacy/references/agent-skill.md` is a verbatim
snapshot of the STRK20 Integration Agent Skill page, with a source header
added for provenance.

The route-specific skills record the exact package snapshot checked on
2026-08-16. The Privacy SDK's `latest` tag was `0.14.3-rc.5` on GitHub
Packages, while the package still returned 404 on public npmjs. Query the
correct registry when refreshing it. Update and test the starknet.js,
get-starknet, and Wallet API connection stack as one unit.

## Sources and license

Original skill prose and configuration in this repository are Apache-2.0.
The bundled by-example documentation remains under its upstream MIT license.
The SDK README and Cairo sources retain their upstream Apache-2.0 terms. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for copyright and license
details. This is a community repository, not an official Starkware project.
