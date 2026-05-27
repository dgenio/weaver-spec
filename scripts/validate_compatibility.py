#!/usr/bin/env python3
"""Stdlib-only validation logic for ``compatibility.yaml``.

This module is intentionally **pure and YAML-parser-free** so it stays within
the ``scripts/`` stdlib-only rule (see ``AGENTS.md``). Callers — the
``validate-compatibility`` CI job and the ``compatibility-manifest`` pre-commit
hook — parse ``compatibility.yaml`` and ``docs/VERSIONING.md`` themselves (with
PyYAML, in their own isolated environments) and pass the parsed mapping plus the
VERSIONING.md text into :func:`validate`.

Run directly to execute the validator's self-test::

    python scripts/validate_compatibility.py
"""

import re
import sys

ALLOWED_STATUS = {"verified", "provisional", "unverified", "incompatible"}
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
REQUIRED_KEYS = {
    "name",
    "role",
    "status",
    "supported_spec_versions",
    "tested_version",
    "declaration",
    "known_limitations",
}
REQUIRED_REPOS = {"contextweaver", "agent-kernel", "ChainWeaver"}


def _referenced(name, versioning_md):
    """True if ``name`` appears as a whole token in ``versioning_md``.

    A plain substring test would pass on a coincidental fragment (e.g. a repo
    name embedded in unrelated prose), so match on non-word, non-hyphen
    boundaries to require the name to stand on its own.
    """
    return re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", versioning_md) is not None


def validate(manifest, versioning_md, *, required_repos=REQUIRED_REPOS):
    """Return a list of human-readable errors. Empty list means the manifest is valid."""
    if not isinstance(manifest, dict):
        return ["compatibility.yaml must be a mapping"]

    errors = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    versions = manifest.get("contract_versions")
    if not isinstance(versions, list) or not versions:
        errors.append("contract_versions must be a non-empty list")
    else:
        for v in versions:
            if not isinstance(v, str) or not SEMVER.match(v):
                errors.append(f"contract_versions entry {v!r} is not MAJOR.MINOR.PATCH")

    valid_contract_versions = (
        {v for v in versions if isinstance(v, str)} if isinstance(versions, list) else set()
    )

    repos = manifest.get("repositories")
    if not isinstance(repos, list) or not repos:
        errors.append("repositories must be a non-empty list")
        repos = []

    seen = set()
    for i, entry in enumerate(repos):
        where = f"repositories[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} must be a mapping")
            continue
        missing = REQUIRED_KEYS - entry.keys()
        if missing:
            errors.append(f"{where} missing keys: {sorted(missing)}")
        name = entry.get("name")
        if isinstance(name, str):
            seen.add(name)
            if not _referenced(name, versioning_md):
                errors.append(f"{where}: {name!r} is not referenced in docs/VERSIONING.md")
        status = entry.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{where}: status {status!r} not in {sorted(ALLOWED_STATUS)}")
        ssv = entry.get("supported_spec_versions")
        if not isinstance(ssv, list):
            errors.append(f"{where}: supported_spec_versions must be a list")
        else:
            for v in ssv:
                if not isinstance(v, str) or not SEMVER.match(v):
                    errors.append(f"{where}: supported_spec_versions entry {v!r} is not semver")
                elif v not in valid_contract_versions:
                    errors.append(
                        f"{where}: supported_spec_versions entry {v!r} is not one of "
                        f"contract_versions {sorted(valid_contract_versions)}"
                    )
        tested = entry.get("tested_version")
        if tested is not None and (not isinstance(tested, str) or not SEMVER.match(tested)):
            errors.append(f"{where}: tested_version {tested!r} must be null or MAJOR.MINOR.PATCH")
        # A claimed status must be backed by a declaration reference and concrete versions.
        if status in {"verified", "provisional"}:
            if not entry.get("declaration"):
                errors.append(f"{where}: status {status!r} requires a non-null 'declaration' reference")
            if not isinstance(ssv, list) or not ssv:
                errors.append(f"{where}: status {status!r} requires a non-empty 'supported_spec_versions'")
            if tested is None:
                errors.append(f"{where}: status {status!r} requires a non-null 'tested_version'")

    for missing_repo in sorted(required_repos - seen):
        errors.append(f"required sibling repository {missing_repo!r} is missing from the manifest")

    return errors


def self_test():
    """Assert the validator accepts a good manifest and rejects malformed ones.

    Each bad case is otherwise complete (all required repos present) with a
    single injected defect, so rejection is attributable to that defect rather
    than an incidental error. Returns a list of failures (empty == all good).
    """
    vm = "contextweaver agent-kernel ChainWeaver"

    def repo(name, **overrides):
        base = {
            "name": name,
            "role": "role",
            "status": "unverified",
            "supported_spec_versions": [],
            "tested_version": None,
            "declaration": None,
            "known_limitations": [],
        }
        base.update(overrides)
        return base

    def manifest(repos):
        return {"schema_version": 1, "contract_versions": ["0.5.0"], "repositories": repos}

    def with_defect(**overrides):
        return manifest([repo("contextweaver", **overrides), repo("agent-kernel"), repo("ChainWeaver")])

    good = manifest([repo("contextweaver"), repo("agent-kernel"), repo("ChainWeaver")])
    bad_cases = {
        "verified without versions/declaration": with_defect(status="verified"),
        "supported_spec_versions not in contract_versions": with_defect(supported_spec_versions=["0.4.0"]),
        "tested_version is not semver": with_defect(tested_version="v1"),
        "unknown status value": with_defect(status="maybe"),
        "missing a required key": manifest(
            [
                {k: v for k, v in repo("contextweaver").items() if k != "role"},
                repo("agent-kernel"),
                repo("ChainWeaver"),
            ]
        ),
    }

    failures = []
    good_errors = validate(good, vm)
    if good_errors:
        failures.append(f"valid manifest was rejected: {good_errors}")
    for label, bad in bad_cases.items():
        if not validate(bad, vm):
            failures.append(f"invalid manifest was accepted: {label}")
    return failures


if __name__ == "__main__":
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        sys.exit(1)
    print("OK: validate_compatibility self-test passed.")
