"""Tests for the x_weaver_stability annotation and its enforcement (issue #163).

The annotation is added to every Core and Extended schema and enforced by
scripts/check_schema_fields.py. These tests confirm the live schemas all carry a
valid value and that the checker's vocabulary is the documented one.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_schema_fields as csf  # noqa: E402

SCHEMA_DIR = REPO_ROOT / "contracts" / "json"


def test_vocabulary_is_documented_set():
    assert csf.STABILITY_LEVELS == ("stable", "experimental", "deprecated")
    assert "x_weaver_stability" in csf.REQUIRED_FIELDS


def test_every_live_schema_has_valid_stability():
    files = sorted(SCHEMA_DIR.rglob("*.schema.json"))
    assert len(files) == 33
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "x_weaver_stability" in data, f"{path.name} missing x_weaver_stability"
        assert data["x_weaver_stability"] in csf.STABILITY_LEVELS


def test_checker_passes_on_live_tree():
    assert csf.main() == 0
