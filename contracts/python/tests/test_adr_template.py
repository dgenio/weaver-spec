"""Tests for scripts/check_adr_template.py (issue #129)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_adr_template as cat  # noqa: E402


def _good_adr() -> str:
    return (
        "# ADR 042: Something\n\n**Status:** accepted\n\n"
        + "\n".join(cat.REQUIRED_SECTIONS)
        + "\n"
    )


def test_self_test_passes():
    assert cat.self_test() == []


def test_valid_adr_accepted():
    assert cat.check_adr("042-something.md", _good_adr(), "[042](042-something.md)") == []


def test_missing_section_detected():
    body = _good_adr().replace("## Decision\n", "")
    assert any("Decision" in e for e in cat.check_adr("042-something.md", body, "042-something.md"))


def test_bad_status_detected():
    body = _good_adr().replace("accepted", "someday")
    assert any("status" in e for e in cat.check_adr("042-something.md", body, "042-something.md"))


def test_absence_from_index_detected():
    assert any("index" in e for e in cat.check_adr("042-something.md", _good_adr(), "no rows"))


def test_live_adrs_conform():
    index = cat.README.read_text(encoding="utf-8")
    adrs = [
        p for p in cat.ADR_DIR.glob("*.md") if p.name not in ("README.md", "template.md")
    ]
    assert adrs, "expected at least one ADR"
    for path in adrs:
        assert cat.check_adr(path.name, path.read_text(encoding="utf-8"), index) == []
