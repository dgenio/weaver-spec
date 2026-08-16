"""Tests for the immutable release identity helper (#202)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_release_tag import ReleaseValidationError, classify_tag, validate_release  # noqa: E402


def _write_pyproject(path: Path, name: str, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'[project]\nname = "{name}"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def _repo(tmp_path: Path, contracts: str = "0.8.0", stack: str = "0.7.0") -> Path:
    _write_pyproject(
        tmp_path / "contracts/python/pyproject.toml",
        "weaver_contracts",
        contracts,
    )
    _write_pyproject(
        tmp_path / "packaging/weaver-stack/pyproject.toml",
        "weaver-stack",
        stack,
    )
    return tmp_path


def test_classify_contract_and_stack_tag_families():
    assert classify_tag("v0.8.0") == ("contracts", "0.8.0")
    assert classify_tag("weaver-stack-v0.7.0") == ("stack", "0.7.0")


@pytest.mark.parametrize(
    "tag",
    [
        "0.8.0",
        "release-v0.8.0",
        "weaver-stack-0.7.0",
        "v0.8",
        "v0.8.0-rc1",
        "v0.8.0+build",
        "v01.2.3",
        "weaver-stack-v00.7.0",
    ],
)
def test_rejects_unsupported_or_ambiguous_tag_families(tag: str):
    with pytest.raises(ReleaseValidationError, match="unsupported release tag family"):
        classify_tag(tag)


def test_contract_tag_must_match_contract_package_version(tmp_path: Path):
    repo = _repo(tmp_path, contracts="0.8.0")
    assert validate_release("v0.8.0", repo_root=repo) == ("contracts", "0.8.0")
    with pytest.raises(ReleaseValidationError, match="tag/package version mismatch"):
        validate_release("v0.7.0", repo_root=repo)


def test_stack_tag_must_match_meta_package_version(tmp_path: Path):
    repo = _repo(tmp_path, stack="0.7.0")
    assert validate_release("weaver-stack-v0.7.0", repo_root=repo) == ("stack", "0.7.0")
    with pytest.raises(ReleaseValidationError, match="tag/package version mismatch"):
        validate_release("weaver-stack-v0.8.0", repo_root=repo)


def test_wrong_tag_family_cannot_publish_other_target(tmp_path: Path):
    repo = _repo(tmp_path)
    with pytest.raises(ReleaseValidationError, match="belongs to 'contracts'"):
        validate_release("v0.8.0", target="stack", repo_root=repo)
    with pytest.raises(ReleaseValidationError, match="belongs to 'stack'"):
        validate_release("weaver-stack-v0.7.0", target="contracts", repo_root=repo)


def test_live_contract_metadata_matches_intended_v080_identity():
    assert validate_release("v0.8.0") == ("contracts", "0.8.0")


def test_live_meta_metadata_matches_current_stack_v070_identity():
    assert validate_release("weaver-stack-v0.7.0") == ("stack", "0.7.0")
