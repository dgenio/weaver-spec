"""Determinism guarantee for the build-time generators (issue #159).

The generated artifacts (well-known/contracts.json, contracts/COVERAGE.md) are
committed, so their generators must be byte-for-byte deterministic: running
twice must produce identical output, and the freshly rendered output must equal
what is on disk (i.e. the committed copy is current and reproducible).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_contracts_index as gci  # noqa: E402
import generate_coverage_table as gct  # noqa: E402


def test_index_generator_is_deterministic():
    first = gci.render_index(gci.build_index())
    second = gci.render_index(gci.build_index())
    assert first == second


def test_index_matches_committed_file():
    rendered = gci.render_index(gci.build_index())
    assert rendered == gci.INDEX_PATH.read_text(encoding="utf-8")


def test_coverage_generator_is_deterministic():
    rows1, totals1 = gct.build_table()
    rows2, totals2 = gct.build_table()
    assert gct.render_markdown(rows1, totals1) == gct.render_markdown(rows2, totals2)


def test_coverage_matches_committed_file():
    rows, totals = gct.build_table()
    assert gct.render_markdown(rows, totals) == gct.OUTPUT_PATH.read_text(encoding="utf-8")
