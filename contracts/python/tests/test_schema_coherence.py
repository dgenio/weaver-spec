"""Tests for scripts/check_schema_coherence.py (issue #128).

Confirms the conservative description/constraint checks fire on real
incoherence and stay quiet on legitimate registry-style wording, and that every
live schema is coherent.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_schema_coherence as csc  # noqa: E402


def test_self_test_passes():
    assert csc.self_test() == []


def test_missing_description_detected():
    errors = csc.check_schema("s", {"properties": {"x": {"type": "string"}}})
    assert any("no description" in e for e in errors)


def test_inline_enum_without_declaration_detected():
    schema = {"properties": {"x": {"description": "one of: a, b, c", "type": "string"}}}
    assert csc.check_schema("s", schema)


def test_registry_prose_not_flagged():
    schema = {"properties": {"x": {"description": "one of the algorithms in the registry"}}}
    assert csc.check_schema("s", schema) == []


def test_deprecated_prose_requires_keyword():
    schema = {"properties": {"x": {"description": "Deprecated; use y."}}}
    assert any("deprecated" in e for e in csc.check_schema("s", schema))


def test_live_schemas_are_coherent():
    for path in sorted((REPO_ROOT / "contracts" / "json").rglob("*.schema.json")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        assert csc.check_schema(rel, json.loads(path.read_text(encoding="utf-8"))) == []
