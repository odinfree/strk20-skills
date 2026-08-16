# strk20-skills

Agent skills for building on [STRK20](https://strk20.starknet.io), the privacy
pool on Starknet. Four skills give a coding agent the working knowledge: how
the pool works, how a dapp asks a privacy-enabled wallet to act, how to write
the Cairo adapter for private DeFi, and how to drive the low-level SDK.

Each skill is a distilled `SKILL.md` plus the relevant official documentation
pages bundled verbatim under `references/`, so the agent can open the source
instead of reconstructing it from memory. Each skill also includes Codex UI
metadata under `agents/openai.yaml`.

## Install

For Claude Code, Cursor, Codex, and other agents that read the skills format:

```sh
npx skills add welttowelt/strk20-skills
```

Manual install for Claude Code, global:

```sh
git clone https://github.com/welttowelt/strk20-skills
cp -r strk20-skills/skills/* ~/.claude/skills/
```

Manual install for Codex, global:

```sh
git clone https://github.com/welttowelt/strk20-skills
cp -r strk20-skills/skills/* ~/.codex/skills/
```

For one project only, copy into the repo's `.claude/skills/` or
`.codex/skills/` directory instead.

## The skills

| Skill | Fires when | Bundled references |
| --- | --- | --- |
| `strk20-privacy` | Route choice, pool concepts, hidden vs public, compliance questions | 9 pages: concepts, builder overview, compliance, the official agent skill |
| `strk20-wallet-api` | Private dapps in TypeScript or React, acting through the user's wallet | 6 pages: Wallet API, private DeFi end to end, AVNU swaps, tip-jar example |
| `strk20-anonymizer-contracts` | Cairo `privacy_invoke` helper contracts for private DeFi | 4 pages: anatomy, swap helper, Vesu lending, escrow |
| `strk20-privacy-sdk` | Privacy wallets and backends holding their own keys, SDK debugging | 11 SDK pages plus the upstream SDK README |

## What they carry

A sample of the load-bearing details, so you know the level:

- The version boundary: STRK20 support starts at starknet.js 10.4.0. A bare
  install still gets the npm `latest` line, which does not carry the API.
- A shield is two transactions (ERC-20 approve first), so the wallet prompts
  twice and the UI should say why.
- The SDK submission tail: `provingBlockId = currentBlock - 10`, conditional
  `proofFacts` spread, `tip: 0n`.
- The transparent-state rule: any onchain state a proof reads must be at
  least 10 blocks old at the proof base, which is why `register()` fails on a
  freshly deployed account.
- The anonymizer balance-delta idiom, and why helpers approve rather than
  transfer.
- What stays public on every route: deposits, withdrawals, open-note amounts,
  timing.

## Relationship to the official agent skill

[`starkience/strk20-agent-skills`](https://github.com/starkience/strk20-agent-skills)
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

Live registry check on 2026-08-16: starknet.js `latest` was `10.0.2` and
`next` was `10.7.0`. get-starknet v6 `next` was `6.0.4`. The Privacy SDK
`latest` was `0.14.3-rc.5`, and Wallet API types remained `0.10.3`. Treat the
documented 10.4.0 plus get-starknet 6.0.3 combination as a tested baseline.
If you move to the current `next` packages, update and test the connection
stack as one unit.

## Sources and license

Original skill prose and configuration in this repository are Apache-2.0.
The bundled by-example documentation remains under its upstream MIT license.
The SDK README and Cairo sources retain their upstream Apache-2.0 terms. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for copyright and license
details. This is a community repository, not an official Starkware project.
