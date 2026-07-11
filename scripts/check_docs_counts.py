#!/usr/bin/env python3
"""Stdlib-only lint that documentation type-counts are current (issue #118).

Prose docs repeatedly state a derived fact — how many Core and Extended contract
types exist — that silently drifts when a type is added or removed. This checker
treats the schema filesystem as the source of truth and fails CI / pre-commit
when a doc states a stale count. (Contract-version string consistency is a
separate concern, enforced across the canonical files by
``scripts/check_version_consistency.py``; this checker does not duplicate it.)

It matches a small set of targeted phrasings rather than trying to parse English:

* ``Core (N)`` / ``Extended (M)`` — the parenthetical counts used in reference docs.
* ``all N Core and Extended types`` — the combined-total phrasing.

Each matched number must equal the real count. Unmatched prose is ignored, so
the checker never fights natural wording — it only guards the specific
machine-derivable claims above.

It is intentionally **parser-free** (no Markdown parser) and stdlib-only, per the
``scripts/`` rule in ``AGENTS.md``; the pure :func:`check` function is driven by
:func:`self_test` with in-memory fixtures.

Run directly to check the live tree (and the checker's own self-test)::

    python scripts/check_docs_counts.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "contracts" / "json"

# Docs scanned for count claims. Relative to REPO_ROOT.
DOC_GLOBS = ("docs/*.md", "README.md", "contracts/*.md")

_CORE_RE = re.compile(r"Core \((\d+)\)")
_EXTENDED_RE = re.compile(r"Extended \((\d+)\)")
_COMBINED_RE = re.compile(r"all (\d+) Core and Extended types")


def count_schemas() -> tuple[int, int]:
    """Return ``(core_count, extended_count)`` from the schema filesystem."""
    core = len(list(SCHEMA_DIR.glob("*.schema.json")))
    extended_dir = SCHEMA_DIR / "extended"
    extended = (
        len(list(extended_dir.glob("*.schema.json"))) if extended_dir.is_dir() else 0
    )
    return core, extended


def check(core: int, extended: int, files: dict[str, str]) -> list[str]:
    """Return human-readable errors (empty == every stated count is current).

    ``files`` maps a doc's display name to its text, keeping this a pure
    function the self-test can drive with in-memory fixtures.
    """
    combined = core + extended
    errors: list[str] = []
    for name, text in files.items():
        for m in _CORE_RE.finditer(text):
            if int(m.group(1)) != core:
                errors.append(
                    f"{name}: states Core ({m.group(1)}) but there are {core} "
                    "Core schemas"
                )
        for m in _EXTENDED_RE.finditer(text):
            if int(m.group(1)) != extended:
                errors.append(
                    f"{name}: states Extended ({m.group(1)}) but there are "
                    f"{extended} Extended schemas"
                )
        for m in _COMBINED_RE.finditer(text):
            if int(m.group(1)) != combined:
                errors.append(
                    f"{name}: states 'all {m.group(1)} Core and Extended types' "
                    f"but there are {combined}"
                )
    return errors


def _read_live_files() -> dict[str, str]:
    files: dict[str, str] = {}
    for pattern in DOC_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern)):
            files[path.relative_to(REPO_ROOT).as_posix()] = path.read_text(
                encoding="utf-8"
            )
    return files


def self_test() -> list[str]:
    """Assert the checker accepts current counts and rejects each stale claim."""
    core, extended, combined = 9, 24, 33
    good = {
        "a.md": f"Core ({core}) and Extended ({extended}).",
        "b.md": f"all {combined} Core and Extended types",
    }
    failures: list[str] = []
    if check(core, extended, good):
        failures.append(f"consistent fixture was rejected: {check(core, extended, good)}")

    cases = {
        "stale core": {"a.md": f"Core ({core + 1})"},
        "stale extended": {"a.md": f"Extended ({extended + 1})"},
        "stale combined": {"a.md": f"all {combined + 1} Core and Extended types"},
    }
    for label, bad in cases.items():
        if not check(core, extended, bad):
            failures.append(f"{label!r} drift was not detected")
    return failures


def main(argv: list[str] | None = None) -> int:
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        return 1

    core, extended = count_schemas()
    errors = check(core, extended, _read_live_files())
    if errors:
        print(
            f"FAIL: documentation counts are stale (real: Core={core}, "
            f"Extended={extended}):",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: doc counts match the filesystem (Core={core}, Extended={extended}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
