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
