"""
Tests that verify sample payloads in examples/sample_payloads/ validate
against the corresponding JSON Schemas in contracts/json/.

These tests act as living documentation: if a schema changes in a breaking way,
the sample payloads will fail to validate, catching the regression.
"""

import json
import pathlib
import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
PAYLOADS_DIR = REPO_ROOT / "examples" / "sample_payloads"


def load_schema(name: str) -> dict:
    path = SCHEMA_DIR / f"{name}.schema.json"
    with open(path) as f:
        return json.load(f)


def load_payload(name: str) -> dict:
    path = PAYLOADS_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)


def build_store() -> dict:
    """Build a URI → schema dict for all local schemas, so $ref resolution
    works without network access."""
    store = {}
    for schema_file in SCHEMA_DIR.glob("*.schema.json"):
        with open(schema_file) as f:
            schema = json.load(f)
        if "$id" in schema:
            store[schema["$id"]] = schema
    return store


_SCHEMA_STORE = build_store()


def validate(payload: dict, schema: dict) -> None:
    """Validate payload against schema using a local-only resolver."""
    resolver = jsonschema.RefResolver(
        base_uri=schema.get("$id", ""),
        referrer=schema,
        store=_SCHEMA_STORE,
    )
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(
        schema,
        resolver=resolver,
        format_checker=jsonschema.FormatChecker(),
    )
    errors = [e for e in validator.iter_errors(payload)]
    if errors:
        msgs = "\n".join(str(e) for e in errors)
        raise AssertionError(f"Schema validation failed:\n{msgs}")


class TestSchemaValidJSON:
    """All schema files must be valid JSON."""

    @pytest.mark.parametrize("schema_file", sorted(SCHEMA_DIR.glob("*.schema.json")))
    def test_schema_is_valid_json(self, schema_file):
        with open(schema_file) as f:
            data = json.load(f)
        assert "$id" in data, f"{schema_file.name} must have $id"
        assert "title" in data, f"{schema_file.name} must have title"
        assert "description" in data, f"{schema_file.name} must have description"


class TestRoutingDecisionPayload:
    """routing_decision.json validates against routing_decision schema."""

    def test_payload_validates(self):
        schema = load_schema("routing_decision")
        payload = load_payload("routing_decision")
        validate(payload, schema)

    def test_required_fields_present(self):
        payload = load_payload("routing_decision")
        assert payload.get("id"), "routing_decision payload must have non-empty id"
        assert payload.get("choice_cards"), "routing_decision payload must have choice_cards"
        assert payload.get("timestamp"), "routing_decision payload must have timestamp"


class TestFrameWithHandlesPayload:
    """frame_with_handles.json validates against frame schema."""

    def test_payload_validates(self):
        schema = load_schema("frame")
        payload = load_payload("frame_with_handles")
        validate(payload, schema)

    def test_required_fields_present(self):
        payload = load_payload("frame_with_handles")
        assert payload.get("frame_id"), "frame payload must have non-empty frame_id"
        assert payload.get("capability_id"), "frame payload must have capability_id"
        assert payload.get("summary"), "frame payload must have summary"
        assert payload.get("created_at"), "frame payload must have created_at"

    def test_no_raw_output_field(self):
        """Frames must not contain a 'raw_output' field (invariant I-01 / I-05)."""
        payload = load_payload("frame_with_handles")
        assert "raw_output" not in payload, (
            "Frame must not contain raw_output (invariant: LLM never sees raw tool output)"
        )


class TestCapabilityTokenPayload:
    """capability_token.json validates against capability_token schema."""

    def test_payload_validates(self):
        schema = load_schema("capability_token")
        payload = load_payload("capability_token")
        validate(payload, schema)

    def test_required_fields_present(self):
        payload = load_payload("capability_token")
        assert payload.get("token_id"), "capability_token payload must have non-empty token_id"
        assert payload.get("principal"), "capability_token payload must have principal"
        assert payload.get("scope"), "capability_token payload must have non-empty scope"
        assert payload.get("issued_at"), "capability_token payload must have issued_at"

    def test_scope_is_not_empty(self):
        """Invariant I-06: CapabilityTokens must be scoped."""
        payload = load_payload("capability_token")
        scope = payload.get("scope", [])
        assert len(scope) > 0, "CapabilityToken.scope must not be empty (invariant I-06)"

    def test_invariant_i06_no_expiry_no_single_use_fails(self):
        """Invariant I-06: token without expires_at and without single_use must fail."""
        schema = load_schema("capability_token")
        invalid_payload = {
            "token_id": "tok-invalid",
            "principal": "agent-1",
            "scope": ["cap.search"],
            "issued_at": "2026-03-08T06:00:00Z",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(invalid_payload, schema)
