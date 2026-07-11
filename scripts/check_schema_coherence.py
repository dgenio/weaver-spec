#!/usr/bin/env python3
"""Stdlib-only lint for description/constraint coherence in JSON Schemas (#128).

A schema's prose ``description`` and its machine-readable constraints can drift
apart: a field can describe an enumeration it never declares, or claim to be
deprecated without the ``deprecated`` keyword. Reviewers catch some of these;
this checker catches them mechanically.

The checks are deliberately **conservative** — each is chosen to have a
near-zero false-positive rate on this repository, so the lint never fights
legitimate wording:

1. **Every declared property has a non-empty ``description``.** (All do today;
   this guards future additions.)
2. **Inline enumerations must be declared.** A description that spells out an
   inline option list — ``one of: a, b, c`` — must back it with ``enum``,
   ``const``, or ``$ref``. Prose like "one of the algorithms in the registry"
   (no inline colon-list) is intentionally *not* matched.
3. **Deprecation prose matches the keyword.** A description that says the field
   is deprecated must set ``"deprecated": true`` (and vice-versa), so the
   register lint (#153) and this one agree.

Parser-free/stdlib-only per the ``scripts/`` rule in ``AGENTS.md``; the pure
:func:`check_schema` is driven by :func:`self_test`.

Run directly to check the live tree::

    python scripts/check_schema_coherence.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "contracts" / "json"

# Matches an inline option list: "one of: a, b, c" or "one of: `x` / `y`".
# Requires the colon and at least two separated tokens, so registry-style prose
# ("one of the algorithms in the published registry") does not match.
_INLINE_ENUM_RE = re.compile(r"one of:\s*[^.\n]*?[,/][^.\n]*", re.IGNORECASE)
_DEPRECATED_PROSE_RE = re.compile(r"\bdeprecated\b", re.IGNORECASE)


def _iter_properties(schema: dict[str, Any]):
    """Yield ``(json_path, field_schema)`` for every declared property, recursively."""
    stack: list[tuple[str, dict[str, Any]]] = []

    def push(container: dict[str, Any], prefix: str) -> None:
        props = container.get("properties")
        if isinstance(props, dict):
            for name, field in props.items():
                if isinstance(field, dict):
                    stack.append((f"{prefix}.{name}", field))

    push(schema, "")
    while stack:
        path, field = stack.pop()
        yield path, field
        if field.get("type") == "object":
            push(field, path)
        items = field.get("items")
        if isinstance(items, dict):
            push(items, f"{path}[]")


def check_schema(name: str, schema: dict[str, Any]) -> list[str]:
    """Return coherence errors for a single parsed schema (empty == coherent)."""
    errors: list[str] = []
    for path, field in _iter_properties(schema):
        desc = str(field.get("description", "")).strip()
        if not desc:
            errors.append(f"{name}: property {path} has no description")
            continue

        if _INLINE_ENUM_RE.search(desc) and not (
            "enum" in field or "const" in field or "$ref" in field
        ):
            errors.append(
                f"{name}: property {path} describes an inline option list "
                "but declares no enum/const/$ref"
            )

        says_deprecated = bool(_DEPRECATED_PROSE_RE.search(desc))
        marked_deprecated = field.get("deprecated") is True
        if says_deprecated and not marked_deprecated:
            errors.append(
                f"{name}: property {path} description says 'deprecated' but the "
                "field is not marked \"deprecated\": true"
            )
        if marked_deprecated and not says_deprecated:
            errors.append(
                f"{name}: property {path} is marked deprecated but its description "
                "does not mention it"
            )
    return errors


def self_test() -> list[str]:
    failures: list[str] = []

    ok = {
        "properties": {
            "status": {"description": "The state.", "enum": ["a", "b"]},
            "algo": {
                "description": "Must be one of the algorithms in the registry.",
                "type": "string",
            },
        }
    }
    if check_schema("ok", ok):
        failures.append(f"coherent schema rejected: {check_schema('ok', ok)}")

    cases = {
        "missing desc": {"properties": {"x": {"type": "string"}}},
        "inline enum no declaration": {
            "properties": {"x": {"description": "one of: a, b, c", "type": "string"}}
        },
        "deprecated prose no keyword": {
            "properties": {"x": {"description": "Deprecated; do not use."}}
        },
    }
    for label, bad in cases.items():
        if not check_schema(label, bad):
            failures.append(f"{label!r} not detected")

    # Registry-style prose must NOT be flagged as an inline enum.
    registry = {"properties": {"x": {"description": "one of the values in the registry"}}}
    if check_schema("registry", registry):
        failures.append("registry-style prose false-positived as inline enum")
    return failures


def main(argv: list[str] | None = None) -> int:
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        return 1

    files = sorted(SCHEMA_DIR.rglob("*.schema.json"))
    if not files:
        print(f"ERROR: No schema files found under {SCHEMA_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        errors += check_schema(rel, json.loads(path.read_text(encoding="utf-8")))

    if errors:
        print("FAIL: schema description/constraint incoherence:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(files)} schema(s) coherent (description ⟷ constraints).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
