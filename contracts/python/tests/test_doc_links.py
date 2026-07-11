"""Tests for scripts/check_doc_links.py (issue #119).

Exercises heading-slug generation, anchor resolution, and schema ``$id``
consistency with fixtures, and confirms the live tree resolves cleanly.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_doc_links as cdl  # noqa: E402


def test_self_test_passes():
    assert cdl.self_test() == []


def test_heading_slugs_github_style_and_dedup():
    slugs = cdl.heading_slugs("# A B (c-D)\n## Dup\n## Dup\n")
    assert "a-b-c-d" in slugs
    assert "dup" in slugs and "dup-1" in slugs


def test_fenced_pseudo_heading_ignored():
    assert cdl.heading_slugs("```\n# not heading\n```\n") == set()


def test_valid_same_doc_anchor_passes():
    assert cdl.check_links({"a.md": "# Sec One\n[x](#sec-one)\n"}) == []


def test_dangling_same_doc_anchor_detected():
    errors = cdl.check_links({"a.md": "# Sec\n[x](#missing)\n"})
    assert any("missing" in e for e in errors)


def test_schema_id_wrong_base_detected():
    base = "https://weaver-spec.dev/contracts/v0"
    errors = cdl.check_schema_ids(base, {"s.schema.json": "https://x/s"}, {"https://x/s"})
    assert any("base URI" in e for e in errors)


def test_schema_id_absent_from_index_detected():
    base = "https://weaver-spec.dev/contracts/v0"
    ids = {"s.schema.json": f"{base}/s.schema.json"}
    errors = cdl.check_schema_ids(base, ids, set())
    assert any("not listed" in e for e in errors)


def test_live_tree_links_and_ids_resolve():
    assert cdl.check_links(cdl._read_live_docs()) == []
    base = cdl.read_schema_base_uri(cdl.VERSION_PY.read_text(encoding="utf-8"))
    assert cdl.check_schema_ids(base, cdl._read_live_schema_ids(), cdl._read_index_ids()) == []
