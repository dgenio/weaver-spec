"""Tests for the weaver-stack meta-package consistency check (issue #80).

The validator lives outside the ``weaver_contracts`` package (build-time CI
tooling, never shipped), so it is loaded by path rather than imported — the same
pattern as ``test_conformance.py``.
"""

import importlib.util
import pathlib

import yaml

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PY = REPO_ROOT / "scripts" / "validate_meta_package.py"
MANIFEST = REPO_ROOT / "compatibility.yaml"
META_PYPROJECT = REPO_ROOT / "packaging" / "weaver-stack" / "pyproject.toml"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_meta_package", VALIDATOR_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vmp = _load_validator()


def test_self_test_passes():
    assert vmp.self_test() == []


def test_live_manifest_and_meta_package_are_consistent():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    pyproject = tomllib.loads(META_PYPROJECT.read_text(encoding="utf-8"))
    assert vmp.validate(manifest, pyproject) == []


def test_meta_package_pins_weaver_contracts_and_has_empty_runtime_today():
    pyproject = tomllib.loads(META_PYPROJECT.read_text(encoding="utf-8"))
    project = pyproject["project"]
    assert project["name"] == "weaver-stack"
    base = {vmp._req_name(r) for r in project["dependencies"]}
    assert "weaver_contracts" in base
    # All siblings are still unverified in compatibility.yaml.
    assert project["optional-dependencies"]["runtime"] == []


def test_expected_pins_track_test_backed_siblings():
    backed = {
        "schema_version": 1,
        "repositories": [
            {"name": "contextweaver", "status": "verified", "tested_version": "0.3.0"},
            {"name": "ChainWeaver", "status": "unverified", "tested_version": None},
        ],
    }
    assert vmp.expected_runtime_pins(backed) == {"contextweaver": "0.3.0"}
