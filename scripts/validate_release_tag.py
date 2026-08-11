#!/usr/bin/env python3
"""Validate release-tag family and package version before publication.

This is build-time, stdlib-only tooling. It deliberately validates source
metadata only; the publish workflow separately proves that the requested ref is
an existing Git tag and checks out that exact tag before calling this script.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11+ in release CI
    import tomli as tomllib  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_PYPROJECT = Path("contracts/python/pyproject.toml")
STACK_PYPROJECT = Path("packaging/weaver-stack/pyproject.toml")

_CONTRACT_TAG = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")
_STACK_TAG = re.compile(r"^weaver-stack-v(?P<version>\d+\.\d+\.\d+)$")


class ReleaseValidationError(ValueError):
    """Raised when a release identity is unsafe or inconsistent."""


def classify_tag(tag: str) -> tuple[str, str]:
    """Return ``(target, version)`` for one supported immutable tag family."""
    match = _CONTRACT_TAG.fullmatch(tag)
    if match:
        return "contracts", match.group("version")
    match = _STACK_TAG.fullmatch(tag)
    if match:
        return "stack", match.group("version")
    raise ReleaseValidationError(
        "unsupported release tag family; expected vX.Y.Z for weaver_contracts "
        "or weaver-stack-vX.Y.Z for the meta-package"
    )


def _project_version(path: Path) -> str:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    try:
        value = data["project"]["version"]
    except (KeyError, TypeError) as exc:
        raise ReleaseValidationError(f"missing [project].version in {path}") from exc
    if not isinstance(value, str) or not value:
        raise ReleaseValidationError(f"invalid [project].version in {path}: {value!r}")
    return value


def validate_release(tag: str, target: str = "auto", repo_root: Path = REPO_ROOT) -> tuple[str, str]:
    """Validate tag family and package metadata; return resolved target/version."""
    resolved_target, expected_version = classify_tag(tag)
    if target != "auto" and target != resolved_target:
        raise ReleaseValidationError(
            f"tag {tag!r} belongs to {resolved_target!r}, not requested target {target!r}"
        )

    pyproject = (
        repo_root / CONTRACTS_PYPROJECT
        if resolved_target == "contracts"
        else repo_root / STACK_PYPROJECT
    )
    actual_version = _project_version(pyproject)
    if actual_version != expected_version:
        raise ReleaseValidationError(
            f"tag/package version mismatch for {resolved_target}: "
            f"tag={expected_version} package={actual_version} ({pyproject})"
        )
    return resolved_target, expected_version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Existing release tag being validated")
    parser.add_argument(
        "--target",
        choices=("auto", "contracts", "stack"),
        default="auto",
        help="Expected package target; auto derives it from the tag family",
    )
    args = parser.parse_args(argv)

    try:
        target, version = validate_release(args.tag, args.target)
    except ReleaseValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {args.tag} -> target={target} version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
