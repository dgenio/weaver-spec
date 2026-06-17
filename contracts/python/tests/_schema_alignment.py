"""Shared schema-alignment harness for the contract test suite.

Single home for the registry/validation boilerplate consumed by the Core
(``test_json_schema_alignment.py``) and Extended
(``test_extended_schema_alignment.py``) alignment modules. It builds one
``referencing.Registry`` over every local schema and validates with
``Draft202012Validator`` — the same modern pattern the conformance runner uses
(``conformance/run.py:load_schemas``), replacing the deprecated
``jsonschema.RefResolver`` the alignment tests used before (issues #113, #114).

This is a helper, not a test module: the leading underscore keeps pytest from
collecting it.
"""

from __future__ import annotations

import json
import pathlib

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CORE_SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
EXTENDED_SCHEMA_DIR = CORE_SCHEMA_DIR / "extended"
PAYLOADS_DIR = REPO_ROOT / "examples" / "sample_payloads"


def _read_json(path: pathlib.Path) -> dict:
    """Parse a JSON file, annotating parse errors with the path.

    ``build_registry`` runs at import time, so a malformed schema would
    otherwise surface as a bare ``JSONDecodeError`` during pytest collection
    with no indication of which file is broken. Stdlib-only.
    """
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def build_registry() -> Registry:
    """Preload every Core + Extended schema by ``$id`` so cross-schema ``$ref``s
    resolve offline (no network), mirroring ``conformance/run.py:load_schemas``."""
    registry: Registry = Registry()
    for path in sorted(CORE_SCHEMA_DIR.glob("*.schema.json")) + sorted(
        EXTENDED_SCHEMA_DIR.glob("*.schema.json")
    ):
        schema = _read_json(path)
        if "$id" in schema:
            registry = registry.with_resource(
                uri=schema["$id"],
                resource=Resource(contents=schema, specification=DRAFT202012),
            )
    return registry


REGISTRY = build_registry()


def load_core_schema(stem: str) -> dict:
    return _read_json(CORE_SCHEMA_DIR / f"{stem}.schema.json")


def load_extended_schema(stem: str) -> dict:
    return _read_json(EXTENDED_SCHEMA_DIR / f"{stem}.schema.json")


def load_payload(stem: str) -> dict:
    return _read_json(PAYLOADS_DIR / f"{stem}.json")


def validate(payload: dict, schema: dict) -> None:
    """Validate ``payload`` against ``schema`` using the preloaded registry for
    offline ``$ref`` resolution and full format checking.

    Raises ``AssertionError`` listing every error on failure, preserving the
    ``"Schema validation failed:"`` prefix the negative-case tests match on.
    """
    validator = Draft202012Validator(
        schema,
        registry=REGISTRY,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    errors = list(validator.iter_errors(payload))
    if errors:
        msgs = "\n".join(str(e) for e in errors)
        raise AssertionError(f"Schema validation failed:\n{msgs}")
