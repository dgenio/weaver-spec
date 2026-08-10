#!/usr/bin/env python3
"""Stdlib-only check that the contract version string is consistent everywhere.

``weaver_contracts.version.CONTRACT_VERSION`` is the single source of truth for
the contract version — it already feeds the conformance badge via
``conformance/run.py:contract_version()``. This script reads that value and
asserts the same version appears in every other file that states it, failing
CI / pre-commit on drift (issue #110).

It is intentionally **pure and parser-free** (no YAML/TOML/JSON parser) so it
stays within the ``scripts/`` stdlib-only rule (see ``AGENTS.md``); it matches
targeted patterns, mirroring ``scripts/validate_compatibility.py``. The version
itself is never changed here — this only enforces consistency.

Run directly to check the live tree (and the validator's own self-test)::

    python scripts/check_version_consistency.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_PY = (
    REPO_ROOT / "contracts" / "python" / "src" / "weaver_contracts" / "version.py"
)

# name -> (path relative to repo root, regex template). ``{v}`` is replaced by
# the escaped canonical version; each template must match iff that file states
# the version. compatibility.yaml may legitimately list several supported
# versions, so its pattern asserts the current version is *present*, not unique.
SOURCES: dict[str, tuple[str, str]] = {
    "pyproject.toml": (
        "contracts/python/pyproject.toml",
        r'(?m)^version = "{v}"',
    ),
    "well-known/contracts.json": (
        "well-known/contracts.json",
        r'"contract_version": "{v}"',
    ),
    "CHANGELOG.md": (
        "CHANGELOG.md",
        r"(?m)^## \[{v}\]",
    ),
    "README.md": (
        "README.md",
        r"Current contract version: \*\*{v}\*\*",
    ),
    "docs/VERSIONING.md": (
        "docs/VERSIONING.md",
        r"Current matrix \(contract version {v}\)",
    ),
    "compatibility.yaml": (
        "compatibility.yaml",
        r'(?m)^  - "{v}"',
    ),
    "docs/scoreboard.md": (
        "docs/scoreboard.md",
        r"Spec contract version:\*\* `v{v}`",
    ),
}


def read_contract_version(version_py_text: str) -> str:
    """Extract ``CONTRACT_VERSION`` from the text of ``version.py``."""
    match = re.search(r'CONTRACT_VERSION\s*=\s*"([^"]+)"', version_py_text)
    if not match:
        raise ValueError("CONTRACT_VERSION not found in version.py")
    return match.group(1)


def check(version: str, files: dict[str, str]) -> list[str]:
    """Return human-readable errors (empty == consistent).

    ``files`` maps each :data:`SOURCES` name to that file's text, keeping this a
    pure function the self-test can drive with in-memory fixtures.
    """
    errors: list[str] = []
    escaped = re.escape(version)
    for name, (_path, template) in SOURCES.items():
        if name not in files:
            errors.append(f"{name}: file content not provided")
            continue
        pattern = template.replace("{v}", escaped)
        if re.search(pattern, files[name]) is None:
            errors.append(
                f"{name}: expected contract version {version!r} "
                f"(pattern {pattern!r} not found) — update it to match "
                "CONTRACT_VERSION in version.py"
            )
    return errors


def _read_live_files() -> dict[str, str]:
    return {
        name: (REPO_ROOT / rel).read_text(encoding="utf-8")
        for name, (rel, _template) in SOURCES.items()
    }


def self_test() -> list[str]:
    """Assert the checker accepts a consistent tree and rejects per-file drift.

    Each bad case mutates exactly one file, so a rejection is attributable to
    that file rather than to an incidental error. Returns failures (empty == ok).
    """
    version = "9.9.9"
    consistent = {
        "pyproject.toml": 'version = "9.9.9"\n',
        "well-known/contracts.json": '{\n  "contract_version": "9.9.9"\n}\n',
        "CHANGELOG.md": "## [Unreleased]\n\n## [9.9.9] - 2026-01-01\n",
        "README.md": "Current contract version: **9.9.9**\n",
        "docs/VERSIONING.md": "### Current matrix (contract version 9.9.9)\n",
        "compatibility.yaml": 'contract_versions:\n  - "9.9.9"\n',
        "docs/scoreboard.md": "- **Spec contract version:** `v9.9.9`\n",
    }

    failures: list[str] = []
    good_errors = check(version, consistent)
    if good_errors:
        failures.append(f"consistent fixture was rejected: {good_errors}")
    for name in SOURCES:
        broken = dict(consistent)
        broken[name] = broken[name].replace("9.9.9", "0.0.0")
        errors = check(version, broken)
        if not any(e.startswith(name + ":") for e in errors):
            failures.append(f"drift in {name!r} was not detected")
    return failures


def main(argv: list[str] | None = None) -> int:
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        return 1

    version = read_contract_version(VERSION_PY.read_text(encoding="utf-8"))
    errors = check(version, _read_live_files())
    if errors:
        print(
            f"FAIL: contract version {version!r} (from version.py) is inconsistent:",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: contract version {version} is consistent across {len(SOURCES)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
