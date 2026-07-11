"""Tests for scripts/check_deprecations.py (issue #153)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_deprecations as cd  # noqa: E402


def test_self_test_passes():
    assert cd.self_test() == []


def test_empty_register_is_compliant():
    assert cd.check([], []) == []


def test_retention_rule_violation_detected():
    rows = [{"item": "`f`", "deprecated in": "0.9.0", "eligible to remove": "0.9.5"}]
    assert any("retention" in e for e in cd.check(rows, []))


def test_valid_retention_passes():
    rows = [{"item": "`f`", "deprecated in": "1.2.0", "eligible to remove": "2.0.0"}]
    assert cd.check(rows, []) == []


def test_unregistered_deprecated_field_detected():
    assert cd.check([], ["frame.schema.json:legacy"])


def test_registered_deprecated_field_ok():
    rows = [{"item": "`legacy`", "deprecated in": "0.9.0", "eligible to remove": "1.0.0"}]
    assert cd.check(rows, ["frame.schema.json:legacy"]) == []


def test_nested_field_matched_by_leaf_name():
    # A nested deprecated field is recorded with its full dotted path; coverage
    # matches on the leaf name, so a register row naming the leaf satisfies it.
    rows = [{"item": "`child`", "deprecated in": "0.9.0", "eligible to remove": "1.0.0"}]
    assert cd.check(rows, ["s.schema.json:parent.child"]) == []
    assert cd.check([], ["s.schema.json:parent.child"])  # unregistered still flagged


def test_active_table_parser_skips_placeholder():
    md = cd.DEPRECATIONS.read_text(encoding="utf-8")
    assert cd.parse_active_rows(md) == []


def test_live_tree_compliant():
    rows = cd.parse_active_rows(cd.DEPRECATIONS.read_text(encoding="utf-8"))
    assert cd.check(rows, cd._collect_deprecated_fields()) == []
