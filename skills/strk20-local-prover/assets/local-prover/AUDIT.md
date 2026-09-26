# RCI review record

Three review, correction and verification passes on **2026-09-26**, starting
from public commit `44018c5975554082feeb80fe88b74e87df4db01e`. Scope: this
starter's helper, Compose usage, platform prerequisites and tests. This is a
maintainer review of deployment tooling, not an independent security audit
of STRK20, the SDK, cryptography, contracts or the official prover image.

## Pass 1: credential handling

**Reproduced:** a URL containing whitespace or control characters raised an
uncaught Python `InvalidURL` exception whose message included its path. A
malformed HTTP status line could also escape the handler and expose response
content. Reproductions used synthetic strings, never real credentials.

**Corrected:** reject whitespace/control characters before URL parsing, move
request construction inside the protected block, and sanitize HTTP protocol
exceptions. Regression tests failed before the fix and passed afterward.

## Pass 2: configuration and logs

**Reproduced:** `COMPOSE_FILE` could select an unrelated project while the
helper checked this starter's `.env`. A backslash-escaped apostrophe parsed
differently in the helper and Compose. Invalid UTF-8 escaped the config error
handler. URL log redaction missed uppercase or mixed-case schemes.

**Corrected:** documented commands and the log helper explicitly select
`compose.yaml` and `.env`. Unsupported quote/backslash escapes are rejected;
users should URL-encode those characters. Encoding failures produce a short
error, and URL redaction is case-insensitive. Tests exercise these failures
and compare supported config values with real Compose rendering. A separate
Compose test confirms inherited file settings and an implicit override file
cannot select another service when the explicit flags are used.

The helper is a URL redactor, not a general secret scanner. Raw logs or proof
payloads can contain other sensitive material; do not publish them.

## Pass 3: platform and release verification

**Found:** the initial guide did not require an Engine version that fixes
older Docker localhost-port exposure. Docker documents that releases before
28.0.0 can expose localhost-published ports to peers on the same L2 network.
See [Docker's port-publishing documentation](https://docs.docker.com/engine/network/port-publishing/).

**Corrected:** require a stable Docker Engine 28.0.0+ on Linux amd64. The new
read-only `python3 check.py docker` checks the selected server and sanitizes
daemon errors. It rejects unsupported or unrecognized versions/platforms.
The guide also explains that custom routing can change exposure; this check
does not inspect or certify firewall/network configuration.

**Verified:**

- All 22 tests passed on Python 3.10.21 and Python 3.14.7 with Compose 5.5.1.
  Twenty are helper tests; two exercise the real Compose CLI without a daemon.
  Compose tests explicitly skip if the CLI/plugin is absent.
- CI now tests Python 3.10 and 3.14, with pinned action revisions. It uses
  synthetic endpoints and performs no image pulls or transaction submission.
- The updated Docker check passed against a Linux amd64 Engine 29.8.1 server.
- The updated health check reached the existing prover and returned
  `0.10.3-rc.2`, both on its host and through a loopback SSH tunnel.
- Skill validation, discovery of all five skills, relative link checks,
  `git diff --check` and a publication-content review passed.

No proof was requested and no transaction was submitted during these passes.
The running prover was not redeployed. The Compose service/image definition
is unchanged; the earlier deployment smoke test remains in
[VALIDATION.md](VALIDATION.md). Passing these checks does not establish
end-to-end proof correctness or anonymity. DYOR and independently review any
deployment before handling funds.
