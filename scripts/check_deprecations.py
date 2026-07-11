#!/usr/bin/env python3
"""Stdlib-only lint enforcing the deprecation register policy (issue #153).

``docs/DEPRECATIONS.md`` is the authoritative register of deprecated contract
items, governed by a one-MAJOR retention rule (a ``0.x`` deprecation is eligible
for removal no earlier than ``1.0.0``; a ``1.x`` deprecation no earlier than
``2.0.0``). This checker turns that prose policy into a mechanical gate:

1. **Retention math.** For every row in the *Active deprecations* table, the
   ``Eligible to remove`` version must be at or beyond the first MAJOR boundary
   after the ``Deprecated in`` version.
2. **Register coverage.** Every schema field marked ``"deprecated": true`` in
   ``contracts/json/`` must be named by some Active register row, so a schema
   deprecation can never ship without its register entry (and vice-versa is
   enforced by review via the worked example in the doc).

The placeholder ``*(none yet)*`` row is ignored, so the lint passes on an empty
register and only bites once a real deprecation lands.

Parser-free-ish (only a tiny Markdown-table reader) and stdlib-only per the
``scripts/`` rule in ``AGENTS.md``; the pure :func:`check` is driven by
:func:`self_test`.

Run directly to check the live tree::

    python scripts/check_deprecations.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPRECATIONS = REPO_ROOT / "docs" / "DEPRECATIONS.md"
SCHEMA_DIR = REPO_ROOT / "contracts" / "json"

_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def _first_semver(cell: str) -> tuple[int, int, int] | None:
    m = _SEMVER_RE.search(cell)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def parse_active_rows(markdown: str) -> list[dict[str, str]]:
    """Parse the table under '## Active deprecations' into row dicts.

    Only that one section is read (up to the next '---' or '## ' heading), so an
    illustrative table elsewhere in the document is never mistaken for a real
    register row. The placeholder ``*(none yet)*`` row is skipped.
    """
    lines = markdown.splitlines()
    rows: list[dict[str, str]] = []
    in_section = False
    header: list[str] | None = None
    for line in lines:
        if line.strip().startswith("## Active deprecations"):
            in_section = True
            continue
        if in_section and (line.strip() == "---" or line.startswith("## ")):
            break
        if not in_section or "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= {"-", " "}:  # separator row
            continue
        if any("none yet" in c.lower() for c in cells):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def check(rows: list[dict[str, str]], deprecated_fields: list[str]) -> list[str]:
    """Return policy errors (empty == compliant). Pure; driven by self_test."""
    errors: list[str] = []
    registered_text = " ".join(
        " ".join(r.values()) for r in rows
    ).lower()

    for row in rows:
        item = row.get("item", "?")
        dep = _first_semver(row.get("deprecated in", ""))
        elig = _first_semver(row.get("eligible to remove", ""))
        if dep is None:
            errors.append(f"register row {item!r}: unparseable 'Deprecated in' version")
            continue
        if elig is None:
            errors.append(f"register row {item!r}: unparseable 'Eligible to remove' version")
            continue
        min_eligible = (dep[0] + 1, 0, 0)
        if elig < min_eligible:
            errors.append(
                f"register row {item!r}: eligible-to-remove {elig[0]}.{elig[1]}.{elig[2]} "
                f"violates the one-MAJOR retention rule (earliest {min_eligible[0]}.0.0)"
            )

    for field in deprecated_fields:
        # field is "schema.json:dotted.path"; the leaf property name should be
        # named in a register row.
        leaf = field.split(":", 1)[-1].split(".")[-1]
        if leaf.lower() not in registered_text:
            errors.append(
                f"schema field {field!r} is marked \"deprecated\": true but is not "
                "listed in the Active deprecations register"
            )
    return errors


def _collect_deprecated_fields() -> list[str]:
    found: list[str] = []
    for path in sorted(SCHEMA_DIR.rglob("*.schema.json")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        data = json.loads(path.read_text(encoding="utf-8"))

        def walk(props: dict[str, Any], prefix: str) -> None:
            for name, field in (props or {}).items():
                if not isinstance(field, dict):
                    continue
                path = f"{prefix}.{name}" if prefix else name
                if field.get("deprecated") is True:
                    found.append(f"{rel}:{path}")
                if field.get("type") == "object" and isinstance(field.get("properties"), dict):
                    walk(field["properties"], path)

        walk(data.get("properties", {}), "")
    return found


def self_test() -> list[str]:
    failures: list[str] = []

    if check([], []):
        failures.append("empty register rejected")

    ok = [{"item": "`foo`", "deprecated in": "0.9.0", "eligible to remove": "1.0.0"}]
    if check(ok, []):
        failures.append(f"valid 0.x->1.0.0 row rejected: {check(ok, [])}")

    bad_math = [{"item": "`foo`", "deprecated in": "0.9.0", "eligible to remove": "0.9.5"}]
    if not check(bad_math, []):
        failures.append("retention-rule violation not detected")

    unregistered = check([], ["frame.schema.json:legacy_field"])
    if not unregistered:
        failures.append("unregistered deprecated schema field not detected")

    covered = [
        {"item": "`legacy_field`", "deprecated in": "0.9.0", "eligible to remove": "1.0.0"}
    ]
    if check(covered, ["frame.schema.json:legacy_field"]):
        failures.append("registered deprecated field false-positived")
    return failures


def main(argv: list[str] | None = None) -> int:
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        return 1

    rows = parse_active_rows(DEPRECATIONS.read_text(encoding="utf-8"))
    errors = check(rows, _collect_deprecated_fields())
    if errors:
        print("FAIL: deprecation register policy violations:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: deprecation register compliant ({len(rows)} active row(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
