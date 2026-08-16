# Encryption & Viewing Keys

Source: https://strk20-by-example.org/viewing-keys

> How viewing keys, domain-separated masking and ECDH on the STARK curve keep note data private

Every participant in the pool has a **viewing keypair**:

| Key                 | Symbol | Who has it    | Used for                                            |
| ------------------- | ------ | ------------- | --------------------------------------------------- |
| Private viewing key | `k`    | The user only | Decrypting notes, deriving channel keys, nullifiers |
| Public viewing key  | `K`    | On-chain      | Letting others encrypt notes and channels _to_ you  |

`K = k·G` on the STARK curve. The public key is **registered once** via the
`SetViewingKey` action and treated as immutable - every channel ever opened to
you is derived from it, so it cannot change without breaking discovery.

## Symmetric masking

Inside a channel, data is hidden with cheap "hash-and-add" masking rather than
heavyweight ciphers. Each field gets its own **domain-separated Poseidon hash**
plus a per-use **salt**, so no mask is ever reused:

```
enc_amount = (h(ENC_AMOUNT_TAG, channel_key, token, index, 0, salt) + amount) mod 2^128
enc_token  =  h(ENC_TOKEN_TAG,  channel_key, index, 0, salt) + token
```

Anyone holding the channel key recomputes the mask and subtracts it off.
Anyone without it sees values indistinguishable from random field elements.
The domain tags (`ENC_AMOUNT_TAG:V1`, `ENC_TOKEN_TAG:V1`, …) guarantee that a
mask derived for one purpose can never be replayed in another context.

## Asymmetric encryption: ECDH with ephemeral keys

Symmetric masking needs a shared secret - the channel key. Establishing it uses
**ECDH on the STARK curve** with a fresh ephemeral key per channel:

```
sender picks random r
publishes   rG            (ephemeral public key)
computes    shared = r·K  (recipient's public viewing key)

enc_channel_key = h(ENC_CHANNEL_KEY_TAG, shared.x) + channel_key
enc_sender_addr = h(ENC_SENDER_ADDR_TAG, shared.x) + sender_addr
```

The recipient computes the same secret from the other side: `k·(rG) = r·K`.
An observer sees only `rG` and two masked values - they learn that _a_ channel
was opened, not by whom or to whom.

## The auditor copy

At registration, the user's private viewing key `k` is also encrypted - with
the same ephemeral ECDH pattern - to the **auditor's public key** and stored
on-chain. This single escrowed ciphertext is what enables compliance: an
auditor under lawful process can recover `k` and decrypt that user's history,
while everyone else's data stays private. See
[Compliance & Auditing](/compliance).

## Why open notes skip masking

An **open note** carries its amount in plaintext, using the protocol-reserved
salt. This is deliberate: when a DeFi interaction (say, an AMM swap) produces
an output amount that is only known at execution time, the client cannot mask
it in advance - the mask is part of the proven transaction, but the amount
isn't decided until the anonymizer contract runs on-chain. Open notes trade amount
privacy for that late binding; ownership and subsequent spends remain private.

## Rule of thumb

- Everything derivable from `k` + public on-chain data → readable by you.
- Everything else → opaque Poseidon outputs and masked field elements.

Next: where encrypted notes are filed and how recipients find them -
[Channels & Note Discovery](/channels-and-subchannels).

---

