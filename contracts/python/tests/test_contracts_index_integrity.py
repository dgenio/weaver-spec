"""Independent integrity test for well-known/contracts.json (issue #132).

Recomputes each entry's SHA-256 directly from the on-disk schema file — without
routing through the generator's own ``--check`` mode — so a hand-edited index or
a schema changed without regenerating is caught by a second, independent path.
"""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = REPO_ROOT / "well-known" / "contracts.json"


def _sha256_of(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n")  # normalize to LF like git
    return hashlib.sha256(raw).hexdigest()


def test_index_provenance_and_schema_version():
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert index["schema_version"] == 2  # bumped when $comment provenance was added
    assert "$comment" in index and "generate_contracts_index.py" in index["$comment"]


def test_every_index_entry_hash_matches_disk():
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    entries = index["core"] + index["extended"]
    assert entries, "index has no entries"
    for entry in entries:
        schema_path = REPO_ROOT / entry["path"]
        assert schema_path.is_file(), f"missing {entry['path']}"
        assert _sha256_of(schema_path) == entry["sha256"], (
            f"{entry['path']}: index sha256 does not match on-disk file — "
            "regenerate well-known/contracts.json"
        )


def test_index_lists_every_schema_file():
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    indexed = {e["path"] for e in index["core"] + index["extended"]}
    on_disk = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in (REPO_ROOT / "contracts" / "json").rglob("*.schema.json")
    }
    assert indexed == on_disk
