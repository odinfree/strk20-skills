# strk20-skills

Agent skills for building on [STRK20](https://strk20.starknet.io), the privacy
pool on Starknet. Five skills give a coding agent the working knowledge: how
the pool works, how a dapp asks a privacy-enabled wallet to act, how to write
the Cairo adapter for private DeFi, how to drive the low-level SDK, and how
to operate a local prover.

The integration skills include relevant upstream source pages bundled under
`references/`, so the agent can open the source instead of reconstructing it
from memory. The local-prover skill includes a runnable community starter.
Skill bodies label source status and community examples. Each skill also
includes Codex UI metadata under `agents/openai.yaml`.

## Run your own prover

**[Open the local-prover guide and Docker starter](skills/strk20-local-prover/assets/local-prover/README.md)**
for Linux, Windows/WSL2, or a Mac connected to an amd64 host. Fork this repo,
use your own RPC endpoint, and follow the checks before connecting a wallet.
The starter pins the official image, binds to localhost, and includes redacted
diagnostics. It does not submit transactions.

**DYOR:** this is experimental, unaudited community tooling, provided as-is.
Review current upstream releases, audits, privacy limits and fees; start on
testnet and take responsibility for your credentials and funds. Read the
[full responsibility notice](skills/strk20-local-prover/assets/local-prover/README.md#dyor-and-responsibility).

## Install

For Claude Code, Cursor, Codex, and other agents that read the skills format:

```sh
npx skills add odinfree/strk20-skills
```

Manual install for Claude Code, global:

```sh
git clone https://github.com/odinfree/strk20-skills
mkdir -p ~/.claude/skills
cp -R strk20-skills/skills/* ~/.claude/skills/
```

Manual install for Codex, global:

```sh
git clone https://github.com/odinfree/strk20-skills
mkdir -p ~/.agents/skills
cp -R strk20-skills/skills/* ~/.agents/skills/
```

For one project only, copy into the repo's `.claude/skills/` or
`.agents/skills/` directory instead. The `.agents/skills` paths follow the
[official Codex skill locations](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).

## The skills

| Skill | Fires when | Bundled references |
| --- | --- | --- |
| `strk20-privacy` | Route choice, pool concepts, hidden vs public, compliance questions | 10 pages: concepts, builder overview, deployments, compliance, the official agent skill |
| `strk20-wallet-api` | Private dapps in TypeScript or React, acting through the user's wallet | 6 pages: Wallet API, stable shadow accounts, private DeFi, AVNU swaps |
| `strk20-anonymizer-contracts` | Cairo `privacy_invoke` helper contracts for private DeFi | 4 pages: anatomy, swap helper, Vesu lending, escrow |
| `strk20-privacy-sdk` | Privacy wallets and backends holding their own keys, SDK debugging | 11 SDK pages plus the upstream SDK README |
| `strk20-local-prover` | Run an official proving service locally or through an SSH tunnel | Community Docker starter, platform guide, diagnostics and tests |

## Contributing

If you hit an STRK20 edge case that this repository misses, send the fix back.
Pull requests are welcome for new flows, corrected moving facts, sharper failure
tables, and clearer skill routing.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before editing. Files under
`references/` are verbatim upstream snapshots. Refresh them from their source
instead of rewriting them.

## What they carry

A sample of the load-bearing details, so you know the level:

- The version boundary: core STRK20 support starts at starknet.js 10.4.0;
  stable shadow accounts require starknet.js 10.8.0 and Wallet API 0.10.4.
- A shield needs an ERC-20 approve from the token owner. A paymaster can carry
  that signed outside execution in the same transaction as the deposit.
- The SDK submission tail: `provingBlockId = currentBlock - 10`, conditional
  `proofFacts` spread, `tip: 0n`.
- The stable shadow-account Wallet API route, including deterministic nonce
  scoping, canonical deployments, collection policies, the public-state
  privacy boundary, and the earlier event-key migration warning.
- The proof base must include every prior onchain state change the proof reads.
  With `provingBlockId = head - 10`, wait until `head - 10 > receiptBlock`
  before proving against a deployment or funding transfer.
- The anonymizer balance-delta idiom, and why helpers approve rather than
  transfer.
- What stays public on every route: deposits, withdrawals, open-note amounts,
  timing.
- A bundled freshness checker for npm tags, monorepo and shadow-account test
  paths, stable Wallet API version and action, canonical pool and shadow
  anonymizer addresses, and the current tutorial page set.

## Relationship to the official documentation

The [STRK20 Agent Skill page](https://strk20-by-example.org/agent-skill)
publishes this skill collection as the agent-readable knowledge layer for the
official builder documentation. The bundled references remain source snapshots;
the concise `SKILL.md` files add routing, failure modes, and operational guidance.

## Freshness

Built from the agent-readable export of
[strk20-by-example.org](https://strk20-by-example.org) (shadow-account refresh
2026-09-29),
with a few facts drawn from the official agent-skill repo and marked as such
in the text. Versions, wallet support, and feature status change. Verify
anything load-bearing against the live docs: every page is raw Markdown when
you append `.md` to its URL, and the whole site is one file at
[`/llms-full.txt`](https://strk20-by-example.org/llms-full.txt).

The bundled `skills/strk20-privacy/references/agent-skill.md` is a verbatim
snapshot of that page, with a source header added for provenance.

The route-specific skills record the exact package snapshot checked on
2026-09-29. The Privacy SDK source was `0.14.3-rc.8`, while the package still
returned 404 on public npmjs. Query the
correct registry when refreshing it. Update and test the starknet.js,
get-starknet, and Wallet API connection stack as one unit.

The shadow-account guides are refreshed from the current Wallet API and SDK
documentation. They distinguish the stable dapp route from the release-candidate
low-level SDK and keep runtime capability checks and the public-state privacy
boundary explicit.

## Sources and license

Original skill prose and configuration in this repository are Apache-2.0.
The bundled by-example documentation remains under its upstream MIT license.
The SDK README and Cairo sources retain their upstream Apache-2.0 terms. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for copyright and license
details. This is a community repository, not an official Starkware project.
