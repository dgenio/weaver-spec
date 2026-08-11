#!/usr/bin/env python3
"""Tests for scripts/build_schema_site.py."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_schema_site  # noqa: E402


class SchemaSiteTests(unittest.TestCase):
    def test_build_publishes_every_indexed_schema_at_its_id_path(self) -> None:
        index = json.loads(
            build_schema_site.INDEX_PATH.read_text(encoding="utf-8")
        )
        entries = list(build_schema_site._entries(index))

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "site"
            count = build_schema_site.build_site(output)

            self.assertEqual(count, len(entries))
            for entry in entries:
                relative = build_schema_site._relative_url_path(entry["$id"])
                hosted = output / relative
                self.assertTrue(hosted.is_file(), relative.as_posix())
                digest = hashlib.sha256(hosted.read_bytes()).hexdigest()
                self.assertEqual(digest, entry["sha256"])

            self.assertEqual(
                (output / ".well-known" / "contracts.json").read_bytes(),
                build_schema_site.INDEX_PATH.read_bytes().replace(b"\r\n", b"\n"),
            )
            self.assertEqual(
                (output / "CNAME").read_text(encoding="utf-8"),
                "weaver-spec.dev\n",
            )
            self.assertTrue((output / "index.html").is_file())

    def test_build_is_byte_deterministic(self) -> None:
        def snapshot(root: Path) -> dict[str, bytes]:
            return {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in sorted(root.rglob("*"))
                if path.is_file()
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first"
            second = Path(temp_dir) / "second"
            build_schema_site.build_site(first)
            build_schema_site.build_site(second)
            self.assertEqual(snapshot(first), snapshot(second))

    def test_rejects_noncanonical_ids(self) -> None:
        bad_ids = (
            "http://weaver-spec.dev/contracts/v0/frame.schema.json",
            "https://example.invalid/contracts/v0/frame.schema.json",
            "https://weaver-spec.dev/not-contracts/frame.schema.json",
            "https://weaver-spec.dev/contracts/v0/frame.schema.json?mutable=1",
            "https://weaver-spec.dev/contracts/../secret.schema.json",
        )
        for schema_id in bad_ids:
            with self.subTest(schema_id=schema_id):
                with self.assertRaises(RuntimeError):
                    build_schema_site._relative_url_path(schema_id)


if __name__ == "__main__":
    unittest.main()
