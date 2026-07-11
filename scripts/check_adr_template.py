#!/usr/bin/env python3
"""Stdlib-only linter enforcing the ADR decision-record template (issue #129).

Architecture Decision Records under ``docs/adr/`` are the durable record of
breaking Core changes (see CONTRIBUTING.md). A malformed ADR — missing a
required section, an unknown status, or absent from the index — degrades that
record silently. This checker asserts every ``docs/adr/NNN-*.md``:

* has an ``# ADR NNN: <title>`` H1 whose number matches its filename;
* declares ``**Status:**`` with a value from the template vocabulary;
* contains each section heading the template mandates;
* is listed in ``docs/adr/README.md`` (the index).

``template.md`` and ``README.md`` are not themselves ADRs and are skipped.

Parser-free/stdlib-only per the ``scripts/`` rule in ``AGENTS.md``; the pure
:func:`check_adr` is driven by :func:`self_test`.

Run directly to check the live tree::

    python scripts/check_adr_template.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = REPO_ROOT / "docs" / "adr"
README = ADR_DIR / "README.md"

REQUIRED_SECTIONS = (
    "## Context",
    "## Decision",
    "## Consequences",
    "## Affected Contracts",
    "## Migration Path",
    "## Cross-Repo Impact",
)
VALID_STATUSES = ("proposed", "accepted", "rejected", "superseded")

_FILENAME_RE = re.compile(r"^(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_H1_RE = re.compile(r"^# ADR (\d{3}):\s+\S", re.MULTILINE)
_STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(\w+)", re.MULTILINE)


def check_adr(filename: str, text: str, index_text: str) -> list[str]:
    """Return template-conformance errors for one ADR (empty == conforms)."""
    errors: list[str] = []
    fn_match = _FILENAME_RE.match(filename)
    if not fn_match:
        errors.append(f"{filename}: filename must match NNN-short-title.md")
        number = None
    else:
        number = fn_match.group(1)

    h1 = _H1_RE.search(text)
    if not h1:
        errors.append(f"{filename}: missing '# ADR NNN: <title>' heading")
    elif number is not None and h1.group(1) != number:
        errors.append(
            f"{filename}: H1 number {h1.group(1)} does not match filename {number}"
        )

    status = _STATUS_RE.search(text)
    if not status:
        errors.append(f"{filename}: missing '**Status:**' line")
    elif status.group(1) not in VALID_STATUSES:
        errors.append(
            f"{filename}: status {status.group(1)!r} not one of "
            f"{', '.join(VALID_STATUSES)}"
        )

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"{filename}: missing required section '{section}'")

    if filename not in index_text:
        errors.append(f"{filename}: not listed in docs/adr/README.md index")
    return errors


def self_test() -> list[str]:
    good_body = (
        "# ADR 042: Something\n\n**Status:** accepted\n\n"
        + "\n".join(REQUIRED_SECTIONS)
        + "\n"
    )
    index = "| [042](042-something.md) | ... |\n"
    failures: list[str] = []
    if check_adr("042-something.md", good_body, index):
        failures.append(f"valid ADR rejected: {check_adr('042-something.md', good_body, index)}")

    if not check_adr("042-something.md", good_body.replace("## Decision\n", ""), index):
        failures.append("missing section not detected")
    if not check_adr("042-something.md", good_body.replace("accepted", "maybe"), index):
        failures.append("bad status not detected")
    if not check_adr("042-something.md", good_body, "nothing here"):
        failures.append("absence from index not detected")
    if not check_adr("042-something.md", good_body.replace("ADR 042", "ADR 999"), index):
        failures.append("H1/filename number mismatch not detected")
    return failures


def main(argv: list[str] | None = None) -> int:
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        return 1

    index_text = README.read_text(encoding="utf-8")
    adrs = sorted(
        p for p in ADR_DIR.glob("*.md") if p.name not in ("README.md", "template.md")
    )
    if not adrs:
        print(f"ERROR: no ADR files found under {ADR_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in adrs:
        errors += check_adr(path.name, path.read_text(encoding="utf-8"), index_text)

    if errors:
        print("FAIL: ADR template violations:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(adrs)} ADR(s) conform to the template and are indexed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
