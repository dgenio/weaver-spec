"""Regression tests for scripts/build_schema_site.py (#213)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_schema_site as schema_site  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_build_schema_site_publishes_every_canonical_id(tmp_path: Path):
    output = tmp_path / "site"
    copied = schema_site.build(output)

    index = json.loads((REPO_ROOT / "well-known" / "contracts.json").read_text())
    entries = index["core"] + index["extended"]

    assert copied == len(entries)
    for entry in entries:
        parsed = urlsplit(entry["$id"])
        assert parsed.scheme == "https"
        assert parsed.netloc == schema_site.CANONICAL_HOST

        hosted = output / parsed.path.lstrip("/")
        assert hosted.is_file(), entry["$id"]
        assert _sha256(hosted) == entry["sha256"]


def test_build_schema_site_publishes_discovery_index_and_nojekyll(tmp_path: Path):
    output = tmp_path / "site"
    schema_site.build(output)

    canonical_index = (REPO_ROOT / "well-known" / "contracts.json").read_bytes()
    assert (output / ".well-known" / "contracts.json").read_bytes() == canonical_index
    assert (output / "well-known" / "contracts.json").read_bytes() == canonical_index
    assert (output / ".nojekyll").is_file()


def test_build_rejects_hash_drift(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "well-known").mkdir(parents=True)
    (repo / "contracts" / "json").mkdir(parents=True)
    schema = repo / "contracts" / "json" / "x.schema.json"
    schema.write_text('{"$id":"https://weaver-spec.dev/contracts/v0/x.schema.json"}\n')

    index = {
        "schema_version": 1,
        "contract_version": "0.0.0",
        "core": [
            {
                "name": "x",
                "version": "v0",
                "$id": "https://weaver-spec.dev/contracts/v0/x.schema.json",
                "path": "contracts/json/x.schema.json",
                "sha256": "0" * 64,
            }
        ],
        "extended": [],
    }
    (repo / "well-known" / "contracts.json").write_text(json.dumps(index))

    try:
        schema_site.build(tmp_path / "site", repo_root=repo)
    except ValueError as exc:
        assert "schema hash mismatch" in str(exc)
    else:
        raise AssertionError("hash drift must fail the schema-site build")
