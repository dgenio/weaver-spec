"""Extension-field (`x_` namespacing) convention tests (issue #160).

The documented convention (CONTRACT_REFERENCE.md): Core schemas accept
additional properties, adopter/extension keys must be `x_`-prefixed, and the
spec reserves the unprefixed namespace. These tests enforce that convention
generically across every Core schema rather than for one hand-picked field.
"""

import json
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")

from jsonschema import Draft202012Validator  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_DIR = REPO_ROOT / "contracts" / "json"


def _core_schemas():
    return sorted(CORE_DIR.glob("*.schema.json"))


def test_core_schemas_allow_additional_properties():
    for path in _core_schemas():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("additionalProperties", True) is not False, (
            f"{path.name} forbids additionalProperties, breaking the x_ convention"
        )


def test_x_prefixed_extension_key_validates_against_core_schema():
    schema = json.loads((CORE_DIR / "frame.schema.json").read_text())
    v = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    payload = {
        "frame_id": "f1",
        "capability_id": "c1",
        "summary": "ok",
        "created_at": "2026-07-10T12:00:00Z",
        "x_myorg_trace_url": "https://example.com/t/1",
    }
    assert not list(v.iter_errors(payload))


def test_every_schema_declares_reserved_x_weaver_stability():
    # x_weaver_stability is a reserved spec-level extension key on every schema.
    for path in CORE_DIR.rglob("*.schema.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("x_weaver_stability") in ("stable", "experimental", "deprecated")


def test_no_declared_property_uses_the_reserved_unprefixed_namespace():
    # The spec reserves unprefixed names; no *declared* property may start with x_
    # unless it is a documented reserved key. This guards against accidentally
    # shipping an adopter-style x_ field as a first-class contract property.
    reserved = {"x_weaver_stability", "x_weaver_signature"}
    for path in CORE_DIR.rglob("*.schema.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for prop in (data.get("properties") or {}):
            if prop.startswith("x_"):
                assert prop in reserved, f"{path.name}: unexpected x_ property {prop!r}"
