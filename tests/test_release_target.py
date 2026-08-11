#!/usr/bin/env python3
"""Tests for scripts/validate_release_target.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_release_target as release_target  # noqa: E402


class ReleaseTargetTests(unittest.TestCase):
    def test_contract_tag_selects_contract_package(self) -> None:
        target = release_target.parse_tag("v0.8.0")
        self.assertEqual(target.target, "contracts")
        self.assertEqual(target.version, "0.8.0")
        self.assertEqual(target.distribution, "weaver_contracts")

    def test_meta_tag_selects_meta_package(self) -> None:
        target = release_target.parse_tag("weaver-stack-v0.7.0")
        self.assertEqual(target.target, "meta")
        self.assertEqual(target.version, "0.7.0")
        self.assertEqual(target.distribution, "weaver-stack")

    def test_rejects_unsupported_or_ambiguous_tags(self) -> None:
        bad_tags = (
            "0.8.0",
            "release-v0.8.0",
            "weaver-v0.8.0",
            "weaver-stack-0.7.0",
            "weaver-stack-v0.7",
            "v0.8",
            "v01.2.3",
            "v0.8.0-rc1",
            "v0.8.0+build",
        )
        for tag in bad_tags:
            with self.subTest(tag=tag):
                with self.assertRaises(ValueError):
                    release_target.parse_tag(tag)

    def test_current_contract_metadata_matches_v080(self) -> None:
        target = release_target.validate("v0.8.0")
        self.assertEqual(target.version, "0.8.0")

    def test_current_meta_metadata_matches_stack_v070(self) -> None:
        target = release_target.validate("weaver-stack-v0.7.0")
        self.assertEqual(target.version, "0.7.0")

    def test_version_mismatch_is_rejected(self) -> None:
        original = release_target.CONTRACTS_PROJECT
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                project = Path(temp_dir) / "pyproject.toml"
                project.write_text(
                    '[project]\nname = "weaver_contracts"\nversion = "9.9.9"\n',
                    encoding="utf-8",
                )
                release_target.CONTRACTS_PROJECT = project
                with self.assertRaisesRegex(ValueError, "declares 9.9.9"):
                    release_target.validate("v0.8.0")
        finally:
            release_target.CONTRACTS_PROJECT = original


if __name__ == "__main__":
    unittest.main()
