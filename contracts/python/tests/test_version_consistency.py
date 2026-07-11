"""Tests for scripts/check_version_consistency.py (issue #110).

The script lives under scripts/ (stdlib-only build-time tooling). These tests
drive its pure ``check`` / ``self_test`` helpers with fixtures and confirm the
live repository tree is consistent.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_version_consistency as cvc  # noqa: E402


def _consistent(version: str = "1.2.3") -> dict[str, str]:
    return {
        "pyproject.toml": f'version = "{version}"\n',
        "well-known/contracts.json": f'{{\n  "contract_version": "{version}"\n}}\n',
        "CHANGELOG.md": f"## [Unreleased]\n\n## [{version}] - 2026-01-01\n",
        "README.md": f"Current contract version: **{version}**\n",
        "docs/VERSIONING.md": f"### Current matrix (contract version {version})\n",
        "compatibility.yaml": f'contract_versions:\n  - "{version}"\n',
        "CITATION.cff": f'version: "{version}"\n',
    }


def test_self_test_passes():
    assert cvc.self_test() == []


def test_consistent_tree_has_no_errors():
    assert cvc.check("1.2.3", _consistent()) == []


def test_detects_mismatch_attributed_to_each_file():
    for name in cvc.SOURCES:
        broken = _consistent()
        broken[name] = broken[name].replace("1.2.3", "9.9.9")
        errors = cvc.check("1.2.3", broken)
        assert any(e.startswith(name + ":") for e in errors), f"{name} drift undetected"


def test_compatibility_allows_multiple_versions():
    # An extra supported version must not trip the "current is present" check.
    files = _consistent()
    files["compatibility.yaml"] = 'contract_versions:\n  - "1.2.3"\n  - "1.1.0"\n'
    assert cvc.check("1.2.3", files) == []


def test_read_contract_version():
    assert cvc.read_contract_version('CONTRACT_VERSION = "3.4.5"\n') == "3.4.5"


def test_live_tree_is_consistent():
    version = cvc.read_contract_version(cvc.VERSION_PY.read_text(encoding="utf-8"))
    assert cvc.check(version, cvc._read_live_files()) == []
