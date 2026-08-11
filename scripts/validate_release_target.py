#!/usr/bin/env python3
"""Validate release tag family, target package, and version identity.

A release tag selects exactly one publishable artifact:

* ``vX.Y.Z`` -> ``weaver_contracts`` under ``contracts/python``
* ``weaver-stack-vX.Y.Z`` -> ``weaver-stack`` under ``packaging/weaver-stack``

The tag version MUST exactly match that target package's ``project.version``.
This script is stdlib-only and is intended to run after checking out the exact
release tag. It can write stable key/value outputs for GitHub Actions.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_PROJECT = REPO_ROOT / "contracts" / "python" / "pyproject.toml"
META_PROJECT = REPO_ROOT / "packaging" / "weaver-stack" / "pyproject.toml"

_CONTRACT_TAG = re.compile(r"^v(?P<version>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$")
_META_TAG = re.compile(
    r"^weaver-stack-v(?P<version>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
)


@dataclass(frozen=True)
class ReleaseTarget:
    tag: str
    target: str
    version: str
    project_path: Path
    distribution: str


def parse_tag(tag: str) -> ReleaseTarget:
    """Return the single package selected by *tag* or raise ``ValueError``."""
    if match := _CONTRACT_TAG.fullmatch(tag):
        version = ".".join(
            (match.group("version"), match.group("minor"), match.group("patch"))
        )
        return ReleaseTarget(
            tag=tag,
            target="contracts",
            version=version,
            project_path=CONTRACTS_PROJECT,
            distribution="weaver_contracts",
        )
    if match := _META_TAG.fullmatch(tag):
        version = ".".join(
            (match.group("version"), match.group("minor"), match.group("patch"))
        )
        return ReleaseTarget(
            tag=tag,
            target="meta",
            version=version,
            project_path=META_PROJECT,
            distribution="weaver-stack",
        )
    raise ValueError(
        "unsupported release tag. Expected vX.Y.Z for weaver_contracts or "
        "weaver-stack-vX.Y.Z for the meta-package"
    )


def project_version(project_path: Path) -> str:
    """Read ``project.version`` from a package pyproject."""
    data = tomllib.loads(project_path.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError(f"missing [project] table: {project_path}")
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError(f"missing project.version: {project_path}")
    return version


def validate(tag: str) -> ReleaseTarget:
    """Resolve *tag* and prove its version matches the selected package."""
    target = parse_tag(tag)
    actual = project_version(target.project_path)
    if actual != target.version:
        raise ValueError(
            f"release tag {tag!r} selects {target.distribution} {target.version}, "
            f"but {target.project_path.relative_to(REPO_ROOT)} declares {actual}"
        )
    return target


def _write_outputs(path: Path, target: ReleaseTarget) -> None:
    lines = (
        f"tag={target.tag}\n",
        f"target={target.target}\n",
        f"version={target.version}\n",
        f"distribution={target.distribution}\n",
        f"project_dir={target.project_path.parent.relative_to(REPO_ROOT).as_posix()}\n",
    )
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.writelines(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Existing release tag being built")
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Append target metadata in GitHub Actions output format",
    )
    args = parser.parse_args()

    try:
        target = validate(args.tag)
        if args.github_output is not None:
            _write_outputs(args.github_output, target)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"OK: {target.tag} -> {target.distribution} {target.version} "
        f"({target.project_path.parent.relative_to(REPO_ROOT)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
