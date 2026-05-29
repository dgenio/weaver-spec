"""Tests for Extended contract dataclasses and sample payload construction."""

import json
import pathlib
from dataclasses import asdict
from datetime import datetime
from typing import Optional

import pytest

from weaver_contracts.core import (
    ChoiceCard,
    Frame,
    Handle,
    PolicyDecision,
    RoutingDecision,
    SelectableItem,
    TraceEvent,
)
from weaver_contracts.extended import (
    ArtifactSafetyGateRequest,
    ArtifactSafetyReport,
    CapabilityTokenSignature,
    CompiledFlow,
    EvaluationArtifact,
    ExecutionCandidate,
    ExecutionFeedback,
    ExecutionRoutingDecision,
    ExtendedFrameMetadata,
    ExtendedSelectableItemMetadata,
    FailureCaseArtifact,
    LessonCard,
    MemoryArtifact,
    OtelTraceMapping,
    RedactionPolicy,
    ReviewArtifact,
    RiskAssessment,
    SchemaFingerprint,
    SessionHandoff,
    SkillCard,
    TelemetryHint,
    TraceBundle,
    UIHint,
)


def parse_dt(s: str) -> datetime:
    """Parse an ISO 8601 string to a datetime (UTC)."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
PAYLOADS_DIR = REPO_ROOT / "examples" / "sample_payloads"


def load_payload(name: str) -> dict:
    path = PAYLOADS_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)


def build_telemetry_hint(data: Optional[dict]) -> Optional[TelemetryHint]:
    if data is None:
        return None
    return TelemetryHint(
        trace_id=data.get("trace_id"),
        span_id=data.get("span_id"),
        baggage=data.get("baggage", {}),
    )


def build_schema_fingerprint(
    data: Optional[dict],
) -> Optional[SchemaFingerprint]:
    if data is None:
        return None
    return SchemaFingerprint(
        schema_id=data["schema_id"],
        schema_version=data["schema_version"],
        content_hash=data.get("content_hash"),
        hash_algorithm=data.get("hash_algorithm", "sha256"),
    )


def build_redaction_policy(data: Optional[dict]) -> Optional[RedactionPolicy]:
    if data is None:
        return None
    return RedactionPolicy(
        policy_id=data["policy_id"],
        redacted_fields=data.get("redacted_fields", []),
        truncated_fields=data.get("truncated_fields", []),
        redaction_reason=data.get("redaction_reason"),
        pii_detected=data.get("pii_detected", False),
        pii_types=data.get("pii_types", []),
    )


def build_ui_hint(data: Optional[dict]) -> Optional[UIHint]:
    if data is None:
        return None
    return UIHint(
        icon=data.get("icon"),
        color=data.get("color"),
        priority=data.get("priority"),
        group=data.get("group"),
        disabled=data.get("disabled", False),
        tooltip=data.get("tooltip"),
    )


def build_risk_assessment(data: Optional[dict]) -> Optional[RiskAssessment]:
    if data is None:
        return None
    return RiskAssessment(
        risk_level=data.get("risk_level", "low"),
        risk_reasons=data.get("risk_reasons", []),
        requires_human_approval=data.get("requires_human_approval", False),
        approval_principal=data.get("approval_principal"),
        mitigations=data.get("mitigations", []),
    )


class TestTelemetryHint:
    def test_valid_from_payload(self):
        payload = load_payload("telemetry_hint")
        hint = build_telemetry_hint(payload)
        assert hint is not None
        assert hint.trace_id == payload["trace_id"]
        assert hint.span_id == payload["span_id"]
        assert hint.baggage["tenant"] == "acme"

    def test_defaults_allow_empty_values(self):
        hint = TelemetryHint()
        assert hint.trace_id is None
        assert hint.span_id is None
        assert hint.baggage == {}

    def test_serialization(self):
        hint = TelemetryHint(
            trace_id="trace-1",
            span_id="span-1",
            baggage={"k": "v"},
        )
        data = asdict(hint)
        json.dumps(data)
        assert data["baggage"]["k"] == "v"


class TestSchemaFingerprint:
    def test_valid_from_payload(self):
        payload = load_payload("schema_fingerprint")
        fp = build_schema_fingerprint(payload)
        assert fp is not None
        assert fp.schema_id == payload["schema_id"]
        assert fp.schema_version == payload["schema_version"]

    def test_empty_schema_id_raises(self):
        with pytest.raises(ValueError, match="schema_id must be non-empty"):
            SchemaFingerprint(schema_id="", schema_version="0.1.1")

    def test_empty_schema_version_raises(self):
        with pytest.raises(ValueError, match="schema_version must be non-empty"):
            SchemaFingerprint(schema_id="s", schema_version="")

    def test_serialization(self):
        fp = SchemaFingerprint(schema_id="s", schema_version="1.0.0")
        data = asdict(fp)
        json.dumps(data)
        assert data["hash_algorithm"] == "sha256"


class TestRedactionPolicy:
    def test_valid_from_payload(self):
        payload = load_payload("redaction_policy")
        policy = build_redaction_policy(payload)
        assert policy is not None
        assert policy.policy_id == payload["policy_id"]
        assert policy.pii_detected is True

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValueError, match="policy_id must be non-empty"):
            RedactionPolicy(policy_id="")

    def test_serialization(self):
        policy = RedactionPolicy(policy_id="rp-1", redacted_fields=["secret"])
        data = asdict(policy)
        json.dumps(data)
        assert data["redacted_fields"] == ["secret"]


class TestUIHint:
    def test_valid_from_payload(self):
        payload = load_payload("ui_hint")
        hint = build_ui_hint(payload)
        assert hint is not None
        assert hint.icon == payload["icon"]
        assert hint.priority == payload["priority"]

    def test_defaults(self):
        hint = UIHint()
        assert hint.disabled is False
        assert hint.tooltip is None

    def test_serialization(self):
        hint = UIHint(icon="bolt", disabled=True)
        data = asdict(hint)
        json.dumps(data)
        assert data["disabled"] is True


class TestRiskAssessment:
    def test_valid_from_payload(self):
        payload = load_payload("risk_assessment")
        risk = build_risk_assessment(payload)
        assert risk is not None
        assert risk.risk_level == "medium"
        assert risk.requires_human_approval is True

    def test_invalid_risk_level_raises(self):
        with pytest.raises(ValueError, match="risk_level must be one of"):
            RiskAssessment(risk_level="unknown")

    def test_serialization(self):
        risk = RiskAssessment(risk_level="low", risk_reasons=["read-only"])
        data = asdict(risk)
        json.dumps(data)
        assert data["risk_reasons"] == ["read-only"]


class TestExtendedFrameMetadata:
    def test_valid_from_payload(self):
        payload = load_payload("extended_frame_metadata")
        metadata = ExtendedFrameMetadata(
            redaction_policy=build_redaction_policy(
                payload.get("redaction_policy")
            ),
            telemetry=build_telemetry_hint(payload.get("telemetry")),
            schema_fingerprint=build_schema_fingerprint(
                payload.get("schema_fingerprint")
            ),
            confidence_score=payload.get("confidence_score"),
            source_capability_version=payload.get("source_capability_version"),
            extra=payload.get("extra", {}),
        )
        assert metadata.redaction_policy is not None
        assert metadata.redaction_policy.policy_id == "rp-safe-default"
        assert metadata.telemetry is not None
        assert metadata.telemetry.trace_id == "trace-20260308-002"

    def test_defaults(self):
        metadata = ExtendedFrameMetadata()
        assert metadata.redaction_policy is None
        assert metadata.telemetry is None
        assert metadata.extra == {}

    def test_serialization(self):
        metadata = ExtendedFrameMetadata(
            telemetry=TelemetryHint(trace_id="trace-3"),
            extra={"region": "eu-west-1"},
        )
        data = asdict(metadata)
        json.dumps(data)
        assert data["telemetry"]["trace_id"] == "trace-3"

    def test_confidence_score_boundaries_accepted(self):
        # Inclusive boundaries — 0.0 and 1.0 are valid.
        ExtendedFrameMetadata(confidence_score=0.0)
        ExtendedFrameMetadata(confidence_score=1.0)

    def test_confidence_score_below_range_raises(self):
        with pytest.raises(ValueError, match=r"confidence_score must be in \[0\.0, 1\.0\]"):
            ExtendedFrameMetadata(confidence_score=-0.01)

    def test_confidence_score_above_range_raises(self):
        with pytest.raises(ValueError, match=r"confidence_score must be in \[0\.0, 1\.0\]"):
            ExtendedFrameMetadata(confidence_score=1.01)


class TestExtendedSelectableItemMetadata:
    def test_valid_from_payload(self):
        payload = load_payload("extended_selectable_item_metadata")
        metadata = ExtendedSelectableItemMetadata(
            ui_hint=build_ui_hint(payload.get("ui_hint")),
            risk_assessment=build_risk_assessment(
                payload.get("risk_assessment")
            ),
            estimated_duration_ms=payload.get("estimated_duration_ms"),
            requires_confirmation=payload.get("requires_confirmation", False),
            extra=payload.get("extra", {}),
        )
        assert metadata.ui_hint is not None
        assert metadata.ui_hint.icon == "rocket"
        assert metadata.risk_assessment is not None
        assert metadata.risk_assessment.risk_level == "low"

    def test_defaults(self):
        metadata = ExtendedSelectableItemMetadata()
        assert metadata.ui_hint is None
        assert metadata.risk_assessment is None
        assert metadata.requires_confirmation is False

    def test_serialization(self):
        metadata = ExtendedSelectableItemMetadata(
            ui_hint=UIHint(icon="wand"),
            estimated_duration_ms=500,
        )
        data = asdict(metadata)
        json.dumps(data)
        assert data["estimated_duration_ms"] == 500

    def test_estimated_duration_ms_zero_accepted(self):
        # Boundary — zero is valid (instant operation).
        ExtendedSelectableItemMetadata(estimated_duration_ms=0)

    def test_negative_estimated_duration_ms_raises(self):
        with pytest.raises(
            ValueError,
            match="estimated_duration_ms must be >= 0",
        ):
            ExtendedSelectableItemMetadata(estimated_duration_ms=-1)


class TestReviewArtifact:
    def test_valid_from_payload(self):
        p = load_payload("review_artifact")
        art = ReviewArtifact(
            artifact_id=p["artifact_id"],
            artifact_type=p["artifact_type"],
            source_project=p["source_project"],
            created_at=p["created_at"],
            subject_ref=p.get("subject_ref"),
            summary=p.get("summary"),
            evidence_refs=p.get("evidence_refs", []),
            decision_refs=p.get("decision_refs", []),
            metadata=p.get("metadata", {}),
        )
        assert art.artifact_id == p["artifact_id"]
        assert art.evidence_refs == p["evidence_refs"]

    def test_empty_artifact_id_raises(self):
        with pytest.raises(ValueError, match="artifact_id must be non-empty"):
            ReviewArtifact(
                artifact_id="",
                artifact_type="review_note",
                source_project="agent-kernel",
                created_at="2026-05-27T08:00:00Z",
            )

    def test_empty_artifact_type_raises(self):
        with pytest.raises(ValueError, match="artifact_type must be non-empty"):
            ReviewArtifact(
                artifact_id="rev-1",
                artifact_type="",
                source_project="agent-kernel",
                created_at="2026-05-27T08:00:00Z",
            )

    def test_empty_source_project_raises(self):
        with pytest.raises(ValueError, match="source_project must be non-empty"):
            ReviewArtifact(
                artifact_id="rev-1",
                artifact_type="review_note",
                source_project="",
                created_at="2026-05-27T08:00:00Z",
            )

    def test_empty_created_at_raises(self):
        with pytest.raises(ValueError, match="created_at must be non-empty"):
            ReviewArtifact(
                artifact_id="rev-1",
                artifact_type="review_note",
                source_project="agent-kernel",
                created_at="",
            )

    def test_defaults(self):
        art = ReviewArtifact(
            artifact_id="rev-1",
            artifact_type="review_note",
            source_project="agent-kernel",
            created_at="2026-05-27T08:00:00Z",
        )
        assert art.subject_ref is None
        assert art.evidence_refs == []
        assert art.decision_refs == []
        assert art.metadata == {}

    def test_serialization(self):
        art = ReviewArtifact(
            artifact_id="rev-1",
            artifact_type="safety_report",
            source_project="vibeguard",
            created_at="2026-05-27T08:00:00Z",
            evidence_refs=["trace:x"],
        )
        data = asdict(art)
        json.dumps(data)
        assert data["evidence_refs"] == ["trace:x"]


class TestMemoryArtifact:
    def _kwargs(self, **overrides):
        base = dict(
            memory_id="mem-1",
            memory_type="preference",
            content="prefers concise summaries",
            source="user_feedback",
            created_at="2026-05-27T08:00:00Z",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("memory_artifact")
        mem = MemoryArtifact(
            memory_id=p["memory_id"],
            memory_type=p["memory_type"],
            content=p["content"],
            source=p["source"],
            created_at=p["created_at"],
            updated_at=p.get("updated_at"),
            scope=p.get("scope"),
            sensitivity=p.get("sensitivity", "internal"),
            confidence=p.get("confidence"),
            expires_at=p.get("expires_at"),
            dependency_refs=p.get("dependency_refs", []),
            provenance=p.get("provenance", {}),
            metadata=p.get("metadata", {}),
        )
        assert mem.memory_id == p["memory_id"]
        assert mem.sensitivity == "internal"
        assert mem.confidence == p["confidence"]

    def test_empty_content_raises(self):
        with pytest.raises(ValueError, match="content must be non-empty"):
            MemoryArtifact(**self._kwargs(content=""))

    def test_empty_source_raises(self):
        with pytest.raises(ValueError, match="source must be non-empty"):
            MemoryArtifact(**self._kwargs(source=""))

    def test_invalid_sensitivity_raises(self):
        with pytest.raises(ValueError, match="sensitivity must be one of"):
            MemoryArtifact(**self._kwargs(sensitivity="secret"))

    def test_defaults(self):
        mem = MemoryArtifact(**self._kwargs())
        assert mem.sensitivity == "internal"
        assert mem.dependency_refs == []
        assert mem.provenance == {}
        assert mem.confidence is None

    def test_serialization(self):
        mem = MemoryArtifact(**self._kwargs(sensitivity="confidential"))
        data = asdict(mem)
        json.dumps(data)
        assert data["sensitivity"] == "confidential"


class TestSessionHandoff:
    def _kwargs(self, **overrides):
        base = dict(
            handoff_id="ho-1",
            from_session_id="sess-a",
            created_at="2026-05-27T12:00:00Z",
            summary="resume work on contracts",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("session_handoff")
        ho = SessionHandoff(
            handoff_id=p["handoff_id"],
            from_session_id=p["from_session_id"],
            created_at=p["created_at"],
            summary=p["summary"],
            to_session_id=p.get("to_session_id"),
            sensitivity=p.get("sensitivity", "internal"),
            open_threads=p.get("open_threads", []),
            memory_refs=p.get("memory_refs", []),
            expires_at=p.get("expires_at"),
            provenance=p.get("provenance", {}),
            metadata=p.get("metadata", {}),
        )
        assert ho.handoff_id == p["handoff_id"]
        assert ho.memory_refs == p["memory_refs"]

    def test_empty_summary_raises(self):
        with pytest.raises(ValueError, match="summary must be non-empty"):
            SessionHandoff(**self._kwargs(summary=""))

    def test_empty_from_session_id_raises(self):
        with pytest.raises(ValueError, match="from_session_id must be non-empty"):
            SessionHandoff(**self._kwargs(from_session_id=""))

    def test_invalid_sensitivity_raises(self):
        with pytest.raises(ValueError, match="sensitivity must be one of"):
            SessionHandoff(**self._kwargs(sensitivity="topsecret"))

    def test_defaults(self):
        ho = SessionHandoff(**self._kwargs())
        assert ho.to_session_id is None
        assert ho.open_threads == []
        assert ho.memory_refs == []

    def test_serialization(self):
        ho = SessionHandoff(**self._kwargs(open_threads=["t1"]))
        data = asdict(ho)
        json.dumps(data)
        assert data["open_threads"] == ["t1"]


class TestLessonCard:
    def _kwargs(self, **overrides):
        base = dict(
            lesson_id="lsn-1",
            title="Always regenerate the index",
            body="Run the index generator after schema changes.",
            created_at="2026-05-27T09:00:00Z",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("lesson_card")
        card = LessonCard(
            lesson_id=p["lesson_id"],
            title=p["title"],
            body=p["body"],
            created_at=p["created_at"],
            lifecycle_state=p.get("lifecycle_state", "draft"),
            scope=p.get("scope"),
            sensitivity=p.get("sensitivity", "internal"),
            applicability=p.get("applicability", []),
            source_refs=p.get("source_refs", []),
            expires_at=p.get("expires_at"),
            provenance=p.get("provenance", {}),
            metadata=p.get("metadata", {}),
        )
        assert card.lesson_id == p["lesson_id"]
        assert card.lifecycle_state == "active"

    def test_empty_body_raises(self):
        with pytest.raises(ValueError, match="body must be non-empty"):
            LessonCard(**self._kwargs(body=""))

    def test_invalid_lifecycle_state_raises(self):
        with pytest.raises(ValueError, match="lifecycle_state must be one of"):
            LessonCard(**self._kwargs(lifecycle_state="published"))

    def test_invalid_sensitivity_raises(self):
        with pytest.raises(ValueError, match="sensitivity must be one of"):
            LessonCard(**self._kwargs(sensitivity="secret"))

    def test_defaults(self):
        card = LessonCard(**self._kwargs())
        assert card.lifecycle_state == "draft"
        assert card.applicability == []
        assert card.sensitivity == "internal"

    def test_serialization(self):
        card = LessonCard(**self._kwargs(lifecycle_state="in_review"))
        data = asdict(card)
        json.dumps(data)
        assert data["lifecycle_state"] == "in_review"


class TestSkillCard:
    def _kwargs(self, **overrides):
        base = dict(
            skill_id="skl-1",
            name="Add a contract",
            description="How to add an Extended contract.",
            created_at="2026-05-27T09:30:00Z",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("skill_card")
        card = SkillCard(
            skill_id=p["skill_id"],
            name=p["name"],
            description=p["description"],
            created_at=p["created_at"],
            lifecycle_state=p.get("lifecycle_state", "draft"),
            steps=p.get("steps", []),
            preconditions=p.get("preconditions", []),
            scope=p.get("scope"),
            sensitivity=p.get("sensitivity", "internal"),
            source_refs=p.get("source_refs", []),
            expires_at=p.get("expires_at"),
            provenance=p.get("provenance", {}),
            metadata=p.get("metadata", {}),
        )
        assert card.skill_id == p["skill_id"]
        assert len(card.steps) == len(p["steps"])

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name must be non-empty"):
            SkillCard(**self._kwargs(name=""))

    def test_invalid_lifecycle_state_raises(self):
        with pytest.raises(ValueError, match="lifecycle_state must be one of"):
            SkillCard(**self._kwargs(lifecycle_state="live"))

    def test_defaults(self):
        card = SkillCard(**self._kwargs())
        assert card.lifecycle_state == "draft"
        assert card.steps == []
        assert card.preconditions == []

    def test_serialization(self):
        card = SkillCard(**self._kwargs(steps=["s1", "s2"]))
        data = asdict(card)
        json.dumps(data)
        assert data["steps"] == ["s1", "s2"]


class TestEvaluationArtifact:
    def _kwargs(self, **overrides):
        base = dict(
            artifact_id="eval-1",
            producer="skdr-eval",
            created_at="2026-05-27T10:00:00Z",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("evaluation_artifact")
        art = EvaluationArtifact(
            artifact_id=p["artifact_id"],
            producer=p["producer"],
            created_at=p["created_at"],
            artifact_type=p.get("artifact_type", "offline_policy_evaluation"),
            producer_version=p.get("producer_version"),
            target_estimand=p.get("target_estimand"),
            candidate_policy=p.get("candidate_policy"),
            baseline_policy=p.get("baseline_policy"),
            metrics=p.get("metrics", {}),
            uncertainty=p.get("uncertainty", {}),
            support_state=p.get("support_state", "ok"),
            support_diagnostics=p.get("support_diagnostics", {}),
            propensity_diagnostics=p.get("propensity_diagnostics", {}),
            sensitivity=p.get("sensitivity", "internal"),
            warnings=p.get("warnings", []),
            recommendation=p.get("recommendation"),
            recommendation_kind=p.get("recommendation_kind"),
            limitations=p.get("limitations", []),
            provenance=p.get("provenance", {}),
            metadata=p.get("metadata", {}),
        )
        assert art.support_state == "caution"
        assert art.recommendation_kind == "experiment_ready"

    def test_invalid_support_state_raises(self):
        with pytest.raises(ValueError, match="support_state must be one of"):
            EvaluationArtifact(**self._kwargs(support_state="unknown"))

    def test_invalid_recommendation_kind_raises(self):
        with pytest.raises(ValueError, match="recommendation_kind must be one of"):
            EvaluationArtifact(**self._kwargs(recommendation_kind="ship_it"))

    def test_invalid_sensitivity_raises(self):
        with pytest.raises(ValueError, match="sensitivity must be one of"):
            EvaluationArtifact(**self._kwargs(sensitivity="secret"))

    def test_high_risk_cannot_recommend_deploy(self):
        """#67: a high-risk evaluation must not recommend deployment."""
        with pytest.raises(ValueError, match="not deployment evidence"):
            EvaluationArtifact(
                **self._kwargs(
                    support_state="high_risk",
                    recommendation_kind="deploy",
                )
            )

    def test_high_risk_allows_non_deploy_recommendation(self):
        art = EvaluationArtifact(
            **self._kwargs(
                support_state="high_risk",
                recommendation_kind="do_not_deploy",
            )
        )
        assert art.recommendation_kind == "do_not_deploy"

    def test_defaults(self):
        art = EvaluationArtifact(**self._kwargs())
        assert art.artifact_type == "offline_policy_evaluation"
        assert art.support_state == "ok"
        assert art.recommendation_kind is None
        assert art.warnings == []

    def test_serialization(self):
        art = EvaluationArtifact(**self._kwargs(warnings=["limited overlap"]))
        data = asdict(art)
        json.dumps(data)
        assert data["warnings"] == ["limited overlap"]


class TestArtifactSafetyGateRequest:
    def _kwargs(self, **overrides):
        base = dict(
            request_id="req-1",
            repository_root="/workspace/app",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("artifact_safety_gate_request")
        req = ArtifactSafetyGateRequest(
            request_id=p["request_id"],
            repository_root=p["repository_root"],
            artifact_paths=p.get("artifact_paths", []),
            diff_scope=p.get("diff_scope"),
            policy_level=p.get("policy_level", "standard"),
            output_format=p.get("output_format", "json"),
            capability_id=p.get("capability_id"),
            metadata=p.get("metadata", {}),
        )
        assert req.request_id == p["request_id"]
        assert req.policy_level == "strict"

    def test_empty_request_id_raises(self):
        with pytest.raises(ValueError, match="request_id must be non-empty"):
            ArtifactSafetyGateRequest(**self._kwargs(request_id=""))

    def test_empty_repository_root_raises(self):
        with pytest.raises(ValueError, match="repository_root must be non-empty"):
            ArtifactSafetyGateRequest(**self._kwargs(repository_root=""))

    def test_defaults(self):
        req = ArtifactSafetyGateRequest(**self._kwargs())
        assert req.policy_level == "standard"
        assert req.output_format == "json"
        assert req.artifact_paths == []

    def test_serialization(self):
        req = ArtifactSafetyGateRequest(**self._kwargs(artifact_paths=["a.py"]))
        data = asdict(req)
        json.dumps(data)
        assert data["artifact_paths"] == ["a.py"]


class TestArtifactSafetyReport:
    def _kwargs(self, **overrides):
        base = dict(
            report_id="rep-1",
            gate_id="org.vibeguard.scan",
            decision="pass",
            created_at="2026-05-27T10:30:00Z",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("artifact_safety_report")
        rep = ArtifactSafetyReport(
            report_id=p["report_id"],
            gate_id=p["gate_id"],
            decision=p["decision"],
            created_at=p["created_at"],
            mode=p.get("mode", "advisory"),
            request_id=p.get("request_id"),
            target_ref=p.get("target_ref"),
            summary=p.get("summary"),
            findings=p.get("findings", []),
            provenance=p.get("provenance", {}),
            metadata=p.get("metadata", {}),
        )
        assert rep.decision == "fail"
        assert rep.mode == "blocking"
        assert rep.findings[0]["severity"] == "high"

    def test_invalid_decision_raises(self):
        with pytest.raises(ValueError, match="decision must be one of"):
            ArtifactSafetyReport(**self._kwargs(decision="maybe"))

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="mode must be one of"):
            ArtifactSafetyReport(**self._kwargs(mode="warn"))

    def test_empty_gate_id_raises(self):
        with pytest.raises(ValueError, match="gate_id must be non-empty"):
            ArtifactSafetyReport(**self._kwargs(gate_id=""))

    def test_defaults(self):
        rep = ArtifactSafetyReport(**self._kwargs())
        assert rep.mode == "advisory"
        assert rep.findings == []
        assert rep.request_id is None

    def test_serialization(self):
        rep = ArtifactSafetyReport(
            **self._kwargs(findings=[{"finding_id": "f1", "severity": "low", "message": "m"}])
        )
        data = asdict(rep)
        json.dumps(data)
        assert data["findings"][0]["finding_id"] == "f1"


class TestCapabilityTokenSignature:
    # 86-char base64url placeholder (64 raw bytes encoded RFC 4648 §5 no padding).
    # Illustrative only — never produced by a real keyring.
    _ILLUSTRATIVE_SIG = (
        "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0-Pw"
    )

    def _kwargs(self, **overrides):
        base = dict(
            alg="ed25519",
            kid="agent-kernel-2026-05-key-01",
            sig=self._ILLUSTRATIVE_SIG,
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("capability_token_signature")
        sig = CapabilityTokenSignature(
            alg=p["alg"],
            kid=p["kid"],
            sig=p["sig"],
            canonicalization=p.get("canonicalization", "JCS"),
            signed_at=p.get("signed_at"),
        )
        assert sig.alg == "ed25519"
        assert sig.canonicalization == "JCS"

    def test_unknown_alg_raises(self):
        with pytest.raises(ValueError, match="alg must be one of"):
            CapabilityTokenSignature(**self._kwargs(alg="rsa-pkcs1"))

    def test_empty_kid_raises(self):
        with pytest.raises(ValueError, match="kid must be non-empty"):
            CapabilityTokenSignature(**self._kwargs(kid=""))

    def test_empty_sig_raises(self):
        with pytest.raises(ValueError, match="sig must be non-empty"):
            CapabilityTokenSignature(**self._kwargs(sig=""))

    def test_short_sig_raises(self):
        with pytest.raises(ValueError, match="sig must be 86 base64url"):
            CapabilityTokenSignature(**self._kwargs(sig="A" * 85))

    def test_long_sig_raises(self):
        with pytest.raises(ValueError, match="sig must be 86 base64url"):
            CapabilityTokenSignature(**self._kwargs(sig="A" * 87))

    def test_non_base64url_sig_raises(self):
        # '+' and '/' belong to standard base64 — base64url forbids them.
        bad = "A" * 84 + "+/"
        with pytest.raises(ValueError, match="sig must be 86 base64url"):
            CapabilityTokenSignature(**self._kwargs(sig=bad))

    def test_unknown_canonicalization_raises(self):
        with pytest.raises(ValueError, match="canonicalization must be one of"):
            CapabilityTokenSignature(
                **self._kwargs(canonicalization="sorted-keys")
            )

    def test_defaults(self):
        sig = CapabilityTokenSignature(**self._kwargs())
        assert sig.canonicalization == "JCS"
        assert sig.signed_at is None

    def test_es256_accepted(self):
        sig = CapabilityTokenSignature(**self._kwargs(alg="es256"))
        assert sig.alg == "es256"

    def test_serialization(self):
        sig = CapabilityTokenSignature(
            **self._kwargs(signed_at="2026-05-28T08:00:00Z")
        )
        data = asdict(sig)
        json.dumps(data)
        assert data["signed_at"] == "2026-05-28T08:00:00Z"


class TestOtelTraceMapping:
    def _kwargs(self, **overrides):
        base = dict(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            span_kind="INTERNAL",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("otel_trace_mapping")
        m = OtelTraceMapping(
            trace_id=p["trace_id"],
            span_id=p["span_id"],
            span_kind=p["span_kind"],
            gen_ai_operation_name=p.get("gen_ai_operation_name"),
            gen_ai_agent_id=p.get("gen_ai_agent_id"),
            gen_ai_agent_name=p.get("gen_ai_agent_name"),
            gen_ai_tool_name=p.get("gen_ai_tool_name"),
            gen_ai_system=p.get("gen_ai_system"),
            parent_span_id=p.get("parent_span_id"),
            semconv_version=p.get("semconv_version"),
        )
        assert m.span_kind == "INTERNAL"
        assert m.gen_ai_operation_name == "execute_tool"
        assert m.gen_ai_tool_name == "org.myapp.search_docs"

    def test_short_trace_id_raises(self):
        with pytest.raises(ValueError, match="trace_id must be 32 lowercase hex"):
            OtelTraceMapping(**self._kwargs(trace_id="deadbeef"))

    def test_short_span_id_raises(self):
        with pytest.raises(ValueError, match="span_id must be 16 lowercase hex"):
            OtelTraceMapping(**self._kwargs(span_id="dead"))

    def test_non_hex_trace_id_raises(self):
        with pytest.raises(ValueError, match="trace_id must be 32 lowercase hex"):
            OtelTraceMapping(
                **self._kwargs(trace_id="z" * 32)  # 32 chars, not hex
            )

    def test_uppercase_trace_id_raises(self):
        # W3C Trace Context requires lowercase hex; uppercase is non-conformant
        # even though the chars are hex-valid.
        with pytest.raises(ValueError, match="trace_id must be 32 lowercase hex"):
            OtelTraceMapping(
                **self._kwargs(trace_id="4BF92F3577B34DA6A3CE929D0E0E4736")
            )

    def test_uppercase_span_id_raises(self):
        with pytest.raises(ValueError, match="span_id must be 16 lowercase hex"):
            OtelTraceMapping(**self._kwargs(span_id="00F067AA0BA902B7"))

    def test_uppercase_parent_span_id_raises(self):
        with pytest.raises(ValueError, match="parent_span_id must be 16 lowercase hex"):
            OtelTraceMapping(
                **self._kwargs(parent_span_id="B9C7C989F97918E1")
            )

    def test_invalid_span_kind_raises(self):
        with pytest.raises(ValueError, match="span_kind must be one of"):
            OtelTraceMapping(**self._kwargs(span_kind="DOWNSTREAM"))

    def test_invalid_parent_span_id_raises(self):
        with pytest.raises(ValueError, match="parent_span_id must be 16 lowercase hex"):
            OtelTraceMapping(**self._kwargs(parent_span_id="z" * 16))

    def test_defaults_omit_optional(self):
        m = OtelTraceMapping(**self._kwargs())
        assert m.gen_ai_operation_name is None
        assert m.parent_span_id is None
        assert m.semconv_version is None

    def test_all_span_kinds_accepted(self):
        for kind in ("INTERNAL", "CLIENT", "SERVER", "PRODUCER", "CONSUMER"):
            m = OtelTraceMapping(**self._kwargs(span_kind=kind))
            assert m.span_kind == kind

    def test_serialization(self):
        m = OtelTraceMapping(**self._kwargs(gen_ai_system="weaver"))
        data = asdict(m)
        json.dumps(data)
        assert data["gen_ai_system"] == "weaver"


# ---------------------------------------------------------------------------
# Selection ↔ execution boundary contracts (#61, #66)
# ---------------------------------------------------------------------------


class TestCompiledFlow:
    def test_valid_from_payload(self):
        p = load_payload("compiled_flow")
        flow = CompiledFlow(
            flow_id=p["flow_id"],
            name=p.get("name"),
            version=p.get("version"),
            description=p.get("description"),
            input_schema_ref=p.get("input_schema_ref"),
            output_schema_ref=p.get("output_schema_ref"),
            tool_dependencies=p.get("tool_dependencies", []),
            sensitivity=p.get("sensitivity"),
            side_effects=p.get("side_effects", []),
            requires_authorization=p.get("requires_authorization", True),
            metadata=p.get("metadata", {}),
        )
        assert flow.flow_id == "invoice_reminder_flow"
        assert flow.requires_authorization is True
        assert "org.email.send_reminder" in flow.tool_dependencies

    def test_defaults(self):
        flow = CompiledFlow(flow_id="f1")
        assert flow.requires_authorization is True
        assert flow.tool_dependencies == []
        assert flow.sensitivity is None

    def test_empty_flow_id_raises(self):
        with pytest.raises(ValueError, match="flow_id must be non-empty"):
            CompiledFlow(flow_id="")

    def test_invalid_sensitivity_raises(self):
        with pytest.raises(ValueError, match="sensitivity must be one of"):
            CompiledFlow(flow_id="f1", sensitivity="top-secret")

    def test_serialization(self):
        flow = CompiledFlow(flow_id="f1", side_effects=["data_write"])
        data = asdict(flow)
        json.dumps(data)
        assert data["side_effects"] == ["data_write"]


class TestExecutionCandidate:
    def test_valid_from_payload(self):
        p = load_payload("execution_candidate")
        cf = p.get("compiled_flow")
        candidate = ExecutionCandidate(
            candidate_id=p["candidate_id"],
            candidate_type=p["candidate_type"],
            name=p.get("name"),
            version=p.get("version"),
            description=p.get("description"),
            compiled_flow=CompiledFlow(
                flow_id=cf["flow_id"],
                name=cf.get("name"),
                version=cf.get("version"),
                description=cf.get("description"),
                tool_dependencies=cf.get("tool_dependencies", []),
                sensitivity=cf.get("sensitivity"),
                side_effects=cf.get("side_effects", []),
                requires_authorization=cf.get("requires_authorization", True),
            )
            if cf is not None
            else None,
            metadata=p.get("metadata", {}),
        )
        assert candidate.candidate_type == "flow"
        assert candidate.compiled_flow is not None
        assert candidate.compiled_flow.flow_id == "invoice_reminder_flow"

    def test_minimal_non_flow_candidate(self):
        candidate = ExecutionCandidate(
            candidate_id="send_invoice_reminder", candidate_type="tool"
        )
        assert candidate.compiled_flow is None

    def test_empty_candidate_id_raises(self):
        with pytest.raises(ValueError, match="candidate_id must be non-empty"):
            ExecutionCandidate(candidate_id="", candidate_type="tool")

    def test_invalid_candidate_type_raises(self):
        with pytest.raises(ValueError, match="candidate_type must be one of"):
            ExecutionCandidate(candidate_id="c1", candidate_type="macro")

    def test_compiled_flow_on_non_flow_candidate_raises(self):
        with pytest.raises(ValueError, match="compiled_flow is only valid"):
            ExecutionCandidate(
                candidate_id="c1",
                candidate_type="tool",
                compiled_flow=CompiledFlow(flow_id="f1"),
            )


class TestExecutionRoutingDecision:
    def _candidate(self) -> ExecutionCandidate:
        return ExecutionCandidate(candidate_id="c1", candidate_type="flow")

    def test_valid_from_payload(self):
        p = load_payload("execution_routing_decision")
        c = p["candidate"]
        decision = ExecutionRoutingDecision(
            decision_id=p["decision_id"],
            candidate=ExecutionCandidate(
                candidate_id=c["candidate_id"],
                candidate_type=c["candidate_type"],
                name=c.get("name"),
                version=c.get("version"),
            ),
            confidence=p.get("confidence"),
            reason_codes=p.get("reason_codes", []),
            reason=p.get("reason"),
            fallback_candidates=[
                ExecutionCandidate(
                    candidate_id=fc["candidate_id"],
                    candidate_type=fc["candidate_type"],
                    name=fc.get("name"),
                )
                for fc in p.get("fallback_candidates", [])
            ],
            constraints=p.get("constraints", {}),
            policy_context_ref=p.get("policy_context_ref"),
            trace_ref=p.get("trace_ref"),
            created_at=p.get("created_at"),
            metadata=p.get("metadata", {}),
        )
        assert decision.decision_id == "dec_123"
        assert decision.candidate.candidate_id == "invoice_reminder_flow"
        assert decision.confidence == 0.86
        assert len(decision.fallback_candidates) == 1

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValueError, match="decision_id must be non-empty"):
            ExecutionRoutingDecision(decision_id="", candidate=self._candidate())

    def test_confidence_above_range_raises(self):
        with pytest.raises(ValueError, match="confidence must be in"):
            ExecutionRoutingDecision(
                decision_id="d1", candidate=self._candidate(), confidence=1.5
            )

    def test_confidence_below_range_raises(self):
        with pytest.raises(ValueError, match="confidence must be in"):
            ExecutionRoutingDecision(
                decision_id="d1", candidate=self._candidate(), confidence=-0.1
            )


class TestExecutionFeedback:
    def _kwargs(self, **overrides):
        base = dict(
            decision_id="dec_123",
            candidate_id="invoice_reminder_flow",
            success=True,
            timestamp="2026-05-25T08:00:00Z",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("execution_feedback")
        fb = ExecutionFeedback(
            decision_id=p["decision_id"],
            candidate_id=p["candidate_id"],
            success=p["success"],
            timestamp=p["timestamp"],
            latency_ms=p.get("latency_ms"),
            cost=p.get("cost", {}),
            quality_score=p.get("quality_score"),
            error_type=p.get("error_type"),
            error_message=p.get("error_message"),
            trace_ref=p.get("trace_ref"),
            execution_summary=p.get("execution_summary", {}),
            metadata=p.get("metadata", {}),
        )
        assert fb.success is True
        assert fb.latency_ms == 842
        assert fb.trace_ref == "chainweaver:trace_id:abc123"

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValueError, match="decision_id must be non-empty"):
            ExecutionFeedback(**self._kwargs(decision_id=""))

    def test_empty_candidate_id_raises(self):
        with pytest.raises(ValueError, match="candidate_id must be non-empty"):
            ExecutionFeedback(**self._kwargs(candidate_id=""))

    def test_empty_timestamp_raises(self):
        with pytest.raises(ValueError, match="timestamp must be non-empty"):
            ExecutionFeedback(**self._kwargs(timestamp=""))

    def test_negative_latency_raises(self):
        with pytest.raises(ValueError, match="latency_ms must be >= 0"):
            ExecutionFeedback(**self._kwargs(latency_ms=-1))

    def test_quality_score_out_of_range_raises(self):
        with pytest.raises(ValueError, match="quality_score must be in"):
            ExecutionFeedback(**self._kwargs(quality_score=1.1))

    def test_serialization(self):
        fb = ExecutionFeedback(**self._kwargs(success=False, error_type="timeout"))
        data = asdict(fb)
        json.dumps(data)
        assert data["error_type"] == "timeout"


# ---------------------------------------------------------------------------
# Audit-chain and replayable-failure artifacts (#50, #72)
# ---------------------------------------------------------------------------


def _routing_decision_from(d: dict) -> RoutingDecision:
    cards = [
        ChoiceCard(
            id=c["id"],
            items=[
                SelectableItem(
                    id=it["id"],
                    label=it["label"],
                    description=it["description"],
                    capability_id=it.get("capability_id"),
                )
                for it in c["items"]
            ],
            context_hint=c.get("context_hint"),
        )
        for c in d["choice_cards"]
    ]
    return RoutingDecision(
        id=d["id"],
        choice_cards=cards,
        timestamp=parse_dt(d["timestamp"]),
        selected_item_id=d.get("selected_item_id"),
        selected_card_id=d.get("selected_card_id"),
        context_summary=d.get("context_summary"),
    )


def _policy_decision_from(d: dict) -> PolicyDecision:
    return PolicyDecision(
        decision_id=d["decision_id"],
        decision=d["decision"],
        capability_id=d["capability_id"],
        principal=d["principal"],
        timestamp=parse_dt(d["timestamp"]),
        token_id=d.get("token_id"),
        reason=d.get("reason"),
        metadata=d.get("metadata", {}),
    )


def _frame_from(d: dict) -> Frame:
    return Frame(
        frame_id=d["frame_id"],
        capability_id=d["capability_id"],
        summary=d["summary"],
        created_at=parse_dt(d["created_at"]),
        handle_refs=d.get("handle_refs", []),
        redaction_notes=d.get("redaction_notes"),
    )


def _handle_from(d: dict) -> Handle:
    return Handle(
        handle_id=d["handle_id"],
        capability_id=d["capability_id"],
        artifact_type=d["artifact_type"],
        created_at=parse_dt(d["created_at"]),
        expires_at=parse_dt(d["expires_at"]) if d.get("expires_at") else None,
        access_policy=d.get("access_policy"),
        byte_size=d.get("byte_size"),
        metadata=d.get("metadata", {}),
    )


def _trace_event_from(d: dict) -> TraceEvent:
    return TraceEvent(
        event_id=d["event_id"],
        event_type=d["event_type"],
        timestamp=parse_dt(d["timestamp"]),
        capability_id=d.get("capability_id"),
        principal=d.get("principal"),
        decision_id=d.get("decision_id"),
        frame_id=d.get("frame_id"),
        handle_id=d.get("handle_id"),
        outcome=d.get("outcome"),
        error_message=d.get("error_message"),
        metadata=d.get("metadata", {}),
    )


def _trace_bundle_from(p: dict) -> TraceBundle:
    sig = p.get("signature")
    return TraceBundle(
        bundle_id=p["bundle_id"],
        routing_decision=_routing_decision_from(p["routing_decision"]),
        policy_decisions=[_policy_decision_from(d) for d in p["policy_decisions"]],
        frames=[_frame_from(d) for d in p["frames"]],
        handles=[_handle_from(d) for d in p["handles"]],
        trace_events=[_trace_event_from(d) for d in p["trace_events"]],
        canonicalization=p.get("canonicalization", "JCS"),
        signature=(
            CapabilityTokenSignature(
                alg=sig["alg"],
                kid=sig["kid"],
                sig=sig["sig"],
                canonicalization=sig.get("canonicalization", "JCS"),
                signed_at=sig.get("signed_at"),
            )
            if sig is not None
            else None
        ),
        created_at=p.get("created_at"),
        metadata=p.get("metadata", {}),
    )


class TestTraceBundle:
    # Core artifacts carry datetimes, so (like the Core roundtrip tests) this
    # constructs from the payload and asserts; it does not asdict/json.dumps.
    def test_unsigned_from_payload(self):
        p = load_payload("trace_bundle")
        bundle = _trace_bundle_from(p)
        assert bundle.bundle_id == "tb-20260308-001"
        assert bundle.routing_decision.id == "rd-20260308-001"
        assert len(bundle.policy_decisions) == 1
        assert bundle.policy_decisions[0].decision == "allow"
        assert bundle.frames[0].frame_id == "frame-20260308-001"
        assert bundle.handles[0].handle_id == "handle-rawresult-20260308-001"
        assert bundle.trace_events[0].outcome == "success"
        assert bundle.canonicalization == "JCS"
        assert bundle.signature is None

    def test_signed_from_payload(self):
        p = load_payload("trace_bundle_signed")
        bundle = _trace_bundle_from(p)
        assert bundle.signature is not None
        assert bundle.signature.alg == "ed25519"
        assert bundle.signature.canonicalization == "JCS"

    def test_invariant_frames_have_no_raw_output(self):
        # I-01: Frames in a bundle expose no raw_output attribute.
        p = load_payload("trace_bundle")
        bundle = _trace_bundle_from(p)
        assert all(not hasattr(f, "raw_output") for f in bundle.frames)

    def test_invariant_policy_decisions_have_matching_trace_event(self):
        # I-02: every PolicyDecision in the bundle has a matching TraceEvent,
        # linked by decision_id (policy_decisions[*].decision_id is referenced
        # by some trace_events[*].decision_id). Interim artifact-level lock-in
        # until the conformance runner enforces this across arbitrary bundles
        # (#74).
        p = load_payload("trace_bundle")
        bundle = _trace_bundle_from(p)
        traced_decision_ids = {
            te.decision_id for te in bundle.trace_events if te.decision_id is not None
        }
        assert bundle.policy_decisions, "sample bundle should exercise I-02"
        for pd in bundle.policy_decisions:
            assert pd.decision_id in traced_decision_ids

    def _minimal_kwargs(self, **overrides):
        base = dict(
            bundle_id="tb-1",
            routing_decision=_routing_decision_from(
                load_payload("trace_bundle")["routing_decision"]
            ),
            policy_decisions=[],
            frames=[],
            handles=[],
            trace_events=[],
        )
        base.update(overrides)
        return base

    def test_empty_bundle_id_raises(self):
        with pytest.raises(ValueError, match="bundle_id must be non-empty"):
            TraceBundle(**self._minimal_kwargs(bundle_id=""))

    def test_invalid_canonicalization_raises(self):
        with pytest.raises(ValueError, match="canonicalization must be one of"):
            TraceBundle(**self._minimal_kwargs(canonicalization="sorted-keys"))

    def test_defaults(self):
        bundle = TraceBundle(**self._minimal_kwargs())
        assert bundle.canonicalization == "JCS"
        assert bundle.signature is None
        assert bundle.created_at is None
        assert bundle.metadata == {}


class TestFailureCaseArtifact:
    def _kwargs(self, **overrides):
        base = dict(
            failure_case_id="fc-1",
            created_at="2026-05-28T14:12:00Z",
            source_project="ChainWeaver",
            property_name="flow_is_idempotent",
            status="candidate",
        )
        base.update(overrides)
        return base

    def test_valid_from_payload(self):
        p = load_payload("failure_case_artifact")
        fc = FailureCaseArtifact(
            failure_case_id=p["failure_case_id"],
            created_at=p["created_at"],
            source_project=p["source_project"],
            property_name=p["property_name"],
            status=p["status"],
            property_description=p.get("property_description"),
            severity=p.get("severity"),
            seed=p.get("seed"),
            generator_config=p.get("generator_config", {}),
            trace_ref=p.get("trace_ref"),
            minimized=p.get("minimized", False),
            minimized_from_ref=p.get("minimized_from_ref"),
            expected_failure_mode=p.get("expected_failure_mode"),
            evidence_refs=p.get("evidence_refs", []),
            sensitivity=p.get("sensitivity", "internal"),
            provenance=p.get("provenance", {}),
            metadata=p.get("metadata", {}),
        )
        assert fc.failure_case_id == "fc-20260528-001"
        assert fc.status == "candidate"
        assert fc.severity == "high"
        assert fc.minimized is True
        assert fc.trace_ref == "chainweaver:trace_id:abc123"

    def test_empty_failure_case_id_raises(self):
        with pytest.raises(ValueError, match="failure_case_id must be non-empty"):
            FailureCaseArtifact(**self._kwargs(failure_case_id=""))

    def test_empty_property_name_raises(self):
        with pytest.raises(ValueError, match="property_name must be non-empty"):
            FailureCaseArtifact(**self._kwargs(property_name=""))

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="status must be one of"):
            FailureCaseArtifact(**self._kwargs(status="open"))

    def test_invalid_severity_raises(self):
        with pytest.raises(ValueError, match="severity must be one of"):
            FailureCaseArtifact(**self._kwargs(severity="extreme"))

    def test_invalid_sensitivity_raises(self):
        with pytest.raises(ValueError, match="sensitivity must be one of"):
            FailureCaseArtifact(**self._kwargs(sensitivity="secret"))

    def test_all_statuses_accepted(self):
        for status in ("candidate", "regression", "ignored", "fixed"):
            fc = FailureCaseArtifact(**self._kwargs(status=status))
            assert fc.status == status

    def test_defaults(self):
        fc = FailureCaseArtifact(**self._kwargs())
        assert fc.severity is None
        assert fc.minimized is False
        assert fc.evidence_refs == []
        assert fc.sensitivity == "internal"
        assert fc.generator_config == {}

    def test_serialization(self):
        fc = FailureCaseArtifact(
            **self._kwargs(status="regression", evidence_refs=["trace:x"])
        )
        data = asdict(fc)
        json.dumps(data)
        assert data["evidence_refs"] == ["trace:x"]
