"""
Tests that Extended sample payloads validate against the Extended JSON
Schemas in contracts/json/extended/.

Mirrors test_json_schema_alignment.py (which covers Core), but targets the
Extended tier. Each Extended type is listed by its dataclass name so the
coverage table generator (scripts/generate_coverage_table.py) detects the
schema-test artifact for that type.
"""

import json

import pytest

pytest.importorskip("jsonschema")

from tests._schema_alignment import (  # noqa: E402
    CORE_SCHEMA_DIR,
    EXTENDED_SCHEMA_DIR,
    load_extended_schema,
    load_payload,
    validate,
)

# (dataclass name, snake_case schema/payload stem). The dataclass names appear
# here as whole tokens so the coverage generator marks the schema test present:
# TelemetryHint, SchemaFingerprint, RedactionPolicy, UIHint, RiskAssessment,
# ExtendedFrameMetadata, ExtendedSelectableItemMetadata,
# ReviewArtifact, MemoryArtifact, SessionHandoff, LessonCard, SkillCard,
# EvaluationArtifact, ArtifactSafetyGateRequest, ArtifactSafetyReport,
# CapabilityTokenSignature, OtelTraceMapping, CompiledFlow,
# ExecutionCandidate, ExecutionRoutingDecision, ExecutionFeedback,
# TraceBundle, FailureCaseArtifact.
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
    ("TraceBundle", "trace_bundle"),
    ("FailureCaseArtifact", "failure_case_artifact"),
    ("ConformanceResult", "conformance_result"),
]


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

    def test_execution_candidate_compiled_flow_on_non_flow_fails(self):
        # compiled_flow is only valid when candidate_type == "flow" (if/then).
        schema = load_extended_schema("execution_candidate")
        bad = {
            "candidate_id": "c1",
            "candidate_type": "tool",
            "compiled_flow": {"flow_id": "f1"},
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

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

    def test_trace_bundle_signed_payload_validates(self):
        # #50: a signed bundle embeds a `signature` resolved via $ref to the
        # CapabilityTokenSignature schema; the nested Core artifacts resolve
        # via the local schema store. The whole document must validate.
        schema = load_extended_schema("trace_bundle")
        payload = load_payload("trace_bundle_signed")
        validate(payload, schema)

    def test_trace_bundle_missing_required_chain_fails(self):
        # #50: the full audit chain is required; a bundle missing the array
        # members must be rejected.
        schema = load_extended_schema("trace_bundle")
        bad = {
            "bundle_id": "tb-1",
            "routing_decision": {
                "id": "rd-1",
                "choice_cards": [
                    {
                        "id": "card-1",
                        "items": [
                            {"id": "i1", "label": "L", "description": "D"}
                        ],
                    }
                ],
                "timestamp": "2026-03-08T06:00:00Z",
            },
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_trace_bundle_bad_canonicalization_fails(self):
        # canonicalization is constrained to the JCS registry.
        schema = load_extended_schema("trace_bundle")
        bad = {
            "bundle_id": "tb-1",
            "routing_decision": {
                "id": "rd-1",
                "choice_cards": [
                    {"id": "c1", "items": [{"id": "i1", "label": "L", "description": "D"}]}
                ],
                "timestamp": "2026-03-08T06:00:00Z",
            },
            "policy_decisions": [],
            "frames": [],
            "handles": [],
            "trace_events": [],
            "canonicalization": "sorted-keys",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_failure_case_artifact_missing_required_fails(self):
        # #72: failure_case_id/created_at/source_project/property_name/status
        # are all required.
        schema = load_extended_schema("failure_case_artifact")
        bad = {"failure_case_id": "fc-1"}
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_failure_case_artifact_bad_status_fails(self):
        schema = load_extended_schema("failure_case_artifact")
        bad = {
            "failure_case_id": "fc-1",
            "created_at": "2026-05-28T14:12:00Z",
            "source_project": "ChainWeaver",
            "property_name": "p",
            "status": "open",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_failure_case_artifact_bad_severity_fails(self):
        schema = load_extended_schema("failure_case_artifact")
        bad = {
            "failure_case_id": "fc-1",
            "created_at": "2026-05-28T14:12:00Z",
            "source_project": "ChainWeaver",
            "property_name": "p",
            "status": "candidate",
            "severity": "extreme",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_conformance_result_bad_status_fails(self):
        # #116: status is constrained to pass|fail.
        schema = load_extended_schema("conformance_result")
        bad = {
            "result_version": "1",
            "contract_version": "0.8.0",
            "mode": "corpus",
            "target": None,
            "status": "maybe",
            "checks_run": 1,
            "failures": 0,
            "generated_at": "2026-07-05T12:00:00Z",
            "runner": "weaver-spec conformance/run.py",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_conformance_result_bad_failure_record_fails(self):
        # #145: each failure_record needs a kind from the enum and a message.
        schema = load_extended_schema("conformance_result")
        bad = {
            "result_version": "1",
            "contract_version": "0.8.0",
            "mode": "corpus",
            "target": None,
            "status": "fail",
            "checks_run": 1,
            "failures": 1,
            "failure_records": [{"kind": "not-a-kind", "message": "x"}],
            "generated_at": "2026-07-05T12:00:00Z",
            "runner": "weaver-spec conformance/run.py",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)
