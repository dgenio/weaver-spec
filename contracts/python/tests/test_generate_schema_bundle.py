"""Contract-version validation for the offline schema bundle generator."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_schema_bundle as bundle_generator  # noqa: E402


@pytest.mark.parametrize("invalid", [None, "", "  ", 123, [], {}])
def test_rejects_missing_or_malformed_index_contract_version(monkeypatch, invalid):
    monkeypatch.setattr(
        bundle_generator,
        "_load_index",
        lambda: {"contract_version": invalid, "core": [], "extended": []},
    )
    with pytest.raises(RuntimeError, match="contract_version.*non-empty string"):
        bundle_generator.build_bundle()


def test_uses_explicit_non_empty_contract_version(monkeypatch):
    monkeypatch.setattr(
        bundle_generator,
        "_load_index",
        lambda: {"contract_version": "1.2.3", "core": [], "extended": []},
    )
    assert bundle_generator.build_bundle()["x_weaver_contract_version"] == "1.2.3"
