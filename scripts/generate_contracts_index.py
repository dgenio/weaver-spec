#!/usr/bin/env python3
"""Generate well-known/contracts.json from the schemas in contracts/json/.

The generated file is a content-addressed index of every published JSON
Schema. Each entry records the schema name, MAJOR version, $id, repo-relative
path, and the SHA-256 of the raw file bytes.

Run with no arguments to regenerate the file in place:

    python scripts/generate_contracts_index.py

Run with --check to verify the on-disk file is up to date. Exits non-zero if
the file is missing or stale. The CI job validate-contracts-index uses this
mode.

This script is intentionally stdlib-only. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
INDEX_PATH = REPO_ROOT / "well-known" / "contracts.json"
VERSION_FILE = REPO_ROOT / "contracts" / "python" / "src" / "weaver_contracts" / "version.py"

INDEX_SCHEMA_VERSION = 1
_CONTRACT_VERSION_RE = re.compile(r'^CONTRACT_VERSION\s*=\s*"([^"]+)"', re.MULTILINE)
_SCHEMA_VERSION_PREFIX_RE = re.compile(
    r'^SCHEMA_VERSION_PREFIX\s*=\s*"([^"]+)"', re.MULTILINE
)


def read_contract_version() -> str:
    """Return CONTRACT_VERSION from version.py, parsed without importing."""
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = _CONTRACT_VERSION_RE.search(text)
    if match is None:
        raise RuntimeError(f"CONTRACT_VERSION not found in {VERSION_FILE}")
    return match.group(1)


def read_schema_version_prefix() -> str:
    """Return SCHEMA_VERSION_PREFIX from version.py."""
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = _SCHEMA_VERSION_PREFIX_RE.search(text)
    if match is None:
        raise RuntimeError(f"SCHEMA_VERSION_PREFIX not found in {VERSION_FILE}")
    return match.group(1)


def schema_entry(path: Path, version_prefix: str) -> dict[str, Any]:
    """Build one index row for a single .schema.json file."""
    raw = path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    schema = json.loads(raw)

    schema_id = schema.get("$id")
    if not isinstance(schema_id, str) or not schema_id:
        raise RuntimeError(f"{path} is missing a non-empty $id")

    name = path.name.removesuffix(".schema.json")
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    return {
        "name": name,
        "version": version_prefix,
        "$id": schema_id,
        "path": rel_path,
        "sha256": sha256,
    }


def build_index() -> dict[str, Any]:
    """Build the full index dict ready to be serialized."""
    version_prefix = read_schema_version_prefix()
    core_entries = [
        schema_entry(p, version_prefix)
        for p in sorted(SCHEMA_DIR.glob("*.schema.json"))
    ]
    extended_dir = SCHEMA_DIR / "extended"
    extended_entries: list[dict[str, Any]] = []
    if extended_dir.is_dir():
        extended_entries = [
            schema_entry(p, version_prefix)
            for p in sorted(extended_dir.glob("*.schema.json"))
        ]
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "contract_version": read_contract_version(),
        "core": core_entries,
        "extended": extended_entries,
    }


def render_index(index: dict[str, Any]) -> str:
    """Serialize the index deterministically (two-space indent, trailing newline)."""
    return json.dumps(index, indent=2, sort_keys=False) + "\n"


def write_index(text: str) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the on-disk index matches the schemas; exit non-zero if stale.",
    )
    args = parser.parse_args()

    expected = render_index(build_index())

    if args.check:
        if not INDEX_PATH.exists():
            print(
                f"ERROR: {INDEX_PATH.relative_to(REPO_ROOT)} does not exist. "
                "Run `python scripts/generate_contracts_index.py` to create it.",
                file=sys.stderr,
            )
            return 1
        actual = INDEX_PATH.read_text(encoding="utf-8")
        if actual != expected:
            print(
                f"ERROR: {INDEX_PATH.relative_to(REPO_ROOT)} is out of date. "
                "Run `python scripts/generate_contracts_index.py` and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {INDEX_PATH.relative_to(REPO_ROOT)} is up to date.")
        return 0

    write_index(expected)
    print(f"Wrote {INDEX_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
