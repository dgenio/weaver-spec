#!/usr/bin/env python3
"""Stdlib-only consistency check for the ``weaver-stack`` meta-package (issue #80).

The umbrella meta-package (``packaging/weaver-stack/pyproject.toml``) is the
*executable form* of the compatibility promise: its ``runtime`` extra must pin
exactly the sibling repositories that ``compatibility.yaml`` marks as
test-backed (status ``verified``/``provisional`` **with** a ``tested_version``),
and must never pin a sibling that is still ``unverified``/``incompatible``. That
keeps ``pip install weaver-stack[runtime]`` honest — it can only ever resolve to
versions the spec has actually vouched for, never an aspirational pin.

This module is intentionally **pure and parser-free** so it stays within the
``scripts/`` stdlib-only rule (see ``AGENTS.md``). Callers — the
``validate-meta-package`` CI job and the ``meta-package`` pre-commit hook —
parse ``compatibility.yaml`` (YAML) and the meta-package ``pyproject.toml``
(TOML) themselves and pass the parsed mappings into :func:`validate`.

Run directly to execute the validator's self-test::

    python scripts/validate_meta_package.py
"""

import re
import sys

TEST_BACKED = {"verified", "provisional"}

# Repository name (as written in compatibility.yaml) -> distribution name the
# meta-package depends on. Default is the lowercased repo name; override here if
# a sibling ever publishes under a different distribution name.
DIST_NAME = {
    "contextweaver": "contextweaver",
    "agent-kernel": "agent-kernel",
    "ChainWeaver": "chainweaver",
}


def _req_name(requirement):
    """Distribution name from a PEP 508 requirement string (best-effort, stdlib)."""
    head = re.split(r"[<>=!~;\[ ]", str(requirement).strip(), maxsplit=1)[0]
    return head.strip().lower()


def _dist_for(name):
    return DIST_NAME.get(name, str(name).lower())


def _admits_version(requirement, version):
    """Best-effort stdlib check: does ``requirement`` admit ``version``?

    A full PEP 440 parser is out of scope (stdlib-only ``scripts/`` rule), so we
    require the tested version to appear behind an inclusive lower-bound/exact
    operator (``==`` or ``>=``). This rejects pins that *exclude* the tested
    version — e.g. ``contextweaver<0.3.0`` or ``contextweaver>0.3.0`` — which a
    plain substring test (``version in requirement``) would wrongly accept. The
    trailing ``(?!\\d)`` guards against a shorter version matching a longer one
    (e.g. tested ``0.3.0`` against a pin of ``0.3.00``).
    """
    pattern = re.compile(r"(==|>=)\s*" + re.escape(str(version)) + r"(?!\d)")
    return bool(pattern.search(str(requirement)))


def expected_runtime_pins(manifest):
    """Return ``{dist_name: tested_version}`` the runtime extra must pin, from the manifest."""
    expected = {}
    for entry in manifest.get("repositories", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("status") in TEST_BACKED and entry.get("tested_version"):
            expected[_dist_for(entry.get("name"))] = entry["tested_version"]
    return expected


def validate(manifest, pyproject):
    """Return a list of human-readable errors. Empty list means consistent."""
    if not isinstance(manifest, dict):
        return ["compatibility manifest must be a mapping"]
    if not isinstance(pyproject, dict):
        return ["meta-package pyproject must be a mapping"]

    project = pyproject.get("project")
    if not isinstance(project, dict):
        return ["meta-package pyproject is missing a [project] table"]

    errors = []
    if project.get("name") != "weaver-stack":
        errors.append(f"meta-package name must be 'weaver-stack', got {project.get('name')!r}")

    requires_python = str(project.get("requires-python", ""))
    if "<" in requires_python:
        errors.append(
            f"meta-package requires-python must not cap the upper bound: {requires_python!r}"
        )

    # weaver_contracts is the one always-published member; the base install must pin it.
    base_names = {_req_name(r) for r in project.get("dependencies", [])}
    if not ({"weaver_contracts", "weaver-contracts"} & base_names):
        errors.append("meta-package must depend on weaver_contracts in [project].dependencies")

    extras = project.get("optional-dependencies", {})
    if not isinstance(extras, dict):
        return errors + ["optional-dependencies must be a table"]
    runtime = extras.get("runtime", [])
    if not isinstance(runtime, list):
        errors.append("optional-dependencies.runtime must be a list")
        runtime = []

    expected = expected_runtime_pins(manifest)
    known_siblings = {
        _dist_for(e.get("name"))
        for e in manifest.get("repositories", [])
        if isinstance(e, dict)
    }

    # Every test-backed sibling must be pinned with (at least) its tested_version.
    for dist, version in sorted(expected.items()):
        matching = [r for r in runtime if _req_name(r) == dist]
        if not matching:
            errors.append(
                f"runtime extra is missing test-backed sibling {dist!r} "
                f"(compatibility.yaml tested_version {version})"
            )
            continue
        for requirement in matching:
            if not _admits_version(requirement, version):
                errors.append(
                    f"runtime pin {requirement!r} must admit the tested_version "
                    f"{version!r} from compatibility.yaml (use '==' or '>=')"
                )

    # No sibling that is NOT test-backed may be pinned — guards against aspirational pins.
    for requirement in runtime:
        name = _req_name(requirement)
        if name in known_siblings and name not in expected:
            errors.append(
                f"runtime extra pins {name!r}, but compatibility.yaml does not mark it "
                f"verified/provisional with a tested_version — remove it until it is test-backed"
            )

    return errors


def self_test():
    """Accept a consistent pair and reject each single-defect variant.

    Returns a list of failures (empty == all good).
    """

    def repo(name, **overrides):
        base = {
            "name": name,
            "status": "unverified",
            "tested_version": None,
        }
        base.update(overrides)
        return base

    def manifest(repos):
        return {"schema_version": 1, "contract_versions": ["0.6.0"], "repositories": repos}

    def pyproject(runtime, *, name="weaver-stack", requires=">=3.10",
                  deps=("weaver_contracts>=0.6,<0.7",)):
        return {
            "project": {
                "name": name,
                "requires-python": requires,
                "dependencies": list(deps),
                "optional-dependencies": {"runtime": list(runtime), "devtools": []},
            }
        }

    all_unverified = manifest([repo("contextweaver"), repo("agent-kernel"), repo("ChainWeaver")])
    one_verified = manifest(
        [
            repo("contextweaver", status="verified", tested_version="0.3.0"),
            repo("agent-kernel"),
            repo("ChainWeaver"),
        ]
    )

    good_cases = {
        "all unverified -> empty runtime extra": (all_unverified, pyproject([])),
        "verified sibling pinned at tested_version": (
            one_verified,
            pyproject(["contextweaver>=0.3.0"]),
        ),
        "verified sibling pinned exactly (==)": (
            one_verified,
            pyproject(["contextweaver==0.3.0"]),
        ),
    }
    bad_cases = {
        "verified sibling not pinned": (one_verified, pyproject([])),
        "pin omits the tested_version": (one_verified, pyproject(["contextweaver>=0.1.0"])),
        "pin excludes the tested_version (<)": (
            one_verified,
            pyproject(["contextweaver<0.3.0"]),
        ),
        "pin excludes the tested_version (strictly >)": (
            one_verified,
            pyproject(["contextweaver>0.3.0"]),
        ),
        "aspirational pin of unverified sibling": (
            all_unverified,
            pyproject(["chainweaver>=0.1.0"]),
        ),
        "requires-python has an upper cap": (
            all_unverified,
            pyproject([], requires=">=3.10,<4.0"),
        ),
        "wrong package name": (all_unverified, pyproject([], name="weaver_stack")),
        "missing weaver_contracts dependency": (all_unverified, pyproject([], deps=())),
    }

    failures = []
    for label, (man, proj) in good_cases.items():
        problems = validate(man, proj)
        if problems:
            failures.append(f"consistent pair was rejected ({label}): {problems}")
    for label, (man, proj) in bad_cases.items():
        if not validate(man, proj):
            failures.append(f"inconsistent pair was accepted: {label}")
    return failures


if __name__ == "__main__":
    problems = self_test()
    for problem in problems:
        print(f"FAIL (self-test): {problem}", file=sys.stderr)
    if problems:
        sys.exit(1)
    print("OK: validate_meta_package self-test passed.")
