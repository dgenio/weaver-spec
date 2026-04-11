"""Tests for Extended contract dataclasses and sample payload construction."""

import json
import pathlib
from dataclasses import asdict
from typing import Optional

import pytest

from weaver_contracts.extended import (
    ExtendedFrameMetadata,
    ExtendedSelectableItemMetadata,
    RedactionPolicy,
    RiskAssessment,
    SchemaFingerprint,
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
