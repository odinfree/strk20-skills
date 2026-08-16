# Tip Jar

Source: https://strk20-by-example.org/app/tip-jar

> Add privacy to an app that already has users, liquidity, and activity

The **Tip Jar** is a worked example of the
[Starknet Wallet API](/starknet-wallet-api/overview) route applied to an app that
already exists. It starts as an ordinary public tip jar deployed on Starknet
mainnet, then gains a private tipping path beside the public one. You can **add
privacy to an app with existing users, liquidity, and activity**, which is the
key advantage of STRK20 over building a separate private app.

Use it as a reference when you have a live app and want to see which files
change. The deployed contract is not one of them. The app itself runs at
[strk20-tipjar.vercel.app](https://strk20-tipjar.vercel.app).

## What the two paths look like

A tip jar has one onchain action: tip the creator.

The **public path** calls a `TipJar` contract, which forwards the token and emits
a `Tipped` event. Who paid whom, how much, and when are permanently visible.

The **private path** calls no contract at all:

1. **Shield** - the tipper deposits tokens into the pool, earlier and on its own.
2. **Wait** - the resulting note matures after roughly 10 blocks.
3. **Swap** (optional) - a private swap turns any shielded token into STRK inside
   the pool.
4. **Private transfer** - the tipper pays the creator, with no public leg.

Both paths deliver the same value to the creator. The private one leaves no
public link between the two.

The snippets below need `starknet@^10.4.0` — STRK20 support is on the npm `next`
tag, and `latest` (10.0.x) has none of it.

## How it works in code

The private tip is a single action handed to the wallet:

```ts
const actions: STRK20_ACTION[] = [
  { type: "transfer", token: strkAddress, amount, recipient },
]
const { transaction_hash } = await account.strk20InvokeTransaction(actions)
```

There is no contract call, no event, and no approval step. The wallet holds the
keys, discovers the notes, generates the proof, and submits.

Shielding is the same call with a different action:

```ts
const actions: STRK20_ACTION[] = [{ type: "deposit", token: tokenAddress, amount }]
```

Capability detection reads no private state:

```ts
const versions = await walletV6.supportedWalletApi(wallet)
const supported = versions.some((v) => compareVersions(v, "0.10.3") >= 0)
```

## Shield separately from the transfer

Shielding is its own step, done ahead of time — and that is what makes the tip
unlinkable. A deposit into the pool is public and names the depositor, while a
private transfer has no public leg at all. Because the two are separate
transactions, nothing on-chain ties the deposit to the payment, and no observer
can connect the tipper to the creator.

Shield ahead of time, tip later. The note matures in the meantime, and the
transfer that follows leaves no public trace.

## Verified onchain

The creator's wallet received four private transfers totalling 42 STRK while the
jar's public counter stayed at 3 tips and 3 STRK. The `TipJar` contract was not
modified, which the repository leaves checkable through two tags:

```sh
git diff --stat v1-public v2-private -- contracts/src/tipjar.cairo
```

Full walkthrough, including the integration log and deployment record:
[TUTORIAL.md](https://github.com/starkience/strk20-tipjar-example/blob/main/TUTORIAL.md)
(MIT).

## Read next

- [Starknet Wallet API overview](/starknet-wallet-api/overview)
- [starknet.js](/starknet-wallet-api/starknet-js)
- [Agent Skill](/agent-skill)
- [Anonymizer Contract Anatomy](/helpers/privacy-invoke)

---

