"""
Core schema-alignment tests: every Core sample payload in
examples/sample_payloads/ validates against its JSON Schema in contracts/json/,
plus targeted invariant assertions that document specific Core constraints.

These tests act as living documentation: if a schema changes in a breaking way,
the sample payloads fail to validate, catching the regression.

The registry/validation boilerplate is shared with the Extended tier in
tests/_schema_alignment.py (the modern referencing.Registry pattern, mirroring
conformance/run.py) — issues #113 and #114.
"""

import json

import pytest

pytest.importorskip("jsonschema")

from tests._schema_alignment import (  # noqa: E402
    CORE_SCHEMA_DIR,
    load_core_schema as load_schema,
    load_payload,
    validate,
)

# (dataclass name, schema stem, payload stem). The CamelCase dataclass names
# appear here as whole tokens so scripts/generate_coverage_table.py detects the
# schema-test artifact for every Core type (it scans this file for the token):
# SelectableItem, ChoiceCard, RoutingDecision, Capability, CapabilityToken,
# PolicyDecision, Frame, Handle, TraceEvent.
CORE_TYPES = [
    ("SelectableItem", "selectable_item", "selectable_item"),
    ("ChoiceCard", "choice_card", "choice_card"),
    ("RoutingDecision", "routing_decision", "routing_decision"),
    ("Capability", "capability", "capability"),
    ("CapabilityToken", "capability_token", "capability_token"),
    ("PolicyDecision", "policy_decision", "policy_decision"),
    ("Frame", "frame", "frame_with_handles"),
    ("Handle", "handle", "handle"),
    ("TraceEvent", "trace_event", "trace_event"),
]


class TestSchemaValidJSON:
    """All Core schema files must be valid JSON with the required metadata."""

    @pytest.mark.parametrize("schema_file", sorted(CORE_SCHEMA_DIR.glob("*.schema.json")))
    def test_schema_is_valid_json(self, schema_file):
        with open(schema_file) as f:
            data = json.load(f)
        assert "$id" in data, f"{schema_file.name} must have $id"
        assert "title" in data, f"{schema_file.name} must have title"
        assert "description" in data, f"{schema_file.name} must have description"


class TestCorePayloadValidation:
    """Each Core sample payload validates against its schema and carries the
    schema's required fields as non-empty values."""

    @pytest.mark.parametrize("class_name,schema_stem,payload_stem", CORE_TYPES)
    def test_payload_validates(self, class_name, schema_stem, payload_stem):
        validate(load_payload(payload_stem), load_schema(schema_stem))

    @pytest.mark.parametrize("class_name,schema_stem,payload_stem", CORE_TYPES)
    def test_required_fields_present(self, class_name, schema_stem, payload_stem):
        schema = load_schema(schema_stem)
        payload = load_payload(payload_stem)
        for field_name in schema.get("required", []):
            assert payload.get(field_name) not in (None, "", [], {}), (
                f"{payload_stem} payload must carry non-empty required field "
                f"{field_name!r}"
            )


class TestCoreInvariants:
    """Targeted assertions documenting specific Core constraints (preserved from
    the per-type tests this module replaced)."""

    def test_frame_has_no_raw_output_field(self):
        """Frames must not contain a 'raw_output' field (invariant I-01 / I-05)."""
        payload = load_payload("frame_with_handles")
        assert "raw_output" not in payload, (
            "Frame must not contain raw_output (invariant: LLM never sees raw tool output)"
        )

    def test_capability_token_scope_is_not_empty(self):
        """Invariant I-06: CapabilityTokens must be scoped."""
        scope = load_payload("capability_token").get("scope", [])
        assert len(scope) > 0, "CapabilityToken.scope must not be empty (invariant I-06)"

    def test_capability_token_no_expiry_no_single_use_fails(self):
        """Invariant I-06: token without expires_at and without single_use must fail."""
        invalid_payload = {
            "token_id": "tok-invalid",
            "principal": "agent-1",
            "scope": ["cap.search"],
            "issued_at": "2026-03-08T06:00:00Z",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(invalid_payload, load_schema("capability_token"))

    def test_choice_card_items_within_bounds(self):
        """ChoiceCard schema requires 1..20 items."""
        items = load_payload("choice_card").get("items", [])
        assert 1 <= len(items) <= 20, "choice_card.items must be 1..20"

    def test_policy_decision_is_allow_or_deny(self):
        assert load_payload("policy_decision")["decision"] in ("allow", "deny")

    def test_handle_byte_size_non_negative(self):
        payload = load_payload("handle")
        if payload.get("byte_size") is not None:
            assert payload["byte_size"] >= 0

    def test_trace_event_type_in_schema_enum(self):
        """Sample event_type must be one of the values declared in the schema.

        Sourced from the loaded schema so the schema's enum remains the single
        source of truth (no drift between test and schema).
        """
        schema = load_schema("trace_event")
        payload = load_payload("trace_event")
        assert payload["event_type"] in schema["properties"]["event_type"]["enum"]
