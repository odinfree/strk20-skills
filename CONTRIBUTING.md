# Contributing

Use these skills on an STRK20 project. If a skill misses a flow, points at
stale package data, or sends an agent down the wrong route, open an issue or
pull request. Small fixes are welcome.

## Useful contributions

- Add a public builder workflow that the current skills do not cover.
- Correct a version, address, wallet capability, or package-registry detail.
- Add a reproducible failure mode and the fix that cleared it.
- Improve a skill trigger, route boundary, example, or failure table.

## Source rules

Link every factual change to a public source or include a minimal reproduction.
Label community examples as community examples. Keep claims about wallet
support, package versions, addresses, and feature status narrow enough to
recheck later.

Files under `skills/*/references/` are verbatim upstream snapshots. Replace a
reference with a fresh upstream copy when the source changes. Do not rewrite
those files for style.

Never commit private keys, API tokens, wallet secrets, internal documents, or
unpublished product information.

## Before opening a pull request

Run these checks from the repository root:

```sh
git diff --check
npx -y skills@latest add . --list
```

Confirm that the second command finds every intended skill. Read the changed
skill once more against its bundled sources, especially when the change touches
proof timing, transaction sequencing, package versions, or network addresses.

In the pull request, explain the problem, the change, the source or
reproduction, and the checks you ran. Keep unrelated fixes separate.
