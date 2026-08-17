#!/usr/bin/env python3
"""Re-check the fast-moving facts used by the STRK20 skills.

This is adapted from the freshness checker in starkience/strk20-agent-skills.
It uses only the Python standard library.

Run:

    python3 scripts/check_freshness.py
    python3 scripts/check_freshness.py --quick

Exit codes:

    0  checks completed without drift
    1  at least one checked fact drifted
    2  a lookup failed, so the result is incomplete
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = {"User-Agent": "strk20-skills-freshness-check"}
TIMEOUT_SECONDS = 20

NPM_TAGS = {
    ("starknet", "latest"): "10.0.2",
    ("starknet", "next"): "10.7.0",
    ("@starknet-io/get-starknet-discovery", "next"): "6.0.4",
    ("@starknet-io/get-starknet-wallet-standard", "next"): "6.0.4",
    ("@starknet-io/types-js", "latest"): "0.10.3",
    ("@avnu/avnu-sdk", "latest"): "4.2.0",
}

PRIVACY_REPO_RAW = (
    "https://raw.githubusercontent.com/starkware-libs/starknet-privacy/main"
)
EXPECTED_PRIVACY_PATHS = {
    "packages/ekubo_swap_anonymizer/Scarb.toml",
    "packages/privacy/Scarb.toml",
    "packages/shadow_account_anonymizer/Scarb.toml",
    "packages/vesu_lending_anonymizer/Scarb.toml",
}
ABSENT_PRIVACY_PATHS = {
    "packages/escrow/Scarb.toml",
    "packages/sub_account_anonymizer/Scarb.toml",
}
EXPECTED_SDK_VERSION = "0.14.3-rc.5"

WALLET_SPEC_URL = (
    "https://raw.githubusercontent.com/starkware-libs/starknet-specs/"
    "master/wallet-api/wallet_rpc.json"
)
EXPECTED_WALLET_SPEC_BRANCH_VERSION = "0.10.4-rc.1"

EXPECTED_SEPOLIA_POOL = (
    "0x0254a6b2997ef52e9f830ce1f543f6b29768295e8d17e2267d672c552cfe0d91"
)

EXPECTED_DOC_PATHS = {
    "actions-and-proofs",
    "agent-skill",
    "app/tip-jar",
    "builder-privacy-overview",
    "channels-and-subchannels",
    "compliance",
    "helpers/escrow",
    "helpers/privacy-invoke",
    "helpers/swap-helper",
    "helpers/vesu-lending-helper",
    "notes-and-nullifiers",
    "overview",
    "sdk/deposit",
    "sdk/deposit-transfer-surplus",
    "sdk/discovery-providers",
    "sdk/getting-started",
    "sdk/multi-op-batch",
    "sdk/note-discovery",
    "sdk/proving-config",
    "sdk/register",
    "sdk/setup-requirements",
    "sdk/transfer",
    "sdk/withdraw",
    "starknet-wallet-api/avnu-private-swaps",
    "starknet-wallet-api/overview",
    "starknet-wallet-api/private-defi",
    "starknet-wallet-api/starknet-js",
    "starknet-wallet-api/starknet-start-hook",
    "viewing-keys",
    "what-is-strk20",
}


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def url_exists(url: str) -> bool:
    try:
        fetch_text(url)
        return True
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise


def result(status: str, label: str, note: str = "") -> tuple[str, str]:
    marks = {"ok": "  ok  ", "warn": " warn ", "drift": " DRIFT", "error": " ERROR"}
    suffix = f"  {note}" if note else ""
    return status, f"{marks[status]} {label}{suffix}"


def check_npm() -> list[tuple[str, str]]:
    output = []
    for (package, tag), expected in NPM_TAGS.items():
        encoded = urllib.parse.quote(package, safe="@")
        try:
            tags = fetch_json(f"https://registry.npmjs.org/{encoded}").get("dist-tags", {})
            current = tags.get(tag)
        except Exception as error:
            output.append(result("error", f"{package} {tag}", f"lookup failed: {error}"))
            continue

        if current == expected:
            output.append(result("ok", f"{package} {tag}", f"{current}"))
        else:
            output.append(
                result("drift", f"{package} {tag}", f"expected {expected}, found {current}")
            )

    sdk_package = urllib.parse.quote(
        "@starkware-libs/starknet-privacy-sdk", safe="@"
    )
    try:
        public_npm = url_exists(f"https://registry.npmjs.org/{sdk_package}")
        if public_npm:
            output.append(
                result(
                    "drift",
                    "Privacy SDK public npm package",
                    "now resolves, refresh the install guidance",
                )
            )
        else:
            output.append(result("ok", "Privacy SDK public npm package", "still returns 404"))
    except Exception as error:
        output.append(result("error", "Privacy SDK public npm package", str(error)))

    return output


def check_privacy_repo() -> list[tuple[str, str]]:
    output = []
    for relative_path in sorted(EXPECTED_PRIVACY_PATHS):
        try:
            present = url_exists(f"{PRIVACY_REPO_RAW}/{relative_path}")
            status = "ok" if present else "drift"
            note = "present" if present else "missing"
            output.append(result(status, relative_path, note))
        except Exception as error:
            output.append(result("error", relative_path, str(error)))

    for relative_path in sorted(ABSENT_PRIVACY_PATHS):
        try:
            present = url_exists(f"{PRIVACY_REPO_RAW}/{relative_path}")
            status = "drift" if present else "ok"
            note = "unexpectedly present" if present else "absent as expected"
            output.append(result(status, relative_path, note))
        except Exception as error:
            output.append(result("error", relative_path, str(error)))

    try:
        package = fetch_json(f"{PRIVACY_REPO_RAW}/sdk/package.json")
        current_version = package.get("version")
        status = "ok" if current_version == EXPECTED_SDK_VERSION else "drift"
        output.append(
            result(
                status,
                "Privacy SDK source version",
                f"expected {EXPECTED_SDK_VERSION}, found {current_version}",
            )
        )
    except Exception as error:
        output.append(result("error", "Privacy SDK source version", str(error)))

    try:
        interfaces = fetch_text(f"{PRIVACY_REPO_RAW}/sdk/src/interfaces.ts")
        current_names = ("shadowAccounts(", "shadowAccountAnonymizerAddress")
        legacy_names = ("subaccounts(", "subAccountAnonymizerAddress")
        missing = [name for name in current_names if name not in interfaces]
        legacy = [name for name in legacy_names if name in interfaces]
        if missing or legacy:
            output.append(
                result(
                    "drift",
                    "shadow-account TypeScript surface",
                    f"missing={missing or 'none'}, legacy={legacy or 'none'}",
                )
            )
        else:
            output.append(result("ok", "shadow-account TypeScript surface", "RC.5 names present"))
    except Exception as error:
        output.append(result("error", "shadow-account TypeScript surface", str(error)))

    return output


def check_wallet_spec() -> list[tuple[str, str]]:
    try:
        spec = fetch_json(WALLET_SPEC_URL)
        current = spec.get("info", {}).get("version")
    except Exception as error:
        return [result("error", "Wallet API development spec", str(error))]

    status = "ok" if current == EXPECTED_WALLET_SPEC_BRANCH_VERSION else "drift"
    return [
        result(
            status,
            "Wallet API development spec",
            f"expected {EXPECTED_WALLET_SPEC_BRANCH_VERSION}, found {current}",
        )
    ]


def check_by_example(quick: bool) -> list[tuple[str, str]]:
    output = []
    try:
        index = fetch_text("https://strk20-by-example.org/llms.txt")
        found = set(
            re.findall(r"https://strk20-by-example\.org/([A-Za-z0-9/_-]+)\.md", index)
        )
        missing = sorted(EXPECTED_DOC_PATHS - found)
        added = sorted(found - EXPECTED_DOC_PATHS)
        if missing or added:
            output.append(
                result(
                    "drift",
                    "STRK20 by Example page set",
                    f"missing={missing or 'none'}, added={added or 'none'}",
                )
            )
        else:
            output.append(result("ok", "STRK20 by Example page set", f"{len(found)} pages"))
    except Exception as error:
        output.append(result("error", "STRK20 by Example page set", str(error)))
        found = set()

    try:
        getting_started = fetch_text("https://strk20-by-example.org/sdk/getting-started.md")
        status = "ok" if EXPECTED_SEPOLIA_POOL in getting_started else "drift"
        output.append(result(status, "Sepolia pool address", EXPECTED_SEPOLIA_POOL))
    except Exception as error:
        output.append(result("error", "Sepolia pool address", str(error)))

    try:
        builder_overview = fetch_text(
            "https://strk20-by-example.org/builder-privacy-overview.md"
        )
        if "shadow_account_anonymizer" in builder_overview:
            output.append(result("ok", "builder overview account terminology", "shadow accounts"))
        elif "sub_account_anonymizer" in builder_overview:
            output.append(
                result(
                    "warn",
                    "builder overview account terminology",
                    "still uses the pre-RC.5 package name",
                )
            )
        else:
            output.append(
                result("drift", "builder overview account terminology", "known package name absent")
            )
    except Exception as error:
        output.append(result("error", "builder overview account terminology", str(error)))

    if quick or not found:
        return output

    def probe(page_path: str) -> tuple[str, int]:
        url = f"https://strk20-by-example.org/{page_path}.md"
        try:
            request = urllib.request.Request(url, headers=USER_AGENT)
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return page_path, response.status
        except urllib.error.HTTPError as error:
            return page_path, error.code
        except Exception:
            return page_path, 0

    dead = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for page_path, status_code in pool.map(probe, sorted(found)):
            if status_code != 200:
                dead.append(f"{page_path}={status_code or 'unreachable'}")

    if dead:
        output.append(result("drift", "STRK20 by Example page liveness", ", ".join(dead)))
    else:
        output.append(result("ok", "STRK20 by Example page liveness", f"{len(found)} pages"))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="skip per-page liveness checks")
    args = parser.parse_args()

    sections = [
        ("npm", check_npm()),
        ("privacy monorepo", check_privacy_repo()),
        ("wallet API", check_wallet_spec()),
        ("STRK20 by Example", check_by_example(args.quick)),
    ]

    statuses = []
    for title, checks in sections:
        print(f"\n{title}\n{'-' * len(title)}")
        for status, message in checks:
            statuses.append(status)
            print(message)

    print()
    if "drift" in statuses:
        print("Drift found. Re-read the named source before changing a pin or status.")
        return 1
    if "error" in statuses:
        print("The check is incomplete because at least one lookup failed.")
        return 2
    if "warn" in statuses:
        print("No checked claim drifted. Review the warnings before quoting upstream prose.")
    else:
        print("No checked claim drifted.")
    print("Wallet support and audit status still require a manual source check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
