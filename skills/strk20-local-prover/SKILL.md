---
name: strk20-local-prover
description: Deploy and verify a self-hosted STRK20 transaction prover on Linux amd64 or Windows WSL2, or connect a Mac through an SSH tunnel. Covers Docker configuration, RPC checks, resource limits and startup failures. Use strk20-privacy-sdk for wallet registration and transaction construction.
---

# Run a local STRK20 prover

This is a community deployment recipe for the official transaction-prover
image. It supplies compute for a wallet/SDK integration. Running the service
does not register an account, move tokens, or change a wallet's provider.

Read [the runnable starter guide](assets/local-prover/README.md) for the selected
platform. Copy `assets/local-prover/` into the user's chosen working directory;
it includes Compose, a placeholder env file and a standard-library Python
checker. Review the guide's **DYOR and responsibility** section with the user
when assessing whether the setup suits their use.

## Deployment decisions

- Prefer native Linux amd64 or amd64 Ubuntu under WSL2 for this pinned release.
  The guide records an Apple Silicon SIGILL reproduction; do not infer that an
  ARM image tag means that it works on every ARM CPU. Use a remote amd64 host
  for a Mac client unless a newer compatible release has been verified.
- Recheck the public upstream compatibility matrix before changing the pinned
  image. A source branch that builds is not proof of protocol compatibility.
- Ask for the network only if it is unknown. The starter defaults to Sepolia;
  mainnet requires a matching RPC endpoint and `CHAIN_ID=SN_MAIN`.
- Use the operator's own RPC credential. The service needs `RPC_URL` and
  `BUILD_MODE=release`. Its persistent config does not need a wallet signing
  key or a viewing key. Proving requests can contain private viewing material,
  so both the prover host and its administrator are in the privacy trust boundary.
- Keep the host port bound to `127.0.0.1`. For another machine, use an encrypted
  SSH tunnel. Public multi-user hosting needs additional authentication,
  transport protection, request limits and a separate threat assessment.

## Bring up and verify

1. Run `python3 check.py docker`: require a Linux amd64 Docker Engine 28.0.0+
   and a Compose plugin, with enough free RAM. The helper checks the server's
   version and platform, not firewall rules. Preserve default bridge NAT;
   custom direct routing can change exposure.
   Inspect existing containers/ports before choosing a project name and port.
2. Copy `.env.example` to `.env`, restrict it to mode 600, and edit it privately.
   Follow the literal dotenv syntax in the guide. Never print resolved Compose
   config, raw environment values, Docker inspect environment, or raw logs.
3. Run `python3 check.py rpc`: require the intended chain and RPC v0.10.
4. Use `docker compose --file compose.yaml --env-file .env` for all operations:
   first `config --quiet`, then `pull`, then `up -d`. Explicit files prevent
   inherited Compose file settings from selecting a different project/config.
   These commands only start the proving service.
5. Run `python3 check.py health` (or `--port PORT`) and inspect redacted logs with
   `python3 check.py logs`. A specVersion result proves only API reachability.
6. For an authorized wallet integration, verify an actual proof using the
   matching SDK. Use the sibling SDK skill if installed, or its public
   [guide](https://github.com/odinfree/strk20-skills/tree/main/skills/strk20-privacy-sdk).
   Use `head - 10`, mature inputs, conditional proof facts and `tip: 0n`.
   Distinguish proof generation, transaction submission and receipt success.

Under Docker Engine installed directly in WSL2, systemd alone does not keep
the distribution alive. The guide includes a foreground keeper and an SSH
command that holds WSL open. A container restart policy cannot wake a sleeping
host or start a closed Docker Desktop application.

## Integration boundaries

Discovery is a separate service. Verify its `/health` and a real SDK query;
the starter does not deploy it. For the known RC.8 rustls panic, read the
guide's discovery notes before changing providers or building from source.

Self-hosted proving does not bypass deposit screening. A supported wallet
can shield through its supported screening flow and privately transfer to a
registered recipient. Verify wallet support and pool details against current
upstream docs. Registration and other mainnet calls incur fees and require
authorization for that action; a request to install a prover is not such
authorization. Never treat a proof or an empty discovery result as a receipt.

If matching versions and the documented checks still fail, retain only
sanitized errors, image digest, platform and RPC version for an upstream issue.
Do not invent proof formats, substitute network addresses or patch around
onchain validation to make a deployment appear successful.

## Maintenance

The guide and starter are authored examples, not upstream snapshots. Their
validation record is [VALIDATION.md](assets/local-prover/VALIDATION.md).
Before release, run the starter's unit tests, Compose validation, skill
discovery and a live amd64 smoke test when that environment is available.
Update the record to distinguish live tests from untested platform instructions.
