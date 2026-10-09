#!/usr/bin/env python3
"""Build the static site that serves canonical weaver-spec JSON Schema $id URLs.

The content-addressed ``well-known/contracts.json`` index is the source of truth.
For every indexed schema this script:

1. validates that the $id uses the canonical HTTPS host and contract path;
2. verifies the source file bytes against the index SHA-256;
3. verifies the source schema's own $id matches the index entry;
4. copies normalized LF bytes to the URL path implied by the $id;
5. publishes the contract index at ``/.well-known/contracts.json``.

The generated output is deterministic and contains no timestamps. It is suitable
for GitHub Pages or another static host. The script is stdlib-only.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "well-known" / "contracts.json"
CANONICAL_HOST = "weaver-spec.dev"
CANONICAL_PREFIX = "/contracts/"


def _normalized_bytes(raw: bytes) -> bytes:
    """Match the index generator's cross-platform LF normalization."""
    return raw.replace(b"\r\n", b"\n")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_index() -> dict[str, Any]:
    value = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("well-known/contracts.json must contain a JSON object")
    return value


def _entries(index: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for tier in ("core", "extended"):
        values = index.get(tier)
        if not isinstance(values, list):
            raise RuntimeError(f"contracts index field {tier!r} must be a list")
        for entry in values:
            if not isinstance(entry, dict):
                raise RuntimeError(f"contracts index {tier!r} entry must be an object")
            yield entry


def _relative_url_path(schema_id: str) -> Path:
    parsed = urlparse(schema_id)
    if parsed.scheme != "https":
        raise RuntimeError(f"schema $id must use https: {schema_id}")
    if parsed.netloc != CANONICAL_HOST:
        raise RuntimeError(
            f"schema $id must use canonical host {CANONICAL_HOST!r}: {schema_id}"
        )
    if parsed.params or parsed.query or parsed.fragment:
        raise RuntimeError(f"schema $id must not contain params/query/fragment: {schema_id}")
    if not parsed.path.startswith(CANONICAL_PREFIX):
        raise RuntimeError(
            f"schema $id path must start with {CANONICAL_PREFIX!r}: {schema_id}"
        )

    relative = Path(parsed.path.lstrip("/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"unsafe schema $id path: {schema_id}")
    return relative


def _source_for(entry: dict[str, Any]) -> tuple[Path, bytes, str, str]:
    required = ("name", "$id", "path", "sha256")
    missing = [key for key in required if not isinstance(entry.get(key), str) or not entry[key]]
    if missing:
        raise RuntimeError(f"contract entry missing non-empty string field(s): {', '.join(missing)}")

    source = (REPO_ROOT / entry["path"]).resolve()
    try:
        source.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RuntimeError(f"contract source escapes repository: {entry['path']}") from exc
    if not source.is_file():
        raise RuntimeError(f"contract source does not exist: {entry['path']}")

    normalized = _normalized_bytes(source.read_bytes())
    actual_hash = _sha256(normalized)
    expected_hash = entry["sha256"].lower()
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"contract hash mismatch for {entry['path']}: "
            f"index={expected_hash} source={actual_hash}"
        )

    schema = json.loads(normalized)
    if not isinstance(schema, dict):
        raise RuntimeError(f"schema must contain a JSON object: {entry['path']}")
    if schema.get("$id") != entry["$id"]:
        raise RuntimeError(
            f"schema $id mismatch for {entry['path']}: "
            f"index={entry['$id']!r} source={schema.get('$id')!r}"
        )

    return source, normalized, entry["$id"], entry["name"]


def _safe_clean_output(output: Path) -> Path:
    output = output.resolve()
    filesystem_root = Path(output.anchor).resolve()
    if output in {filesystem_root, REPO_ROOT.resolve()}:
        raise RuntimeError(f"refusing to replace unsafe output directory: {output}")
    if output.exists():
        if output.is_symlink():
            raise RuntimeError(f"refusing to replace symlink output directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    return output


def build_site(output: Path) -> int:
    """Build *output* and return the number of published schemas."""
    index = _load_index()
    output = _safe_clean_output(output)
    destinations: set[Path] = set()
    rows: list[tuple[str, str]] = []

    for entry in _entries(index):
        _source, normalized, schema_id, name = _source_for(entry)
        relative = _relative_url_path(schema_id)
        if relative in destinations:
            raise RuntimeError(f"duplicate hosted schema path: {relative.as_posix()}")
        destinations.add(relative)

        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(normalized)
        rows.append((name, schema_id))

    well_known = output / ".well-known"
    well_known.mkdir(parents=True, exist_ok=True)
    index_bytes = _normalized_bytes(INDEX_PATH.read_bytes())
    (well_known / "contracts.json").write_bytes(index_bytes)

    # Preserve the canonical schema namespace even if the external brand changes.
    (output / "CNAME").write_text(f"{CANONICAL_HOST}\n", encoding="utf-8")

    version = html.escape(str(index.get("contract_version", "unknown")))
    links = "\n".join(
        f'<li><a href="{html.escape(urlparse(schema_id).path)}">{html.escape(name)}</a></li>'
        for name, schema_id in sorted(rows)
    )
    index_html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Schema host</title></head>
<body>
<h1>Schema host</h1>
<p>Contract version: <code>{version}</code></p>
<p>Machine-readable index: <a href="/.well-known/contracts.json">/.well-known/contracts.json</a></p>
<ul>
{links}
</ul>
</body>
</html>
"""
    (output / "index.html").write_text(index_html, encoding="utf-8", newline="\n")

    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "_schema_site",
        help="Directory to replace with the generated static site.",
    )
    args = parser.parse_args()

    try:
        count = build_site(args.output)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Built {count} hosted schema(s) in {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
