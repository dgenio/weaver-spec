#!/usr/bin/env python3
"""Build the static site used to serve canonical Weaver JSON Schema IDs.

This is stdlib-only build-time tooling. It copies every schema listed in the
content-addressed contract index to the path encoded by its canonical ``$id``
and verifies the published bytes against the index before writing them.

The generated directory is intended for GitHub Pages (or any static host). It
is never imported by ``weaver_contracts`` and does not define contract
semantics; ``well-known/contracts.json`` remains the source of truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "well-known" / "contracts.json"
CANONICAL_HOST = "weaver-spec.dev"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _entries(index: dict[str, object]):
    for tier in ("core", "extended"):
        values = index.get(tier, [])
        if not isinstance(values, list):
            raise ValueError(f"index field {tier!r} must be a list")
        for entry in values:
            if not isinstance(entry, dict):
                raise ValueError(f"index field {tier!r} contains a non-object entry")
            yield tier, entry


def build(output: Path, repo_root: Path = REPO_ROOT) -> int:
    index_path = repo_root / "well-known" / "contracts.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    copied = 0
    seen_destinations: set[Path] = set()

    for tier, entry in _entries(index):
        for required in ("$id", "path", "sha256"):
            if required not in entry or not isinstance(entry[required], str):
                raise ValueError(f"{tier} entry missing string field {required!r}: {entry!r}")

        schema_id = entry["$id"]
        parsed = urlsplit(schema_id)
        if parsed.scheme != "https" or parsed.netloc != CANONICAL_HOST:
            raise ValueError(f"unexpected canonical schema host in $id: {schema_id}")
        if parsed.query or parsed.fragment:
            raise ValueError(f"canonical schema $id must not contain query/fragment: {schema_id}")
        if not parsed.path.startswith("/contracts/"):
            raise ValueError(f"canonical schema $id must live under /contracts/: {schema_id}")

        source = (repo_root / entry["path"]).resolve()
        if repo_root.resolve() not in source.parents:
            raise ValueError(f"schema source escapes repository: {entry['path']}")
        if not source.is_file():
            raise ValueError(f"schema source does not exist: {entry['path']}")

        actual_hash = _sha256(source)
        if actual_hash != entry["sha256"]:
            raise ValueError(
                f"schema hash mismatch for {entry['path']}: "
                f"index={entry['sha256']} actual={actual_hash}"
            )

        destination = output / parsed.path.lstrip("/")
        if destination in seen_destinations:
            raise ValueError(f"duplicate canonical destination: {parsed.path}")
        seen_destinations.add(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        copied += 1

    # Publish both the conventional hidden endpoint and the repository-shaped
    # endpoint. The hidden path is useful for machine discovery; the non-hidden
    # path preserves the existing checked-in layout and is easier to inspect.
    for relative in (Path(".well-known/contracts.json"), Path("well-known/contracts.json")):
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(index_path, destination)

    # GitHub Pages/Jekyll must not transform schema JSON.
    (output / ".nojekyll").write_text("", encoding="utf-8")

    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "_site",
        help="Static-site output directory (default: %(default)s)",
    )
    args = parser.parse_args()

    count = build(args.output)
    print(f"Built schema site with {count} canonical schema(s) at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
