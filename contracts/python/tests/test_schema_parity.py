"""
Mechanical dataclass <-> JSON Schema parity for Core and Extended contracts
(issues #111, #112).

AGENTS.md ("Source of truth: schemas lead") requires the Python types to mirror
their JSON Schemas exactly — same field names, same required/optional status,
same type shape, zero divergence. The payload-validation tests
(test_json_schema_alignment.py / test_extended_schema_alignment.py) only check
that *sample payloads* validate, so a dataclass could add, rename, or retype a
field without any test failing. This module turns the mirroring rule into a
mechanical guarantee for every type that has a schema.

Authority is schema-led for both tiers now that every Extended type has a schema
(see docs/CONTRACT_REFERENCE.md). The type-shape comparison is deliberately
coarse — container kind plus nullability — to catch real drift without flagging
benign annotation differences.
"""

from __future__ import annotations

import dataclasses
import re
import typing
from datetime import datetime

import pytest

# The shared helper imports jsonschema + referencing at module load, so skip
# gracefully (as the other alignment modules do) when the dev extras are absent.
pytest.importorskip("jsonschema")
pytest.importorskip("referencing")

import weaver_contracts.core as core  # noqa: E402
import weaver_contracts.extended as extended  # noqa: E402
from tests._schema_alignment import load_core_schema, load_extended_schema  # noqa: E402

# Fields that back a schema's `additionalProperties: true` extension bag rather
# than a declared property. Allowed to be absent from `properties` either way.
EXTENSION_BAG_FIELDS = frozenset({"metadata", "extra"})


def _camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _dataclasses_in(module) -> list[type]:
    """@dataclass types *defined* in this module (not imported into it)."""
    return [
        obj
        for obj in vars(module).values()
        if isinstance(obj, type)
        and dataclasses.is_dataclass(obj)
        and obj.__module__ == module.__name__
    ]


CORE_TYPES = [(cls, _camel_to_snake(cls.__name__), "core") for cls in _dataclasses_in(core)]
EXTENDED_TYPES = [
    (cls, _camel_to_snake(cls.__name__), "extended") for cls in _dataclasses_in(extended)
]
ALL_TYPES = CORE_TYPES + EXTENDED_TYPES
_IDS = [cls.__name__ for cls, _stem, _tier in ALL_TYPES]


def _load_schema(stem: str, tier: str) -> dict:
    return load_core_schema(stem) if tier == "core" else load_extended_schema(stem)


def _dataclass_fields(cls: type) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


def _dataclass_required(cls: type) -> set[str]:
    """Dataclass fields with no default and no default_factory are required."""
    return {
        f.name
        for f in dataclasses.fields(cls)
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
    }


def _strip_optional(annotation):
    if typing.get_origin(annotation) is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _dataclass_kind(annotation) -> str | None:
    """Coarse JSON-Schema-style kind for a Python annotation, or None if unknown."""
    annotation = _strip_optional(annotation)
    origin = typing.get_origin(annotation)
    if origin in (list, typing.List):
        return "array"
    if origin in (dict, typing.Dict):
        return "object"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation in (str, datetime):
        return "string"
    if dataclasses.is_dataclass(annotation):
        return "object"
    return None


def _schema_kinds(prop: dict) -> set[str]:
    """Non-null JSON Schema types for a property (handles $ref / anyOf / type list)."""
    if "type" in prop:
        types = prop["type"]
        types = [types] if isinstance(types, str) else types
        return {t for t in types if t != "null"}
    if "$ref" in prop:
        return {"object"}
    if "anyOf" in prop:
        out: set[str] = set()
        for sub in prop["anyOf"]:
            out |= _schema_kinds(sub)
        return out
    return set()


@pytest.mark.parametrize("cls,stem,tier", ALL_TYPES, ids=_IDS)
def test_every_type_has_a_schema(cls, stem, tier):
    """Schema-led authority: every Core and Extended dataclass has a schema."""
    schema = _load_schema(stem, tier)
    assert schema.get("title") == cls.__name__, (
        f"{cls.__name__}: schema title {schema.get('title')!r} should match the class name"
    )


@pytest.mark.parametrize("cls,stem,tier", ALL_TYPES, ids=_IDS)
def test_field_name_parity(cls, stem, tier):
    """Every dataclass field maps to a schema property and vice versa."""
    schema = _load_schema(stem, tier)
    props = set(schema.get("properties", {}))
    fields = _dataclass_fields(cls)

    # The extension bag (metadata/extra) may be modelled via additionalProperties
    # rather than a declared property; namespaced x_* keys are extension points.
    missing_in_schema = fields - props - EXTENSION_BAG_FIELDS
    extra_in_schema = {p for p in (props - fields) if not p.startswith("x_")}

    assert not missing_in_schema, (
        f"{cls.__name__}: dataclass fields absent from schema properties: "
        f"{sorted(missing_in_schema)}"
    )
    assert not extra_in_schema, (
        f"{cls.__name__}: schema properties absent from dataclass: "
        f"{sorted(extra_in_schema)}"
    )


@pytest.mark.parametrize("cls,stem,tier", ALL_TYPES, ids=_IDS)
def test_required_parity(cls, stem, tier):
    """Required/optional status matches between dataclass and schema."""
    schema = _load_schema(stem, tier)
    schema_required = set(schema.get("required", []))
    dataclass_required = _dataclass_required(cls)
    assert dataclass_required == schema_required, (
        f"{cls.__name__}: required-field divergence — "
        f"dataclass-only {sorted(dataclass_required - schema_required)}, "
        f"schema-only {sorted(schema_required - dataclass_required)}"
    )


@pytest.mark.parametrize("cls,stem,tier", ALL_TYPES, ids=_IDS)
def test_type_shape(cls, stem, tier):
    """Coarse type-shape parity (container kind + scalar family) per shared field."""
    schema = _load_schema(stem, tier)
    props = schema.get("properties", {})
    hints = typing.get_type_hints(cls)

    mismatches = []
    for field in dataclasses.fields(cls):
        if field.name in EXTENSION_BAG_FIELDS or field.name not in props:
            continue
        dc_kind = _dataclass_kind(hints[field.name])
        schema_kinds = _schema_kinds(props[field.name])
        if dc_kind is None or not schema_kinds:
            continue  # nothing meaningful to compare (e.g. enum-only / unknown)
        ok = dc_kind in schema_kinds or (dc_kind == "integer" and "number" in schema_kinds)
        if not ok:
            mismatches.append(
                f"{field.name}: dataclass {dc_kind} vs schema {sorted(schema_kinds)}"
            )
    assert not mismatches, f"{cls.__name__}: type-shape mismatches: {mismatches}"


def test_parity_check_detects_drift():
    """Self-check: the parity logic flags a dataclass field with no schema match.

    Guards against the parity test silently passing because the comparison
    became a no-op (issue #111 test plan).
    """

    @dataclasses.dataclass
    class _Drifted:
        token_id: str
        principal: str
        scope: list
        issued_at: str
        bogus_extra: str = "x"

    schema = load_core_schema("capability_token")
    props = set(schema.get("properties", {}))
    fields = _dataclass_fields(_Drifted)
    missing_in_schema = fields - props - EXTENSION_BAG_FIELDS
    assert "bogus_extra" in missing_in_schema
