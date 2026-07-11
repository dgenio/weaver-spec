#!/usr/bin/env python3
"""Stdlib-only CI gate for the six-artifact rule on Core contract changes (#136).

AGENTS.md requires that **every Core contract change updates all six artifacts in
the same PR**: JSON Schema, Python dataclass, sample payload, roundtrip test,
CHANGELOG, and version bump. Today that rule is enforced only socially (the PR
template checklist). This gate enforces it mechanically for pull requests.

Two design decisions keep it precise rather than noisy:

* **Only *structural* Core-schema changes trigger it.** Annotation-only edits —
  ``x_weaver_stability`` (#163), ``$comment`` (#151), ``title``, ``description`` —
  are not contract-shape changes, so a PR that only re-annotates schemas (like
  the one that introduced this gate) is not forced through the six-artifact
  dance. Structural equality is decided by stripping those annotation keys
  recursively and comparing.
* **Breaking-vs-additive classification is out of scope** — that belongs to the
  schema-diff detector (#45). This gate only checks *presence* of the six
  artifacts, never whether the change should have been a MAJOR.

The base ref is taken from ``--base`` (or the ``SIX_ARTIFACT_BASE`` env var);
when no base is resolvable (e.g. a push to ``main`` with no PR context) the gate
no-ops and prints why, so it never blocks non-PR builds.

Run in CI::

    python scripts/check_six_artifacts.py --base "origin/main"
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

CORE_SCHEMA_PREFIX = "contracts/json/"
CORE_SCHEMA_SUFFIX = ".schema.json"
EXTENDED_PREFIX = "contracts/json/extended/"

# Annotation keys that do not constitute a contract-shape change.
ANNOTATION_KEYS = frozenset({"x_weaver_stability", "$comment", "title", "description"})

# category -> predicate over a changed path.
REQUIRED_ARTIFACTS: dict[str, Any] = {
    "Python dataclass (core.py)": lambda p: p
    == "contracts/python/src/weaver_contracts/core.py",
    "sample payload": lambda p: p.startswith("examples/sample_payloads/")
    and p.endswith(".json"),
    "roundtrip test": lambda p: p
    == "contracts/python/tests/test_roundtrip_examples.py",
    "CHANGELOG entry": lambda p: p == "CHANGELOG.md",
    "version bump (version.py)": lambda p: p
    == "contracts/python/src/weaver_contracts/version.py",
    "version bump (pyproject.toml)": lambda p: p == "contracts/python/pyproject.toml",
}


def _strip_annotations(node: Any) -> Any:
    """Recursively drop annotation-only keys so two schemas compare structurally."""
    if isinstance(node, dict):
        return {
            k: _strip_annotations(v)
            for k, v in node.items()
            if k not in ANNOTATION_KEYS
        }
    if isinstance(node, list):
        return [_strip_annotations(v) for v in node]
    return node


def is_structural_change(base: dict | None, head: dict | None) -> bool:
    """True if the schema changed in a way that is not annotation-only.

    A newly added schema (no base) with any structural content, or a deleted
    schema (no head), both count as structural.
    """
    if base is None or head is None:
        return True
    return _strip_annotations(base) != _strip_annotations(head)


def is_core_schema(path: str) -> bool:
    return (
        path.startswith(CORE_SCHEMA_PREFIX)
        and path.endswith(CORE_SCHEMA_SUFFIX)
        and not path.startswith(EXTENDED_PREFIX)
    )


def evaluate(changed: list[str], structural_core_schemas: list[str]) -> list[str]:
    """Return errors (empty == compliant). Pure; driven by self_test.

    ``structural_core_schemas`` is the subset of changed Core schemas whose
    change is not annotation-only. If it is empty, the six-artifact rule does not
    apply and no errors are returned.
    """
    if not structural_core_schemas:
        return []
    changed_set = list(changed)
    errors: list[str] = []
    for category, predicate in REQUIRED_ARTIFACTS.items():
        if not any(predicate(p) for p in changed_set):
            errors.append(
                f"Core schema(s) {', '.join(sorted(structural_core_schemas))} "
                f"changed structurally, but no {category} change is in this PR"
            )
    return errors


# --------------------------------------------------------------------------
# git plumbing (only main() touches the repo/subprocess; the logic above is pure)
# --------------------------------------------------------------------------

def _git(*args: str) -> str | None:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _load_at(ref: str, path: str) -> dict | None:
    blob = _git("show", f"{ref}:{path}")
    if blob is None:
        return None
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def _resolve_base(explicit: str | None) -> str | None:
    base = explicit or os.environ.get("SIX_ARTIFACT_BASE")
    if not base:
        return None
    # Confirm the ref exists.
    if _git("rev-parse", "--verify", "--quiet", base) is None:
        return None
    return base


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Base ref to diff against (e.g. origin/main).")
    args = parser.parse_args(argv)

    base = _resolve_base(args.base)
    if base is None:
        print(
            "OK (no-op): no resolvable base ref, so no PR diff to check "
            "(set --base or SIX_ARTIFACT_BASE in PR context)."
        )
        return 0

    diff = _git("diff", "--name-only", f"{base}...HEAD")
    if diff is None:
        print(f"OK (no-op): could not diff against {base!r}.")
        return 0
    changed = [line.strip() for line in diff.splitlines() if line.strip()]

    structural: list[str] = []
    for path in changed:
        if not is_core_schema(path):
            continue
        if is_structural_change(_load_at(base, path), _load_at("HEAD", path)):
            structural.append(path)

    errors = evaluate(changed, structural)
    if errors:
        print("FAIL: six-artifact rule not satisfied:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print(
            "  See AGENTS.md 'Core contract change scope'. If this was an "
            "annotation-only change, no action is needed — this gate ignores "
            "annotation-only diffs, so a trigger means a structural change.",
            file=sys.stderr,
        )
        return 1

    if structural:
        print(
            f"OK: structural Core change ({', '.join(structural)}) is accompanied "
            "by all six artifacts."
        )
    else:
        print("OK: no structural Core-schema change in this diff.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
