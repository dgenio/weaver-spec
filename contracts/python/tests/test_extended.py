"""Tests for Extended contract dataclasses and sample payload construction."""

import json
import pathlib
from dataclasses import asdict
from typing import Optional

import pytest

from weaver_contracts.extended import (
    ArtifactSafetyGateRequest,
    ArtifactSafetyReport,
    EvaluationArtifact,
    ExtendedFrameMetadata,
    ExtendedSelectableItemMetadata,
    LessonCard,
    MemoryArtifact,
    RedactionPolicy,
    ReviewArtifact,
    RiskAssessment,
    SchemaFingerprint,
    SessionHandoff,
    SkillCard,
    TelemetryHint,
    UIHint,
)

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
