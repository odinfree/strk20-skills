# Validation record

Community validation on **2026-09-26**. This records specific checks, not an
audit or a promise of compatibility on every CPU, RPC provider or future
Starknet release. No wallet, viewing key, private transaction data or RPC
credential is included in these artifacts.

## Automated checks

- 11 Python tests passed on Python 3.14. The helper supports Python 3.10+.
- Tests cover matching and mismatched networks, RPC version rejection,
  refusing submission methods, redirect refusal, private config permissions,
  literal dotenv parsing, shell override precedence, and redacted errors/logs.
- Skill frontmatter validation passed.
- `npx -y skills@latest add . --list` found all five skills, including
  `strk20-local-prover`.
- `git diff --check` passed. Relative Markdown links and the publication
  payload were checked before publishing.
- CI runs the Python tests and validates Compose using a synthetic URL.
  CI does not receive credentials, pull the prover image or submit transactions.

## Live starter smoke test

Environment: Windows with Ubuntu 26.04 on WSL2, Linux amd64, Docker Engine
29.8.1, Docker Compose 5.5.1. The exact `compose.yaml` and `check.py` in this
starter were copied to a private temporary directory.

- The pinned official image started successfully in an isolated Compose project.
- Upstream Mainnet RPC check passed: `SN_MAIN`, RPC `0.10.3-rc.0`.
- A separate read-only Sepolia RPC check passed: `SN_SEPOLIA`, RPC `0.10.3-rc.0`.
- Local prover health returned `0.10.3-rc.2`, including after a container restart.
- Docker inspection confirmed loopback binding on test port 3101, 12 CPUs,
  a 32 GiB memory ceiling and `unless-stopped` restart policy.
- The temporary container, network, credential file and directory were removed.

This starter smoke test did **not** request a proof, register an account or
submit a transaction. A specVersion response does not demonstrate that any
particular proof will succeed. The default Sepolia container configuration
was not separately used for an end-to-end proof test.

## Platform and integration observations

The guide also records these operational observations from deploying the
same release family:

- The official amd64 prover successfully generated a registration proof using
  SDK `0.14.3-rc.8` in a separate integration check. No account or receipt data
  from that check is published here. This is not a reproducible funded test
  bundled with the starter.
- A Mac client reached an amd64 WSL2 prover through an SSH loopback tunnel.
- The release's ARM image failed with `SIGILL` on an Apple Silicon machine.
  It was not validated on other ARM hardware or through amd64 emulation.
- The discovery RC.8 Linux image failed at rustls provider initialization.
  A native build with explicit `ring` provider initialization, plus both RPC
  and WebSocket environment settings, passed health and an SDK discovery query.

The Windows Docker Desktop instructions follow official documentation; that
engine route was not independently installed for this validation. Bare-metal
Linux, host reboot recovery, larger proofs, sustained concurrent load and
public multi-user hosting were not tested by this starter's smoke test.
