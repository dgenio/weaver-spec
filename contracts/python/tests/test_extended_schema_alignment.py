"""
Tests that Extended sample payloads validate against the Extended JSON
Schemas in contracts/json/extended/.

Mirrors test_json_schema_alignment.py (which covers Core), but targets the
Extended tier. Each Extended type is listed by its dataclass name so the
coverage table generator (scripts/generate_coverage_table.py) detects the
schema-test artifact for that type.
"""

import json
import pathlib

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
CORE_SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
EXTENDED_SCHEMA_DIR = CORE_SCHEMA_DIR / "extended"
PAYLOADS_DIR = REPO_ROOT / "examples" / "sample_payloads"

# (dataclass name, snake_case schema/payload stem). The dataclass names appear
# here as whole tokens so the coverage generator marks the schema test present:
# TelemetryHint, SchemaFingerprint, RedactionPolicy, UIHint, RiskAssessment,
# ExtendedFrameMetadata, ExtendedSelectableItemMetadata,
# ReviewArtifact, MemoryArtifact, SessionHandoff, LessonCard, SkillCard,
# EvaluationArtifact, ArtifactSafetyGateRequest, ArtifactSafetyReport,
# CapabilityTokenSignature, OtelTraceMapping, CompiledFlow,
# ExecutionCandidate, ExecutionRoutingDecision, ExecutionFeedback.
EXTENDED_TYPES = [
    ("TelemetryHint", "telemetry_hint"),
    ("SchemaFingerprint", "schema_fingerprint"),
    ("RedactionPolicy", "redaction_policy"),
    ("UIHint", "ui_hint"),
    ("RiskAssessment", "risk_assessment"),
    ("ExtendedFrameMetadata", "extended_frame_metadata"),
    ("ExtendedSelectableItemMetadata", "extended_selectable_item_metadata"),
    ("ReviewArtifact", "review_artifact"),
    ("MemoryArtifact", "memory_artifact"),
    ("SessionHandoff", "session_handoff"),
    ("LessonCard", "lesson_card"),
    ("SkillCard", "skill_card"),
    ("EvaluationArtifact", "evaluation_artifact"),
    ("ArtifactSafetyGateRequest", "artifact_safety_gate_request"),
    ("ArtifactSafetyReport", "artifact_safety_report"),
    ("CapabilityTokenSignature", "capability_token_signature"),
    ("OtelTraceMapping", "otel_trace_mapping"),
    ("CompiledFlow", "compiled_flow"),
    ("ExecutionCandidate", "execution_candidate"),
    ("ExecutionRoutingDecision", "execution_routing_decision"),
    ("ExecutionFeedback", "execution_feedback"),
]


def load_extended_schema(stem: str) -> dict:
    with open(EXTENDED_SCHEMA_DIR / f"{stem}.schema.json") as f:
        return json.load(f)


def load_payload(stem: str) -> dict:
    with open(PAYLOADS_DIR / f"{stem}.json") as f:
        return json.load(f)


def build_store() -> dict:
    """URI -> schema for all local schemas (Core + Extended), so $ref
    resolution works without network access."""
    store = {}
    for schema_file in list(CORE_SCHEMA_DIR.glob("*.schema.json")) + list(
        EXTENDED_SCHEMA_DIR.glob("*.schema.json")
    ):
        with open(schema_file) as f:
            schema = json.load(f)
        if "$id" in schema:
            store[schema["$id"]] = schema
    return store


_SCHEMA_STORE = build_store()


def validate(payload: dict, schema: dict) -> None:
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
    errors = list(validator.iter_errors(payload))
    if errors:
        msgs = "\n".join(str(e) for e in errors)
        raise AssertionError(f"Schema validation failed:\n{msgs}")


class TestExtendedSchemaStructure:
    """Every Extended schema must declare the required metadata fields."""

    @pytest.mark.parametrize(
        "schema_file", sorted(EXTENDED_SCHEMA_DIR.glob("*.schema.json"))
    )
    def test_schema_has_required_metadata(self, schema_file):
        with open(schema_file) as f:
            data = json.load(f)
        for key in ("$id", "title", "description", "required"):
            assert key in data, f"{schema_file.name} must declare {key}"
        assert "extended/" in data["$id"], (
            f"{schema_file.name} $id must live under the extended/ namespace"
        )


class TestExtendedPayloadValidation:
    """Each Extended sample payload validates against its schema."""

    @pytest.mark.parametrize("class_name,stem", EXTENDED_TYPES)
    def test_payload_validates(self, class_name, stem):
        schema = load_extended_schema(stem)
        payload = load_payload(stem)
        validate(payload, schema)


class TestExtendedNegativeCases:
    """A few targeted negatives confirm the schemas actually constrain."""

    def test_memory_artifact_missing_required_fails(self):
        schema = load_extended_schema("memory_artifact")
        bad = {"memory_id": "m1"}  # missing memory_type/content/source/created_at
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_evaluation_artifact_bad_support_state_fails(self):
        schema = load_extended_schema("evaluation_artifact")
        bad = {
            "artifact_id": "e1",
            "producer": "skdr-eval",
            "created_at": "2026-05-27T10:00:00Z",
            "support_state": "explosive",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_evaluation_artifact_high_risk_deploy_fails(self):
        # #67: a high-risk evaluation is not deployment evidence. The schema
        # must reject this pairing, matching the Python dataclass constraint.
        schema = load_extended_schema("evaluation_artifact")
        bad = {
            "artifact_id": "e1",
            "producer": "skdr-eval",
            "created_at": "2026-05-27T10:00:00Z",
            "support_state": "high_risk",
            "recommendation_kind": "deploy",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_artifact_safety_report_bad_decision_fails(self):
        schema = load_extended_schema("artifact_safety_report")
        bad = {
            "report_id": "r1",
            "gate_id": "g1",
            "decision": "maybe",
            "created_at": "2026-05-27T10:30:00Z",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_risk_assessment_invalid_level_fails(self):
        schema = load_extended_schema("risk_assessment")
        bad = {"risk_level": "extreme"}
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_schema_fingerprint_missing_required_fails(self):
        schema = load_extended_schema("schema_fingerprint")
        bad = {"schema_version": "0.6.0"}  # missing schema_id
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_capability_token_signature_unknown_alg_fails(self):
        # #44: verifiers MUST reject signatures whose alg is not in the
        # registry. The schema enforces this with an enum constraint.
        schema = load_extended_schema("capability_token_signature")
        bad = {"alg": "rsa-pkcs1", "kid": "k1", "sig": "abc"}
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_capability_token_signature_unknown_canonicalization_fails(self):
        # #44: canonicalization must be JCS (RFC 8785); other forms are not
        # in the registry and must be rejected.
        schema = load_extended_schema("capability_token_signature")
        bad = {
            "alg": "ed25519",
            "kid": "k1",
            "sig": "abc",
            "canonicalization": "sorted-keys",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_capability_token_signed_payload_validates(self):
        # The signed CapabilityToken sample carries `x_weaver_signature` as
        # a namespaced extension; the Core schema accepts extra properties
        # so a signed token must remain valid against capability_token.
        with open(CORE_SCHEMA_DIR / "capability_token.schema.json") as f:
            schema = json.load(f)
        payload = load_payload("capability_token_signed")
        validate(payload, schema)

        # The embedded signature itself must validate against the Extended
        # signature schema.
        sig_schema = load_extended_schema("capability_token_signature")
        validate(payload["x_weaver_signature"], sig_schema)

    def test_otel_trace_mapping_bad_span_kind_fails(self):
        schema = load_extended_schema("otel_trace_mapping")
        bad = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "span_kind": "DOWNSTREAM",  # not a SpanKind
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_otel_trace_mapping_bad_trace_id_length_fails(self):
        # W3C Trace Context: trace_id is exactly 32 hex chars.
        schema = load_extended_schema("otel_trace_mapping")
        bad = {
            "trace_id": "deadbeef",  # too short
            "span_id": "00f067aa0ba902b7",
            "span_kind": "INTERNAL",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_otel_trace_mapping_uppercase_trace_id_fails(self):
        # W3C Trace Context requires lowercase hex; the schema pattern must
        # reject uppercase even though chars are hex-valid.
        schema = load_extended_schema("otel_trace_mapping")
        bad = {
            "trace_id": "4BF92F3577B34DA6A3CE929D0E0E4736",
            "span_id": "00f067aa0ba902b7",
            "span_kind": "INTERNAL",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_extended_frame_metadata_confidence_score_above_range_fails(self):
        # Description claims [0.0, 1.0]; schema must enforce both bounds.
        schema = load_extended_schema("extended_frame_metadata")
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate({"confidence_score": 1.5}, schema)

    def test_extended_frame_metadata_confidence_score_below_range_fails(self):
        schema = load_extended_schema("extended_frame_metadata")
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate({"confidence_score": -0.1}, schema)

    def test_extended_selectable_item_negative_duration_fails(self):
        # Schema declares `minimum: 0` on estimated_duration_ms.
        schema = load_extended_schema("extended_selectable_item_metadata")
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate({"estimated_duration_ms": -1}, schema)

    def test_capability_token_signature_wrong_length_sig_fails(self):
        # docs/SIGNING.md fixes both registered algorithms at 64 raw bytes,
        # which is 86 base64url chars without padding. Anything else (DER-
        # encoded ECDSA, RSA, truncated, etc.) is structurally invalid and
        # the schema pattern must reject it before crypto verification runs.
        schema = load_extended_schema("capability_token_signature")
        bad = {
            "alg": "ed25519",
            "kid": "k1",
            "sig": "A" * 50,  # base64url alphabet, wrong length
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_compiled_flow_missing_required_fails(self):
        # #66: flow_id is the only required field.
        schema = load_extended_schema("compiled_flow")
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate({"name": "no id"}, schema)

    def test_compiled_flow_invalid_sensitivity_fails(self):
        # sensitivity must be one of the shared artifact sensitivity levels.
        schema = load_extended_schema("compiled_flow")
        bad = {"flow_id": "f1", "sensitivity": "top-secret"}
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_execution_candidate_invalid_type_fails(self):
        # #61 open question 1 settled: candidate_type is a fixed enum.
        schema = load_extended_schema("execution_candidate")
        bad = {"candidate_id": "c1", "candidate_type": "macro"}
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_execution_candidate_with_compiled_flow_validates(self):
        # candidate_type=flow may embed a CompiledFlow via $ref; this must
        # resolve against the local schema store and validate.
        schema = load_extended_schema("execution_candidate")
        payload = load_payload("execution_candidate")
        validate(payload, schema)

    def test_execution_routing_decision_missing_candidate_fails(self):
        # candidate is required; a decision without one is invalid.
        schema = load_extended_schema("execution_routing_decision")
        bad = {"decision_id": "dec_1"}
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_execution_routing_decision_confidence_above_range_fails(self):
        # #61 open question 2 settled: confidence is standardized to [0.0, 1.0].
        schema = load_extended_schema("execution_routing_decision")
        bad = {
            "decision_id": "dec_1",
            "candidate": {"candidate_id": "c1", "candidate_type": "tool"},
            "confidence": 1.5,
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_execution_feedback_missing_required_fails(self):
        schema = load_extended_schema("execution_feedback")
        bad = {"decision_id": "dec_1", "candidate_id": "c1"}  # no success/timestamp
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_execution_feedback_negative_latency_fails(self):
        schema = load_extended_schema("execution_feedback")
        bad = {
            "decision_id": "dec_1",
            "candidate_id": "c1",
            "success": True,
            "timestamp": "2026-05-25T08:00:00Z",
            "latency_ms": -1,
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)
