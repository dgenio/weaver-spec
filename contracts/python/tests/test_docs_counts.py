"""Tests for scripts/check_docs_counts.py (issue #118).

Drives the pure ``check`` / ``self_test`` helpers with fixtures and confirms the
live documentation counts match the real schema filesystem.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_docs_counts as cdc  # noqa: E402


def test_self_test_passes():
    assert cdc.self_test() == []


def test_consistent_counts_have_no_errors():
    files = {"a.md": "Core (9) and Extended (24). all 33 Core and Extended types"}
    assert cdc.check(9, 24, files) == []


def test_detects_stale_core_count():
    errors = cdc.check(9, 24, {"a.md": "Core (8)"})
    assert any("Core" in e for e in errors)


def test_detects_stale_combined_count():
    errors = cdc.check(9, 24, {"a.md": "all 30 Core and Extended types"})
    assert any("30" in e for e in errors)


def test_prose_without_counts_is_ignored():
    assert cdc.check(9, 24, {"a.md": "The Core contracts are language-agnostic."}) == []


def test_live_tree_counts_match_filesystem():
    core, extended = cdc.count_schemas()
    assert cdc.check(core, extended, cdc._read_live_files()) == []
