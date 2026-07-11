"""Tests for scripts/check_six_artifacts.py (issue #136).

The gate must (a) ignore annotation-only Core-schema diffs, (b) fire when a
structural Core change omits any of the six artifacts, and (c) pass when all six
are present.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_six_artifacts as csa  # noqa: E402

CORE = "contracts/json/frame.schema.json"
ALL_SIX = [
    CORE,
    "contracts/python/src/weaver_contracts/core.py",
    "examples/sample_payloads/frame.json",
    "contracts/python/tests/test_roundtrip_examples.py",
    "CHANGELOG.md",
    "contracts/python/src/weaver_contracts/version.py",
    "contracts/python/pyproject.toml",
]


def test_annotation_only_change_is_not_structural():
    base = {"type": "object", "x_weaver_stability": "stable",
            "properties": {"a": {"type": "string", "description": "old"}}}
    head = {"type": "object", "x_weaver_stability": "experimental",
            "properties": {"a": {"type": "string", "description": "new"}}}
    assert csa.is_structural_change(base, head) is False


def test_added_field_is_structural():
    base = {"type": "object", "properties": {"a": {"type": "string"}}}
    head = {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}}
    assert csa.is_structural_change(base, head) is True


def test_new_or_deleted_schema_is_structural():
    assert csa.is_structural_change(None, {"type": "object"}) is True
    assert csa.is_structural_change({"type": "object"}, None) is True


def test_is_core_schema_excludes_extended():
    assert csa.is_core_schema(CORE) is True
    assert csa.is_core_schema("contracts/json/extended/telemetry_hint.schema.json") is False


def test_no_structural_change_no_errors():
    assert csa.evaluate([CORE], []) == []


def test_missing_all_six_reports_each():
    errors = csa.evaluate([CORE], [CORE])
    assert len(errors) == len(csa.REQUIRED_ARTIFACTS)


def test_missing_one_artifact_reported():
    without_changelog = [p for p in ALL_SIX if p != "CHANGELOG.md"]
    errors = csa.evaluate(without_changelog, [CORE])
    assert len(errors) == 1 and "CHANGELOG" in errors[0]


def test_all_six_present_passes():
    assert csa.evaluate(ALL_SIX, [CORE]) == []
