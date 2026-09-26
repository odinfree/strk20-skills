#!/usr/bin/env python3
"""Read-only RPC/prover checks and redacted logs. Python 3.10+, stdlib only."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
CHAIN_IDS = {"SN_MAIN": "0x534e5f4d41494e", "SN_SEPOLIA": "0x534e5f5345504f4c4941"}
ALLOWED_METHODS = {"starknet_chainId", "starknet_specVersion", "starknet_blockNumber"}


class CheckError(Exception):
    pass


def read_config(path, environ=None):
    """Accept the template's literal dotenv subset, with Compose's shell precedence."""
    env = os.environ if environ is None else environ
    try:
        if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise CheckError("Protect the config first: chmod 600 .env")
        lines = path.read_text().splitlines()
    except OSError:
        raise CheckError("Cannot read .env; copy .env.example and configure it first") from None
    config = {}
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise CheckError(f"Invalid config assignment on line {number}")
        if value.startswith("'") and value.endswith("'") and len(value) >= 2:
            value = value[1:-1]
        elif any(c in value for c in "\"'$#") or any(c.isspace() for c in value):
            raise CheckError(f"Use a single-quoted literal value on config line {number}")
        config[key] = value
    for key in ("RPC_URL", "CHAIN_ID", "PROVER_HOST_PORT"):
        if key in env:
            config[key] = env[key]
    return config


def validate_url(url):
    try:
        parts = urllib.parse.urlsplit(url)
        _ = parts.port
        loopback = parts.hostname == "localhost"
        if parts.hostname and not loopback:
            try:
                loopback = ipaddress.ip_address(parts.hostname).is_loopback
            except ValueError:
                pass
    except ValueError:
        raise CheckError("Malformed RPC URL") from None
    if (not parts.hostname or parts.username or parts.password or parts.fragment
            or (parts.scheme != "https" and not (parts.scheme == "http" and loopback))):
        raise CheckError("Use an HTTPS RPC URL, or HTTP on loopback; no URL userinfo/fragments")
    if "REPLACE_ME" in url:
        raise CheckError("Replace the template RPC URL with your own endpoint")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def rpc(url, method):
    if method not in ALLOWED_METHODS:
        raise CheckError("This helper only performs read-only health checks")
    validate_url(url)
    request = urllib.request.Request(url, data=json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": []
    }).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            payload = response.read(65537)
            if len(payload) > 65536:
                raise CheckError("Unexpectedly large health response")
            data = json.loads(payload)
    except urllib.error.HTTPError as error:
        code = error.code
        error.close()
        raise CheckError(f"HTTP {code}; check the endpoint, credentials and service") from None
    except (OSError, ValueError, urllib.error.URLError):
        raise CheckError("RPC connection or JSON response failed; endpoint details withheld") from None
    if not isinstance(data, dict) or data.get("jsonrpc") != "2.0" or data.get("id") != 1:
        raise CheckError("Unexpected JSON-RPC health response")
    if "error" in data or "result" not in data:
        raise CheckError("RPC returned an error; raw response withheld to protect credentials")
    return data["result"]


def version(url):
    result = rpc(url, "starknet_specVersion")
    if not isinstance(result, str) or not re.fullmatch(r"0\.10(?:\.[0-9]+)*(?:-[A-Za-z0-9.-]+)?", result):
        raise CheckError("Expected the pinned release's RPC v0.10 interface; recheck compatibility")
    return result


def check_upstream(config):
    chain = config.get("CHAIN_ID", "SN_SEPOLIA")
    if chain not in CHAIN_IDS:
        raise CheckError("CHAIN_ID must be SN_SEPOLIA or SN_MAIN for this starter")
    url = config.get("RPC_URL", "")
    spec = version(url)
    if rpc(url, "starknet_chainId") != CHAIN_IDS[chain]:
        raise CheckError("RPC network does not match CHAIN_ID; fix config before starting")
    block = rpc(url, "starknet_blockNumber")
    if type(block) is not int or block < 0:
        raise CheckError("Invalid upstream block height")
    return {"upstream": "OK", "chain": chain, "rpcVersion": spec, "blockNumber": block}


def redact(text, config):
    value = config.get("RPC_URL", "")
    if value:
        text = text.replace(value, "[RPC URL REDACTED]")
    return re.sub(r'''(?:https?|wss?)://[^\s"'<>]+''', "[URL REDACTED]", text)


def logs(config, follow):
    command = ["docker", "compose", "logs", "--no-color", "--tail", "100"]
    if follow:
        command.append("--follow")
    command.append("prover")
    proc = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        for line in iter(proc.stdout.readline, b""):
            print(redact(line.decode("utf-8", "replace"), config), end="", flush=True)
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        return 130


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["rpc", "health", "logs"])
    parser.add_argument("--port", type=int, help="Loopback prover port; default 3000")
    parser.add_argument("--follow", action="store_true", help="Follow redacted container logs")
    args = parser.parse_args()
    try:
        # A Mac client can check an SSH tunnel without storing the RPC credential.
        config = read_config(ROOT / ".env") if args.command != "health" else {}
        if args.command == "rpc":
            result = check_upstream(config)
        elif args.command == "health":
            port = args.port if args.port is not None else 3000
            if not 1 <= port <= 65535:
                raise CheckError("Port must be between 1 and 65535")
            result = {"prover": "reachable", "rpcVersion": version(f"http://127.0.0.1:{port}"),
                      "proofGenerationTested": False}
        else:
            return logs(config, args.follow)
        print(json.dumps(result))
        return 0
    except (CheckError, OSError) as error:
        # Do not dump exception chains, request bodies, or arbitrary upstream errors.
        message = str(error) if isinstance(error, CheckError) else "Required local command unavailable"
        print(f"Check failed: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
