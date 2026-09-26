# Run your own STRK20 prover

A forkable community starter for running the official Starknet privacy
transaction prover on your own computer or server.

The prover does the heavy maths for a private operation and returns a proof to
your wallet or SDK. The wallet submits the resulting transaction to Starknet.
An RPC provider supplies blockchain state; a separate discovery service helps
the wallet find private notes. See the [upstream architecture and compatibility
matrix](https://github.com/starkware-libs/starknet-privacy#compatibility-matrix).

## DYOR and responsibility

**Do your own research.** This community example is experimental, unaudited
deployment tooling, provided as-is without warranty. It is not an official
StarkWare product, a security audit, or financial advice. You are responsible
for your hardware, credentials, operating costs, transaction fees, wallet
backups and any funds you use. Start on testnet and review current upstream
code, audits, release notes and wallet support before considering mainnet.

Self-hosting does not guarantee anonymity or bypass deposit screening. Public
deposits, withdrawals, timing and a transaction's submitting account can reveal
information. Proving and discovery requests can contain private viewing
material: trust the hosts and administrators that process them. A tunnel
protects transport; it does not hide requests from the prover operator. Read
the [privacy model](https://github.com/odinfree/strk20-skills/blob/main/skills/strk20-privacy/SKILL.md) and
[upstream security material](https://github.com/starkware-libs/starknet-privacy/tree/main/docs)
before handling meaningful funds.

## Choose a machine

| Setup | Route |
| --- | --- |
| Linux x86-64 / amd64 | Docker Engine and the Compose plugin; use the quickstart below |
| Windows x86-64 | Ubuntu on WSL2 with Docker Desktop integration **or** Docker Engine inside Ubuntu; see the Windows section |
| Apple Silicon Mac | Run the prover on an amd64 Linux/WSL2 host and reach it through SSH; see the Mac section |

The starter allocates **12 CPU cores and up to 32 GiB RAM**, with one proving
request at a time. This is a starting allocation, not a measured minimum or a
performance guarantee. Leave memory for the host OS and other processes. CPU
and RAM needs depend on the proof; no GPU is requested by this configuration.
It uses a hosted RPC endpoint, so a full local Starknet node is not required.

For the pinned release, an ARM image failed with `SIGILL` on an Apple Silicon
machine. Forcing amd64 emulation on that machine was not validated. The
amd64 route below is the tested deployment path; check future release notes
before assuming broader hardware compatibility.

## Quickstart: Linux or an Ubuntu WSL terminal

You need Git, Python 3.10+, a running Linux amd64 Docker Engine **28.0.0+**, Docker Compose
and your own Starknet RPC v0.10 endpoint. For Ubuntu, use the
[official Docker Engine instructions](https://docs.docker.com/engine/install/ubuntu/).

Fork [odinfree/strk20-skills](https://github.com/odinfree/strk20-skills/fork),
clone your fork, then enter this starter directory. To try the upstream copy:

```sh
git clone https://github.com/odinfree/strk20-skills.git
cd strk20-skills/skills/strk20-local-prover/assets/local-prover
python3 check.py docker
docker compose version
```

The Docker **server** should report Linux and x86_64/amd64. A Docker client
without a working server is insufficient. Review your Docker context if the
server is remote; the port will be bound on that server's loopback interface.
The checker queries the selected server and rejects older engines, unsupported
platforms and unrecognized version strings. It does not audit firewall rules.
Docker documents that engines older than 28.0.0 can expose localhost-published
ports to peers on the same network segment. Keep the default bridge NAT
configuration; custom direct routing can change exposure even on newer engines.
See [Docker's port-publishing documentation](https://docs.docker.com/engine/network/port-publishing/).

Create the private configuration and edit it in your editor:

```sh
umask 077
cp .env.example .env
chmod 600 .env
nano .env
```

Set `RPC_URL` to your own **HTTPS RPC v0.10 endpoint**, such as the versioned
endpoint from your Alchemy dashboard. The template starts on **Sepolia**.
For mainnet, set `CHAIN_ID=SN_MAIN` and use a matching mainnet endpoint.
`SN_SEPOLIA` and `SN_MAIN` must not be mixed. Provider quotas and billing still
apply. [Alchemy's Starknet docs](https://www.alchemy.com/docs/reference/starknet-api-quickstart)
are the starting point for obtaining an endpoint.

Use one literal assignment per line, with URLs enclosed in single quotes.
Keep comments on separate lines. Use UTF-8 and URL-encode embedded apostrophes
or backslashes rather than using dotenv escapes. The checker deliberately does not evaluate
shell commands or dotenv expressions. Existing shell variables override
`.env` in Compose and in the checker; clear old `RPC_URL` / `CHAIN_ID` variables
if you want the file to control them. Never place a wallet signing key or
viewing key in this service configuration.

The explicit `--file` and `--env-file` flags below keep Compose pointed at the
files the checker reads, even when a shell has an old `COMPOSE_FILE` or
`COMPOSE_ENV_FILES` setting. Use these flags for subsequent operations too.
If you intentionally customize the project name or Docker context, use that
same selection consistently for checks, startup, logs and shutdown.

```sh
python3 check.py rpc
docker compose --file compose.yaml --env-file .env config --quiet
docker compose --file compose.yaml --env-file .env pull
docker compose --file compose.yaml --env-file .env up -d
python3 check.py health
```

The RPC check prints only network, version and block height. Allow startup a
few seconds; retry the health check if precomputation is still in progress.
A healthy response looks like:

```json
{"prover":"reachable","rpcVersion":"0.10.3-rc.2","proofGenerationTested":false}
```

Version patch labels can differ between an upstream node and a prover.
`starknet_specVersion` verifies API reachability, **not successful proof
generation**. An actual proof requires the matching SDK and valid application
state. The commands above do not create a wallet, register it, or send a
transaction.

The supplied Compose file binds the host port to `127.0.0.1`. Set `PROVER_HOST_PORT` if 3000 is
already occupied, then use `python3 check.py health --port YOUR_PORT` and the
same port in your SDK configuration. Do not stop an unknown process to free it.

## What is pinned

The image in `compose.yaml` is the official `PRIVACY-0.14.3-RC.2` prover,
pinned to this immutable image-index digest:

```text
ghcr.io/starkware-libs/starknet-privacy/transaction-prover@sha256:a2f71d7139069fa566c4f44bdd66b79cac992c0cbc20ddf0af3a3558c6cabd64
```

The file selects `linux/amd64`. The upstream matrix checked on 2026-09-26 pairs
this prover with discovery `PRIVACY-0.14.3-RC.8` and SDK
`@starkware-libs/starknet-privacy-sdk` `0.14.3-rc.8`.
Use the [live compatibility matrix](https://github.com/starkware-libs/starknet-privacy#compatibility-matrix)
when upgrading. A digest fixes the artifact you run; it does not establish its
safety or ongoing compatibility with a changing network.

Two easy-to-miss settings are already supplied: **`BUILD_MODE=release`** and
**`RPC_URL`**. The image's node setting is not named `STARKNET_RPC_URL`.
Other settings are described in the
[official prover README](https://github.com/starkware-libs/sequencer/tree/avi/privacy/configmap-docs/crates/starknet_transaction_prover).

## Windows / WSL2

From PowerShell, verify the distro uses version 2:

```powershell
wsl --list --verbose
```

If WSL is missing, follow [Microsoft's installation guide](https://learn.microsoft.com/en-us/windows/wsl/install).
Install or select an Ubuntu distro. Choose **one** Docker route:

- **Docker Desktop:** follow [Docker's WSL2 setup](https://docs.docker.com/desktop/features/wsl/),
  enable integration for Ubuntu, and keep Docker Desktop running.
- **Docker Engine inside Ubuntu:** use the Ubuntu installation link above,
  verify [systemd is enabled](https://learn.microsoft.com/en-us/windows/wsl/systemd),
  and enable/start Docker with `sudo systemctl enable --now docker`.

Installing both engines in the same WSL environment can cause conflicts. Run
the quickstart commands inside Ubuntu, preferably from its Linux home directory
so Unix file permissions protect `.env`. Docker access is powerful host access;
follow the official installation guide's permission guidance.

For the Engine-only route, **systemd services do not keep WSL alive**, as
[Microsoft documents](https://learn.microsoft.com/en-us/windows/wsl/systemd#how-does-enabling-systemd-affect-wsl-architecture).
Keep a foreground process attached while using the prover, for example in a
dedicated PowerShell window:

```powershell
wsl -d Ubuntu --exec /bin/sleep infinity
```

Use your actual distro name. Keep that window open; arrange a task at login
yourself if unattended use is required. `restart: unless-stopped` applies when
the Docker daemon is running. It does not wake Windows, start Docker Desktop,
or guarantee recovery before user login. Test your own reboot/resume behavior.

## Use it from a Mac or another computer

Keep the prover port private and use SSH to a host you control. Tailscale is
one way to make the SSH host reachable. Verify its host key and set up your
own SSH account/key through your host's normal administration process.

For a Linux host, or Windows with Docker Desktop managing the service:

```sh
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L 127.0.0.1:3000:127.0.0.1:3000 YOUR_USER@YOUR_HOST
```

For Windows OpenSSH plus Docker Engine inside Ubuntu WSL2, this version also
holds the distro open for the lifetime of the tunnel:

```sh
ssh -T -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L 127.0.0.1:3000:127.0.0.1:3000 YOUR_USER@YOUR_WINDOWS_HOST \
  'wsl.exe -d Ubuntu --exec /bin/sleep infinity'
```

This relies on Windows-to-WSL localhost forwarding. Verify the prover from
inside WSL first, then from Windows, then from the Mac. If the Windows hop
fails, inspect your [WSL networking configuration](https://learn.microsoft.com/en-us/windows/wsl/networking)
rather than exposing the service on all interfaces.

Keep the SSH command running. In another Mac terminal, from a copy of this
starter directory:

```sh
python3 check.py health
```

That health check needs no RPC credential on the client. Use the local port
in the wallet/SDK configuration. Configure your own process supervisor if
you need automatic tunnel reconnect after logout, sleep or network changes.

## Connect your SDK

In an existing `createPrivateTransfers(...)` setup, use:

```typescript
provingProvider: {
  url: "http://127.0.0.1:3000",
  chainId: constants.StarknetChainId.SN_SEPOLIA,
},
```

Use `SN_MAIN` only when your account, pool, node and prover all target mainnet.
The loopback URL also works through the SSH tunnel. Read the
[SDK skill](https://github.com/odinfree/strk20-skills/blob/main/skills/strk20-privacy-sdk/SKILL.md) and
[upstream SDK README](https://github.com/starkware-libs/starknet-privacy/tree/main/sdk)
for package installation and complete wallet wiring; a wallet application
does not automatically switch to this prover merely because it is running.

For a real proof, use `provingBlockId = currentBlock - 10`; all state the proof
reads must already exist at that block. Follow the SDK's nonce, note maturity,
conditional `proofFacts` and `tip: 0n` requirements. Generating a proof is
separate from sending the signed onchain transaction. Review the pool fee,
gas estimate, any required exact allowance and receipt before treating a
funded action as successful. This starter deliberately has no transaction
submission command or bundled account.

Self-hosting does not bypass deposit screening. A supported wallet such as
Ready can shield through its supported flow and privately transfer to an
already registered receiving account. Check current token/network support
and the [screening model](https://strk20-by-example.org/sdk/deposit) first.
Do not assume arbitrary direct SDK deposits are accepted.

### Discovery is a separate service

For note discovery, configure and verify a separate service following the
[upstream discovery deployment guide](https://github.com/starkware-libs/starknet-privacy/tree/main/deploy/discovery-service).
It needs **both `RPC_URL` and `WS_URL`**. A running process with only a WebSocket
URL can connect to block updates while failing every storage query.

The RC.8 Linux image reproduced this startup error:

```text
Could not automatically determine the process-level CryptoProvider from Rustls crate features.
```

A native source build with an explicit rustls provider installed before TLS
initialization resolved that error in a community test. If you choose that
route, inspect the upstream dependency features and select one provider;
the tested build used `rustls::crypto::ring::default_provider().install_default()`
at the start of `main`, with the `ring` feature enabled. This is an operational
patch to review, not a claim that every RC.8 image works unchanged. Check for
an upstream fix before maintaining a local patch.

Verify `/health` reports `OK` with a fresh head, and also run an actual SDK
discovery query. Keep viewing material in your own trusted environment. The
SDK accepts a numeric `blockIdentifier`, which can pin a query to a known
block; this does not replace fixing an unhealthy service.

## Operations and troubleshooting

```sh
docker compose --file compose.yaml --env-file .env ps
python3 check.py logs
python3 check.py logs --follow
docker compose --file compose.yaml --env-file .env stop
docker compose --file compose.yaml --env-file .env up -d
```

`stop` stops this Compose service; `up -d` starts it again. To remove this
starter's container and network, use `docker compose --file compose.yaml --env-file .env down`. Its local `.env`
and the downloaded image remain. None of these commands act on wallet funds.

After an RPC credential change, edit `.env` privately, run `check.py rpc`, then
`docker compose --file compose.yaml --env-file .env up -d --force-recreate`. A simple container restart does not
reload an env file. Docker administrators can inspect container environment
and logs: only run this on a trusted host. Do not paste raw `docker inspect`,
`docker compose --file compose.yaml --env-file .env config`, request bodies or logs into issues; `config --quiet`
validates without displaying credentials, and the helper redacts URLs in logs.

| Symptom | Check |
| --- | --- |
| Docker command exists, server fails | Start the Docker daemon/Desktop and confirm the selected context |
| Docker check rejects the version or architecture | Use a recognized stable Engine 28.0.0+ on Linux amd64; review vendor-suffixed versions against upstream before adapting the check |
| Immediate entrypoint failure | Keep `BUILD_MODE=release`; set `RPC_URL` rather than `STARKNET_RPC_URL` |
| RPC check rejects the network | Match the endpoint's chain to `CHAIN_ID`; inspect stale shell overrides privately |
| RPC reports v0.9 | Select a provider endpoint that actually returns RPC v0.10 |
| `SIGILL` / illegal instruction | Verify CPU and image platform; use the tested native amd64 route for this release |
| Health answers, proof fails | Health is only reachability; verify the SDK/image matrix, finalized proof base and upstream error |
| Prover vanishes after an SSH command exits | Keep WSL attached on Engine-only Windows setups; verify the daemon is still running |
| SSH says address already in use | Pick another local port and use it consistently; preserve the existing listener |
| OOM / exit 137 | Check Docker/WSL memory limits and host pressure; reduce concurrency and provision more RAM |
| Source build hits a Starknet OS assertion | Recheck protocol/image compatibility; compilation alone does not establish compatibility |
| Discovery connects but storage queries fail | Ensure its process actually received `RPC_URL`, as well as `WS_URL` |

For unresolved failures, provide upstream with the image digest, architecture,
RPC version, network and sanitized error. Keep keys, viewing material, private
notes and credential-bearing URLs out of the report.

## Fork, validate, contribute

Original starter code and docs are Apache-2.0 under the repository's
[license](https://github.com/odinfree/strk20-skills/blob/main/LICENSE). The downloaded official image retains its
upstream license. Forks and improvements are welcome; preserve attribution,
make your own compatibility checks, and record the scope of your tests.

```sh
python3 -m unittest discover -s tests -v
docker compose --file compose.yaml --env-file .env config --quiet
```

See [VALIDATION.md](VALIDATION.md) for deployment evidence and [AUDIT.md](AUDIT.md)
for the subsequent review, fixes and regression checks. Follow the
repository's [contribution guide](https://github.com/odinfree/strk20-skills/blob/main/CONTRIBUTING.md) for skill checks
and source updates. No claim of a security audit is implied by passing tests.
