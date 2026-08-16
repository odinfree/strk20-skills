# Discovering Notes

Source: https://strk20-by-example.org/sdk/note-discovery

> Scan your channels for unspent notes with discoverNotes and discoverChannels

Discovery scans your channels and decrypts the notes addressed to you. It is
a **query, not a transaction** - no proof, no fee, no submission. Use it to
show the user's private balance and to feed `.inputs(...)`.

Snippets assume `transfers`, `account` and `provider` from
[Getting Started](/sdk/getting-started).

```typescript
const { notes, timestamp } = await transfers.discoverNotes({
  tokens: [BigInt(tokenAddress)], // token filter entries MUST be bigint
})

// notes: AddressMap<Note[]> keyed by BIGINT token address
const tokenNotes = notes.get(BigInt(tokenAddress)) ?? []
const balance = tokenNotes.reduce((sum, note) => sum + note.amount, 0n)
```

## `AddressMap`

The result map normalizes address keys - but as **bigints**, not strings:

```typescript
notes.get(tokenAddress) // undefined - string key never matches
notes.get(tokenAddress.toLowerCase()) // still undefined
notes.get(BigInt(tokenAddress)) // works

// Iterating across all tokens is always safe:
for (const tokenNotes of notes.values()) {
  // ...
}
```

## Incremental scans with a cursor

Discovery without a cursor scans from the beginning. Persist the cursor from
the underlying provider (or better: reuse the `registry`) so repeat scans
only cover new blocks:

```typescript
const { notes } = await transfers.discoverNotes({
  tokens: [BigInt(tokenAddress)],
  cursor: previousCursor, // resume where the last scan stopped
})
```

The higher-level version of the same idea is the **registry**: every
`execute()` returns an updated `PrivateRegistry` (channels + notes + cursor).
Pass it back into the next `build({ registry })` and combine with
`autoDiscover: { notes: "missing" }` to fetch only what the registry lacks -
`"refresh"` re-scans, `"all"` rebuilds from scratch.

## Discovering channels

```typescript
const { channels, total } = await transfers.discoverChannels("all", {
  cursor: previousChannelCursor,
})
// channels: AddressMap<Channel> keyed by recipient address
```

Pass `"all"` or a list of recipient addresses to filter. Channels hold the
shared key and per-token nonces; you mostly treat them as opaque values that
the registry manages for you.

## Things to notice

- A note becomes visible to discovery once its transaction is accepted, but
  it is only **spendable 10 blocks after creation**. Check `note.created`
  against the current block before offering it as an input.
- Discovery cost scales with unscanned history - a fresh full scan on a
  long-lived pool is slow on RPC-based providers. Cursors and the registry
  exist precisely to avoid it.

Next: [Discovery Providers](/sdk/discovery-providers) - choosing what backs
these scans.

---

