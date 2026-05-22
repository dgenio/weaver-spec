#!/usr/bin/env python3
"""Validate that every JSON Schema in contracts/json/ has the required fields.

A spec-compliant schema in this repository must declare ``$id``, ``title``,
``description``, and a top-level ``required`` array (per CONTRIBUTING.md
"Style Guidelines" and contracts/json/README.md "Schema Design Principles").
This script enforces that contract from both CI and the pre-commit hook so
the two stay in sync.

Run with no arguments to scan ``contracts/json/*.schema.json``:

    python scripts/check_schema_fields.py

Scans every schema and reports all violations before exiting non-zero, so a
single run shows every fix needed. Prints one ``OK`` line per validated
schema and a summary line on success.

This script is intentionally stdlib-only. No third-party dependencies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
REQUIRED_FIELDS = ("$id", "title", "description", "required")


def main() -> int:
    files = sorted(SCHEMA_DIR.glob("*.schema.json"))
    if not files:
        print(f"ERROR: No schema files found under {SCHEMA_DIR}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for path in files:
        rel = path.relative_to(REPO_ROOT)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{rel}: invalid JSON ({exc})")
            continue

        missing = [field for field in REQUIRED_FIELDS if field not in data]
        if missing:
            failures.append(f"{rel}: missing {', '.join(missing)}")
            continue

        print(f"OK: {rel}")

    if failures:
        for line in failures:
            print(f"ERROR: {line}", file=sys.stderr)
        return 1

    print(f"Validated {len(files)} schema(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
