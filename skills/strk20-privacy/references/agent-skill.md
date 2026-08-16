# Agent Skill

Source: https://strk20-by-example.org/agent-skill

> Let your coding agent plan and build an STRK20 integration for your app

Everything on this site can be done for you by a coding agent. The STRK20
integration skill turns Claude Code, Codex, Cursor, and 14+ other agents into
an integration engineer for the repo they run in:

```sh
npx skills add starkience/strk20-agent-skills
```

Then, inside your project, ask your agent to **"plan STRK20 privacy for this
app."**

### What it does

1. **Scans** your repo - starknet.js version, get-starknet, Cairo contracts,
   backend SDKs - and finds the plug-in points.
2. **Asks** - a short interview: what exactly should be private, which wallets
   your users hold, testnet or mainnet first.
3. **Routes** - Starknet Wallet API via starknet.js (most dapps), anonymizer
   contract + Wallet API (DeFi protocols), Privacy SDK direct (wallets and
   backends holding their own keys), or private sub-accounts (tracked).
4. **Plans** - writes a phased, versioned `STRK20_INTEGRATION_PLAN.md` naming
   your actual files, honest about what is hidden vs. visible.
5. **Executes on your approval** - builds the plan phase by phase, with
   headless checks per phase and a short manual wallet check handed to you at
   every phase boundary. Its chat output links back to the matching pages on
   this site.

### What it never does

- **Generate or edit Cairo contracts.** An anonymizer contract stays your
  team's code to write, review, and audit; the skill points at the public
  reference packages instead. Learn more about Cairo at
  [cairo-lang.org](https://www.cairo-lang.org/) and about anonymizer contracts
  in [Anonymizer Contract Anatomy](/helpers/privacy-invoke).
- **Touch key material.** Viewing keys, private keys, and secrets never land
  in files - env-var placeholders only.
- **Ship to mainnet silently.** Testnet by default; mainnet-affecting changes
  require your explicit confirmation.

### This site is agent-readable

Agents don't need to parse the app bundle: every page on this site is mirrored
as raw Markdown. Start from [/llms.txt](/llms.txt) (index of all pages as `.md`
URLs) or fetch the whole site in one file at [/llms-full.txt](/llms-full.txt).

Source, docs, and issues:
[github.com/starkience/strk20-agent-skills](https://github.com/starkience/strk20-agent-skills)
(Apache 2.0).
