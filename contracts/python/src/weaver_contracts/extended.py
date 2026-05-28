"""
Extended Weaver contracts.

These types provide optional metadata for richer integrations. They extend Core
contracts with telemetry, schema fingerprints, redaction policies, UI hints,
and risk metadata. No type in this module is required for spec compliance.

Extended contracts may evolve faster than Core; they follow the same semver rules
but breaking changes are permitted in MINOR versions (see VERSIONING.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# TelemetryHint — attached to any contract for observability enrichment
# ---------------------------------------------------------------------------

@dataclass
class TelemetryHint:
    """Optional telemetry metadata that can be attached to any event or contract."""

    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# SchemaFingerprint — for schema evolution and compatibility checking
# ---------------------------------------------------------------------------

@dataclass
class SchemaFingerprint:
    """Records the schema version and content hash for a contract payload."""

    schema_id: str
    schema_version: str
    content_hash: Optional[str] = None
    hash_algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if not self.schema_id:
            raise ValueError("SchemaFingerprint.schema_id must be non-empty")
        if not self.schema_version:
            raise ValueError("SchemaFingerprint.schema_version must be non-empty")


# ---------------------------------------------------------------------------
# RedactionPolicy — governs how raw output is processed by the firewall
# ---------------------------------------------------------------------------

@dataclass
class RedactionPolicy:
    """Describes the redaction rules applied by the firewall when producing a Frame."""

    policy_id: str
    redacted_fields: List[str] = field(default_factory=list)
    truncated_fields: List[str] = field(default_factory=list)
    redaction_reason: Optional[str] = None
    pii_detected: bool = False
    pii_types: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.policy_id:
            raise ValueError("RedactionPolicy.policy_id must be non-empty")


# ---------------------------------------------------------------------------
# UIHint — display guidance for UI layers that render ChoiceCards
# ---------------------------------------------------------------------------

@dataclass
class UIHint:
    """Optional rendering hints for UI layers that display ChoiceCards."""

    icon: Optional[str] = None
    color: Optional[str] = None
    priority: Optional[int] = None
    group: Optional[str] = None
    disabled: bool = False
    tooltip: Optional[str] = None


# ---------------------------------------------------------------------------
# RiskAssessment — optional risk metadata for capability execution
# ---------------------------------------------------------------------------

@dataclass
class RiskAssessment:
    """Optional risk metadata for a capability invocation."""

    risk_level: str = "low"  # "low" | "medium" | "high" | "critical"
    risk_reasons: List[str] = field(default_factory=list)
    requires_human_approval: bool = False
    approval_principal: Optional[str] = None
    mitigations: List[str] = field(default_factory=list)

    _VALID_LEVELS = frozenset({"low", "medium", "high", "critical"})

    def __post_init__(self) -> None:
        if self.risk_level not in self._VALID_LEVELS:
            raise ValueError(
                f"RiskAssessment.risk_level must be one of {self._VALID_LEVELS}"
            )


# ---------------------------------------------------------------------------
# ExtendedFrameMetadata — enriched Frame metadata
# ---------------------------------------------------------------------------

@dataclass
class ExtendedFrameMetadata:
    """Optional extended metadata for a Frame, beyond the Core contract."""

    redaction_policy: Optional[RedactionPolicy] = None
    telemetry: Optional[TelemetryHint] = None
    schema_fingerprint: Optional[SchemaFingerprint] = None
    confidence_score: Optional[float] = None
    source_capability_version: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.confidence_score is not None and not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(
                "ExtendedFrameMetadata.confidence_score must be in [0.0, 1.0]"
            )


# ---------------------------------------------------------------------------
# ExtendedSelectableItemMetadata — UI and risk hints for a SelectableItem
# ---------------------------------------------------------------------------

@dataclass
class ExtendedSelectableItemMetadata:
    """Optional extended metadata for a SelectableItem."""

    ui_hint: Optional[UIHint] = None
    risk_assessment: Optional[RiskAssessment] = None
    estimated_duration_ms: Optional[int] = None
    requires_confirmation: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.estimated_duration_ms is not None and self.estimated_duration_ms < 0:
            raise ValueError(
                "ExtendedSelectableItemMetadata.estimated_duration_ms must be >= 0"
            )


# ===========================================================================
# Cross-project artifact contracts
#
# The types below are standalone, language-neutral artifacts exchanged between
# Weaver-stack repos and adjacent tools (lessonweaver, skdr-eval, vibeguard).
# They are Extended (optional, not required for spec compliance per I-04) and
# share a common envelope: a non-empty string id, an ISO-8601 `created_at`
# string, an optional `sensitivity` level, optional `provenance`, and a
# `metadata` extension bag. See docs/ARTIFACT_CONTRACTS.md for the taxonomy
# that distinguishes these from one another and from Core contracts.
# ===========================================================================

# Shared sensitivity vocabulary for artifact contracts.
_SENSITIVITY_LEVELS = frozenset(
    {"public", "internal", "confidential", "restricted"}
)

# Shared lifecycle states for reusable, review-gated artifacts (lessons, skills).
_LIFECYCLE_STATES = frozenset({"draft", "in_review", "active", "deprecated"})


# ---------------------------------------------------------------------------
# ReviewArtifact — minimal cross-project trace/review interchange shape
# ---------------------------------------------------------------------------

@dataclass
class ReviewArtifact:
    """A minimal, language-neutral interchange shape for trace/review artifacts.

    Sibling projects produce or consume trace-like records (context build
    records, execution records, policy decisions, review notes, safety
    reports). This is the interchange envelope, not a storage system. Richer,
    project-specific fields belong under ``metadata`` (namespaced).
    """

    artifact_id: str
    artifact_type: str
    source_project: str
    created_at: str
    subject_ref: Optional[str] = None
    summary: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    decision_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("ReviewArtifact.artifact_id must be non-empty")
        if not self.artifact_type:
            raise ValueError("ReviewArtifact.artifact_type must be non-empty")
        if not self.source_project:
            raise ValueError("ReviewArtifact.source_project must be non-empty")
        if not self.created_at:
            raise ValueError("ReviewArtifact.created_at must be non-empty")


# ---------------------------------------------------------------------------
# MemoryArtifact — durable or semi-durable agent memory record
# ---------------------------------------------------------------------------

@dataclass
class MemoryArtifact:
    """A durable or semi-durable agent memory record.

    Distinct from transient conversation context, raw tool output, and traces:
    a MemoryArtifact is a curated, reusable fact/preference/convention carrying
    its own sensitivity and provenance. Memory content may be sensitive, so
    ``sensitivity`` and ``provenance`` are first-class.
    """

    memory_id: str
    memory_type: str
    content: str
    source: str
    created_at: str
    updated_at: Optional[str] = None
    scope: Optional[str] = None
    sensitivity: str = "internal"
    confidence: Optional[float] = None
    expires_at: Optional[str] = None
    dependency_refs: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.memory_id:
            raise ValueError("MemoryArtifact.memory_id must be non-empty")
        if not self.memory_type:
            raise ValueError("MemoryArtifact.memory_type must be non-empty")
        if not self.content:
            raise ValueError("MemoryArtifact.content must be non-empty")
        if not self.source:
            raise ValueError("MemoryArtifact.source must be non-empty")
        if not self.created_at:
            raise ValueError("MemoryArtifact.created_at must be non-empty")
        if self.sensitivity not in _SENSITIVITY_LEVELS:
            raise ValueError(
                f"MemoryArtifact.sensitivity must be one of {_SENSITIVITY_LEVELS}"
            )


# ---------------------------------------------------------------------------
# SessionHandoff — compact continuity pack between sessions
# ---------------------------------------------------------------------------

@dataclass
class SessionHandoff:
    """A compact continuity pack carried between agent sessions.

    Summarizes state needed to resume work without replaying full context. It
    references (does not inline) durable memory via ``memory_refs``.
    """

    handoff_id: str
    from_session_id: str
    created_at: str
    summary: str
    to_session_id: Optional[str] = None
    sensitivity: str = "internal"
    open_threads: List[str] = field(default_factory=list)
    memory_refs: List[str] = field(default_factory=list)
    expires_at: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.handoff_id:
            raise ValueError("SessionHandoff.handoff_id must be non-empty")
        if not self.from_session_id:
            raise ValueError("SessionHandoff.from_session_id must be non-empty")
        if not self.created_at:
            raise ValueError("SessionHandoff.created_at must be non-empty")
        if not self.summary:
            raise ValueError("SessionHandoff.summary must be non-empty")
        if self.sensitivity not in _SENSITIVITY_LEVELS:
            raise ValueError(
                f"SessionHandoff.sensitivity must be one of {_SENSITIVITY_LEVELS}"
            )


# ---------------------------------------------------------------------------
# LessonCard — a reviewed, reusable lesson derived from traces
# ---------------------------------------------------------------------------

@dataclass
class LessonCard:
    """A reusable lesson derived from traces and approved for reuse.

    Not a raw trace, raw memory, or generic prompt fragment. ``lifecycle_state``
    gates activation: a lesson should pass through review before it is
    ``active``.
    """

    lesson_id: str
    title: str
    body: str
    created_at: str
    lifecycle_state: str = "draft"
    scope: Optional[str] = None
    sensitivity: str = "internal"
    applicability: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    expires_at: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.lesson_id:
            raise ValueError("LessonCard.lesson_id must be non-empty")
        if not self.title:
            raise ValueError("LessonCard.title must be non-empty")
        if not self.body:
            raise ValueError("LessonCard.body must be non-empty")
        if not self.created_at:
            raise ValueError("LessonCard.created_at must be non-empty")
        if self.lifecycle_state not in _LIFECYCLE_STATES:
            raise ValueError(
                f"LessonCard.lifecycle_state must be one of {_LIFECYCLE_STATES}"
            )
        if self.sensitivity not in _SENSITIVITY_LEVELS:
            raise ValueError(
                f"LessonCard.sensitivity must be one of {_SENSITIVITY_LEVELS}"
            )


# ---------------------------------------------------------------------------
# SkillCard — a reviewed, reusable procedure derived from traces
# ---------------------------------------------------------------------------

@dataclass
class SkillCard:
    """A reusable procedure/skill derived from traces and approved for reuse.

    Like LessonCard, ``lifecycle_state`` gates activation. ``steps`` and
    ``preconditions`` describe how and when to apply the skill.
    """

    skill_id: str
    name: str
    description: str
    created_at: str
    lifecycle_state: str = "draft"
    steps: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    scope: Optional[str] = None
    sensitivity: str = "internal"
    source_refs: List[str] = field(default_factory=list)
    expires_at: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.skill_id:
            raise ValueError("SkillCard.skill_id must be non-empty")
        if not self.name:
            raise ValueError("SkillCard.name must be non-empty")
        if not self.description:
            raise ValueError("SkillCard.description must be non-empty")
        if not self.created_at:
            raise ValueError("SkillCard.created_at must be non-empty")
        if self.lifecycle_state not in _LIFECYCLE_STATES:
            raise ValueError(
                f"SkillCard.lifecycle_state must be one of {_LIFECYCLE_STATES}"
            )
        if self.sensitivity not in _SENSITIVITY_LEVELS:
            raise ValueError(
                f"SkillCard.sensitivity must be one of {_SENSITIVITY_LEVELS}"
            )


# ---------------------------------------------------------------------------
# EvaluationArtifact — statistical / model-evaluation decision report
# ---------------------------------------------------------------------------

@dataclass
class EvaluationArtifact:
    """A statistical / offline model-evaluation report carried with semantics.

    Makes the intended meaning explicit so agents cannot misuse a headline
    score: value estimates, uncertainty, support diagnostics, warnings, and a
    decision recommendation. ``support_state`` and ``recommendation_kind``
    encode that a high-risk evaluation is not deployment evidence.
    """

    artifact_id: str
    producer: str
    created_at: str
    artifact_type: str = "offline_policy_evaluation"
    producer_version: Optional[str] = None
    target_estimand: Optional[str] = None
    candidate_policy: Optional[str] = None
    baseline_policy: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    uncertainty: Dict[str, Any] = field(default_factory=dict)
    support_state: str = "ok"
    support_diagnostics: Dict[str, Any] = field(default_factory=dict)
    propensity_diagnostics: Dict[str, Any] = field(default_factory=dict)
    sensitivity: str = "internal"
    warnings: List[str] = field(default_factory=list)
    recommendation: Optional[str] = None
    recommendation_kind: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    _SUPPORT_STATES = frozenset({"ok", "caution", "high_risk"})
    _RECOMMENDATION_KINDS = frozenset(
        {"deploy", "do_not_deploy", "experiment_ready", "needs_more_data"}
    )

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("EvaluationArtifact.artifact_id must be non-empty")
        if not self.producer:
            raise ValueError("EvaluationArtifact.producer must be non-empty")
        if not self.created_at:
            raise ValueError("EvaluationArtifact.created_at must be non-empty")
        if not self.artifact_type:
            raise ValueError("EvaluationArtifact.artifact_type must be non-empty")
        if self.support_state not in self._SUPPORT_STATES:
            raise ValueError(
                f"EvaluationArtifact.support_state must be one of {self._SUPPORT_STATES}"
            )
        if (
            self.recommendation_kind is not None
            and self.recommendation_kind not in self._RECOMMENDATION_KINDS
        ):
            raise ValueError(
                "EvaluationArtifact.recommendation_kind must be one of "
                f"{self._RECOMMENDATION_KINDS}"
            )
        if self.sensitivity not in _SENSITIVITY_LEVELS:
            raise ValueError(
                f"EvaluationArtifact.sensitivity must be one of {_SENSITIVITY_LEVELS}"
            )
        # A high-risk evaluation must never recommend deployment: a high-risk
        # support state means the evidence cannot back a deploy decision.
        if self.support_state == "high_risk" and self.recommendation_kind == "deploy":
            raise ValueError(
                "EvaluationArtifact: recommendation_kind 'deploy' is not permitted "
                "when support_state is 'high_risk' (a high-risk evaluation is not "
                "deployment evidence)"
            )


# ---------------------------------------------------------------------------
# ArtifactSafetyGateRequest — inputs to an artifact safety gate capability
# ---------------------------------------------------------------------------

@dataclass
class ArtifactSafetyGateRequest:
    """Inputs to an optional artifact safety gate run.

    Describes what to check (artifact paths, diff scope, repository root) and
    how (policy level, output format). Implementation-neutral: it does not
    name a specific scanner or rule set.
    """

    request_id: str
    repository_root: str
    artifact_paths: List[str] = field(default_factory=list)
    diff_scope: Optional[str] = None
    policy_level: str = "standard"
    output_format: str = "json"
    capability_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("ArtifactSafetyGateRequest.request_id must be non-empty")
        if not self.repository_root:
            raise ValueError(
                "ArtifactSafetyGateRequest.repository_root must be non-empty"
            )


# ---------------------------------------------------------------------------
# ArtifactSafetyReport — output of an artifact safety gate capability
# ---------------------------------------------------------------------------

@dataclass
class ArtifactSafetyReport:
    """Output of an artifact safety gate run.

    ``mode`` distinguishes an advisory check from a blocking gate; ``decision``
    is the pass/fail verdict. ``findings`` is a list of objects, each carrying
    a severity, message, optional stable fingerprint, and remediation hint
    (shape defined in the JSON schema).
    """

    report_id: str
    gate_id: str
    decision: str
    created_at: str
    mode: str = "advisory"
    request_id: Optional[str] = None
    target_ref: Optional[str] = None
    summary: Optional[str] = None
    findings: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    _DECISIONS = frozenset({"pass", "fail"})
    _MODES = frozenset({"advisory", "blocking"})

    def __post_init__(self) -> None:
        if not self.report_id:
            raise ValueError("ArtifactSafetyReport.report_id must be non-empty")
        if not self.gate_id:
            raise ValueError("ArtifactSafetyReport.gate_id must be non-empty")
        if not self.created_at:
            raise ValueError("ArtifactSafetyReport.created_at must be non-empty")
        if self.decision not in self._DECISIONS:
            raise ValueError(
                f"ArtifactSafetyReport.decision must be one of {self._DECISIONS}"
            )
        if self.mode not in self._MODES:
            raise ValueError(
                f"ArtifactSafetyReport.mode must be one of {self._MODES}"
            )


# ===========================================================================
# Cryptographic and observability bindings
#
# CapabilityTokenSignature (#44) defines a detached signature over a
# JCS-canonicalized CapabilityToken payload; the signature attaches to the
# Core token under the namespaced extension key `x_weaver_signature` so Core
# stays unchanged. OtelTraceMapping (#47) carries the OTel identifiers and
# GenAI semantic-convention attributes that a Weaver TraceEvent maps to.
# Field-by-field documentation:
#   - docs/SIGNING.md and docs/adr/001-capability-token-signing.md
#   - docs/OTEL_MAPPING.md
# ===========================================================================


# ---------------------------------------------------------------------------
# CapabilityTokenSignature — RFC 8785 JCS detached signature for tokens
# ---------------------------------------------------------------------------

@dataclass
class CapabilityTokenSignature:
    """Detached signature over a JCS-canonicalized CapabilityToken payload.

    Attached to a CapabilityToken under the namespaced extension key
    ``x_weaver_signature``. Verifiers MUST reject signatures whose ``alg`` or
    ``canonicalization`` is not in the published registry. See
    ``docs/SIGNING.md`` for verification pseudocode and ``docs/adr/001-capability-token-signing.md``
    for the design decision.
    """

    alg: str
    kid: str
    sig: str
    canonicalization: str = "JCS"
    signed_at: Optional[str] = None

    _VALID_ALGS = frozenset({"ed25519", "es256"})
    _VALID_CANONICALIZATIONS = frozenset({"JCS"})
    # Both registered algorithms produce 64-byte raw signatures (ed25519 RFC 8032
    # raw, or es256 IEEE P1363 r||s), which encode to exactly 86 base64url chars
    # without padding. See docs/SIGNING.md for the algorithm registry.
    _SIG_BASE64URL_LEN = 86
    _SIG_BASE64URL_ALPHABET = frozenset(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    )

    def __post_init__(self) -> None:
        if self.alg not in self._VALID_ALGS:
            raise ValueError(
                f"CapabilityTokenSignature.alg must be one of {self._VALID_ALGS}"
            )
        if not self.kid:
            raise ValueError("CapabilityTokenSignature.kid must be non-empty")
        if not self.sig:
            raise ValueError("CapabilityTokenSignature.sig must be non-empty")
        if (
            len(self.sig) != self._SIG_BASE64URL_LEN
            or not all(c in self._SIG_BASE64URL_ALPHABET for c in self.sig)
        ):
            raise ValueError(
                "CapabilityTokenSignature.sig must be 86 base64url characters "
                "(64 raw bytes, RFC 4648 §5 no padding); see docs/SIGNING.md"
            )
        if self.canonicalization not in self._VALID_CANONICALIZATIONS:
            raise ValueError(
                "CapabilityTokenSignature.canonicalization must be one of "
                f"{self._VALID_CANONICALIZATIONS}"
            )


# ---------------------------------------------------------------------------
# OtelTraceMapping — TraceEvent → OpenTelemetry GenAI span attributes
# ---------------------------------------------------------------------------

@dataclass
class OtelTraceMapping:
    """Mapping of a Weaver TraceEvent onto an OpenTelemetry span.

    Carries the OTel trace/span identifiers and the GenAI semantic-convention
    attributes downstream observability tools consume (e.g. Datadog,
    Honeycomb, New Relic). The full field-by-field mapping lives in
    ``docs/OTEL_MAPPING.md``, pinned to a specific OTel semconv snapshot.
    """

    trace_id: str
    span_id: str
    span_kind: str
    gen_ai_operation_name: Optional[str] = None
    gen_ai_agent_id: Optional[str] = None
    gen_ai_agent_name: Optional[str] = None
    gen_ai_tool_name: Optional[str] = None
    gen_ai_system: Optional[str] = None
    parent_span_id: Optional[str] = None
    semconv_version: Optional[str] = None

    _VALID_SPAN_KINDS = frozenset(
        {"INTERNAL", "CLIENT", "SERVER", "PRODUCER", "CONSUMER"}
    )
    _TRACE_ID_LEN = 32  # 16 bytes hex per W3C Trace Context
    _SPAN_ID_LEN = 16  # 8 bytes hex per W3C Trace Context

    def __post_init__(self) -> None:
        if not self.trace_id:
            raise ValueError("OtelTraceMapping.trace_id must be non-empty")
        # W3C Trace Context requires lowercase hex; producers must normalize
        # before constructing this object (https://www.w3.org/TR/trace-context/#trace-id).
        if len(self.trace_id) != self._TRACE_ID_LEN or not all(
            c in "0123456789abcdef" for c in self.trace_id
        ):
            raise ValueError(
                "OtelTraceMapping.trace_id must be 32 lowercase hex characters "
                "(W3C Trace Context)"
            )
        if not self.span_id:
            raise ValueError("OtelTraceMapping.span_id must be non-empty")
        if len(self.span_id) != self._SPAN_ID_LEN or not all(
            c in "0123456789abcdef" for c in self.span_id
        ):
            raise ValueError(
                "OtelTraceMapping.span_id must be 16 lowercase hex characters "
                "(W3C Trace Context)"
            )
        if self.span_kind not in self._VALID_SPAN_KINDS:
            raise ValueError(
                f"OtelTraceMapping.span_kind must be one of {self._VALID_SPAN_KINDS}"
            )
        if self.parent_span_id is not None and (
            len(self.parent_span_id) != self._SPAN_ID_LEN
            or not all(c in "0123456789abcdef" for c in self.parent_span_id)
        ):
            raise ValueError(
                "OtelTraceMapping.parent_span_id must be 16 lowercase hex characters"
            )
