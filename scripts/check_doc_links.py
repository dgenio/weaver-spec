#!/usr/bin/env python3
"""Stdlib-only internal link + anchor + schema ``$id`` checker (issue #119).

Supersedes the inline blob that used to live in ``.github/workflows/links.yml``.
It performs three checks over the repository's Markdown and JSON Schemas, all
offline (no network — the schema ``$id`` URLs are not hosted yet, so "liveness"
means *internal* resolvability, not HTTP reachability):

1. **File links.** Every relative ``[text](path)`` link resolves to a file that
   exists (the original check).
2. **Anchors.** Every ``[text](path#fragment)`` or same-document ``[text](#fragment)``
   link resolves to a real heading in the target Markdown file, using GitHub's
   heading-slug algorithm (including its ``-1`` / ``-2`` de-duplication).
3. **Schema ``$id`` consistency.** Every ``contracts/json/**/*.schema.json``
   declares a ``$id`` that starts with ``SCHEMA_BASE_URI`` and appears in
   ``well-known/contracts.json`` — so a link/reference to a schema id can never
   point at an id the index does not publish.

Parser-free and stdlib-only per the ``scripts/`` rule in ``AGENTS.md``. The pure
helpers (:func:`heading_slugs`, :func:`iter_links`) are exercised by
:func:`self_test`.

Run directly to check the live tree::

    python scripts/check_doc_links.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
INDEX_PATH = REPO_ROOT / "well-known" / "contracts.json"
VERSION_PY = (
    REPO_ROOT / "contracts" / "python" / "src" / "weaver_contracts" / "version.py"
)

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_SCHEMA_BASE_URI_RE = re.compile(r'SCHEMA_BASE_URI\s*=\s*f?"([^"]+)"')

# Files skipped from link checking (their links resolve in a non-file context).
_SKIP_NAMES = frozenset({"pull_request_template.md"})


def _slugify(text: str) -> str:
    """GitHub-style heading slug (before de-duplication)."""
    # Drop inline code backticks and link syntax markers, keep the visible text.
    text = text.replace("`", "")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # [t](u) -> t
    slug = text.strip().lower()
    slug = re.sub(r"[^\w\- ]+", "", slug)  # keep word chars, hyphen, space
    return slug.replace(" ", "-")


def heading_slugs(markdown: str) -> set[str]:
    """Return the set of anchor slugs GitHub would mint for a document's headings.

    Fenced code blocks are ignored so a ``# comment`` inside a code sample is not
    mistaken for a heading. Duplicate slugs get ``-1`` / ``-2`` suffixes, matching
    GitHub's renderer.
    """
    slugs: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in markdown.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if not m:
            continue
        base = _slugify(m.group(2))
        if base in seen:
            seen[base] += 1
            slugs.add(f"{base}-{seen[base]}")
        else:
            seen[base] = 0
            slugs.add(base)
    return slugs


def iter_links(markdown: str) -> list[str]:
    """Return every link target ``(...)`` in a Markdown document."""
    return [m.group(1).strip() for m in _LINK_RE.finditer(markdown)]


def check_links(files: dict[str, str]) -> list[str]:
    """Check file-existence and anchor resolution for a map of relpath -> text."""
    errors: list[str] = []
    slug_cache: dict[str, set[str]] = {}

    def slugs_for(rel: str) -> set[str] | None:
        if rel not in slug_cache:
            path = REPO_ROOT / rel
            if not path.is_file():
                return None
            slug_cache[rel] = heading_slugs(path.read_text(encoding="utf-8"))
        return slug_cache[rel]

    for rel, text in files.items():
        base_dir = (REPO_ROOT / rel).parent
        for link in iter_links(text):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, _, fragment = link.partition("#")
            # Same-document anchor.
            if not path_part:
                if fragment and fragment not in heading_slugs(text):
                    errors.append(f"{rel}: anchor '#{fragment}' has no matching heading")
                continue
            target = (base_dir / path_part).resolve()
            if not target.exists():
                errors.append(f"{rel}: broken link -> {link}")
                continue
            # Cross-document anchor into a Markdown file.
            if fragment and target.suffix == ".md":
                try:
                    target_rel = target.relative_to(REPO_ROOT).as_posix()
                except ValueError:
                    continue
                slugs = slugs_for(target_rel)
                if slugs is not None and fragment not in slugs:
                    errors.append(
                        f"{rel}: anchor '{path_part}#{fragment}' has no matching "
                        f"heading in {target_rel}"
                    )
    return errors


def read_schema_base_uri(version_py_text: str) -> str:
    """Reconstruct SCHEMA_BASE_URI from version.py without importing it."""
    prefix = re.search(r'SCHEMA_VERSION_PREFIX\s*=\s*"([^"]+)"', version_py_text)
    if not prefix:
        raise ValueError("SCHEMA_VERSION_PREFIX not found in version.py")
    return f"https://weaver-spec.dev/contracts/{prefix.group(1)}"


def check_schema_ids(
    base_uri: str, schema_ids: dict[str, str], index_ids: set[str]
) -> list[str]:
    """Every schema $id must start with base_uri and be present in the index."""
    errors: list[str] = []
    for rel, schema_id in sorted(schema_ids.items()):
        if not schema_id.startswith(base_uri):
            errors.append(
                f"{rel}: $id {schema_id!r} does not start with base URI {base_uri!r}"
            )
        if schema_id not in index_ids:
            errors.append(
                f"{rel}: $id {schema_id!r} is not listed in well-known/contracts.json "
                "(regenerate the index)"
            )
    return errors


def _read_live_docs() -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(REPO_ROOT.rglob("*.md")):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        if path.name in _SKIP_NAMES:
            continue
        files[path.relative_to(REPO_ROOT).as_posix()] = path.read_text(encoding="utf-8")
    return files


def _read_live_schema_ids() -> dict[str, str]:
    ids: dict[str, str] = {}
    for path in sorted(SCHEMA_DIR.rglob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        ids[path.relative_to(REPO_ROOT).as_posix()] = data.get("$id", "")
    return ids


def _read_index_ids() -> set[str]:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {
        entry["$id"]
        for section in ("core", "extended")
        for entry in index.get(section, [])
    }


def self_test() -> list[str]:
    """Drive the pure helpers with in-memory fixtures."""
    failures: list[str] = []

    doc = "# Title\n## Extended stability exception (MINOR-breaking)\n## Dup\n## Dup\n"
    slugs = heading_slugs(doc)
    for want in ("title", "extended-stability-exception-minor-breaking", "dup", "dup-1"):
        if want not in slugs:
            failures.append(f"slug {want!r} missing from {sorted(slugs)}")

    # Fenced '# not a heading' must be ignored.
    if "not-a-heading" in heading_slugs("```\n# not a heading\n```\n"):
        failures.append("fenced pseudo-heading was slugified")

    # Anchor resolution: good same-doc anchor passes, bad one fails.
    good = {"a.md": "# Sec\n[x](#sec)\n"}
    if check_links(good):
        failures.append(f"valid same-doc anchor rejected: {check_links(good)}")
    bad = {"a.md": "# Sec\n[x](#nope)\n"}
    if not check_links(bad):
        failures.append("dangling same-doc anchor not detected")

    # Schema id checks.
    base = "https://weaver-spec.dev/contracts/v0"
    ids = {"s.schema.json": f"{base}/s.schema.json"}
    if check_schema_ids(base, ids, {f"{base}/s.schema.json"}):
        failures.append("valid $id rejected")
    if not check_schema_ids(base, ids, set()):
        failures.append("missing-from-index $id not detected")
    if not check_schema_ids(base, {"s.schema.json": "https://evil/x"}, {"https://evil/x"}):
        failures.append("wrong-base $id not detected")
    return failures


def main(argv: list[str] | None = None) -> int:
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        return 1

    docs = _read_live_docs()
    errors = check_links(docs)

    base_uri = read_schema_base_uri(VERSION_PY.read_text(encoding="utf-8"))
    errors += check_schema_ids(base_uri, _read_live_schema_ids(), _read_index_ids())

    if errors:
        print("FAIL: internal link / anchor / $id problems:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"OK: internal links, anchors, and schema $ids resolve "
        f"({len(docs)} Markdown files checked)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
