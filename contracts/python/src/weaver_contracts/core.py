"""
Core Weaver contracts.

All types in this module correspond 1:1 to the JSON Schemas in contracts/json/.
These are minimal, stable types. No third-party runtime dependencies.

Design rules:
- Use dataclasses with field-level type annotations.
- Optional fields default to None or empty collections.
- Post-init validation enforces non-negotiable invariants.
- All IDs and required string fields must be non-empty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# SelectableItem
# ---------------------------------------------------------------------------

@dataclass
class SelectableItem:
    """A single option within a ChoiceCard presented to the LLM for selection."""

    id: str
    label: str
    description: str
    capability_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("SelectableItem.id must be non-empty")
        if not self.label:
            raise ValueError("SelectableItem.label must be non-empty")
        if not self.description:
            raise ValueError("SelectableItem.description must be non-empty")


# ---------------------------------------------------------------------------
# ChoiceCard
# ---------------------------------------------------------------------------

@dataclass
class ChoiceCard:
    """A bounded set of SelectableItems presented to the LLM as a structured menu."""

    id: str
    items: List[SelectableItem]
    context_hint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("ChoiceCard.id must be non-empty")
        if not self.items:
            raise ValueError("ChoiceCard.items must contain at least one SelectableItem")


# ---------------------------------------------------------------------------
# RoutingDecision
# ---------------------------------------------------------------------------

@dataclass
class RoutingDecision:
    """The output of the contextweaver routing phase."""

    id: str
    choice_cards: List[ChoiceCard]
    timestamp: datetime
    selected_item_id: Optional[str] = None
    selected_card_id: Optional[str] = None
    context_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("RoutingDecision.id must be non-empty")
        if not self.choice_cards:
            raise ValueError("RoutingDecision.choice_cards must contain at least one ChoiceCard")


# ---------------------------------------------------------------------------
# Capability
# ---------------------------------------------------------------------------

@dataclass
class Capability:
    """A named, versioned unit of executable functionality in agent-kernel."""

    id: str
    name: str
    version: str
    description: str
    input_schema_ref: Optional[str] = None
    output_schema_ref: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Capability.id must be non-empty")
        if not self.name:
            raise ValueError("Capability.name must be non-empty")
        if not self.version:
            raise ValueError("Capability.version must be non-empty")
        if not self.description:
            raise ValueError("Capability.description must be non-empty")


# ---------------------------------------------------------------------------
# CapabilityToken
# ---------------------------------------------------------------------------

@dataclass
class CapabilityToken:
    """A scoped authorization credential for capability invocation."""

    token_id: str
    principal: str
    scope: List[str]
    issued_at: datetime
    expires_at: Optional[datetime] = None
    single_use: bool = False
    issuer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.token_id:
            raise ValueError("CapabilityToken.token_id must be non-empty")
        if not self.principal:
            raise ValueError("CapabilityToken.principal must be non-empty")
        if not self.scope:
            raise ValueError("CapabilityToken.scope must contain at least one capability ID")
        if not self.single_use and self.expires_at is None:
            raise ValueError(
                "CapabilityToken must have expires_at unless single_use is True"
            )


# ---------------------------------------------------------------------------
# PolicyDecision
# ---------------------------------------------------------------------------

@dataclass
class PolicyDecision:
    """The authorization verdict produced by the agent-kernel policy engine."""

    decision_id: str
    decision: str  # "allow" | "deny"
    capability_id: str
    principal: str
    timestamp: datetime
    token_id: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    _VALID_DECISIONS = frozenset({"allow", "deny"})

    def __post_init__(self) -> None:
        if not self.decision_id:
            raise ValueError("PolicyDecision.decision_id must be non-empty")
        if self.decision not in self._VALID_DECISIONS:
            raise ValueError(f"PolicyDecision.decision must be one of {self._VALID_DECISIONS}")
        if not self.capability_id:
            raise ValueError("PolicyDecision.capability_id must be non-empty")
        if not self.principal:
            raise ValueError("PolicyDecision.principal must be non-empty")


# ---------------------------------------------------------------------------
# Frame
# ---------------------------------------------------------------------------

@dataclass
class Frame:
    """A safe, filtered view of a tool execution result produced by the firewall.

    Invariant: A Frame never contains raw tool output. Raw output is stored
    as a Handle. contextweaver and the LLM consume only Frames.
    """

    frame_id: str
    capability_id: str
    summary: str
    created_at: datetime
    structured_data: Optional[Dict[str, Any]] = None
    handle_refs: List[str] = field(default_factory=list)
    redaction_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.frame_id:
            raise ValueError("Frame.frame_id must be non-empty")
        if not self.capability_id:
            raise ValueError("Frame.capability_id must be non-empty")
        if not self.summary:
            raise ValueError("Frame.summary must be non-empty")


# ---------------------------------------------------------------------------
# Handle
# ---------------------------------------------------------------------------

@dataclass
class Handle:
    """An opaque reference to a raw artifact stored in the HandleStore.

    Resolution requires authorization through agent-kernel.
    """

    handle_id: str
    capability_id: str
    artifact_type: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_policy: Optional[str] = None
    byte_size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.handle_id:
            raise ValueError("Handle.handle_id must be non-empty")
        if not self.capability_id:
            raise ValueError("Handle.capability_id must be non-empty")
        if not self.artifact_type:
            raise ValueError("Handle.artifact_type must be non-empty")
        if self.byte_size is not None and self.byte_size < 0:
            raise ValueError("Handle.byte_size must be non-negative")


# ---------------------------------------------------------------------------
# TraceEvent
# ---------------------------------------------------------------------------

TRACE_EVENT_TYPES = frozenset({
    "capability_authorized",
    "capability_denied",
    "capability_executed",
    "firewall_applied",
    "handle_created",
    "handle_resolved",
    "token_issued",
    "token_invalidated",
    "flow_started",
    "flow_step_started",
    "flow_step_completed",
    "flow_completed",
    "flow_failed",
})

TRACE_EVENT_OUTCOMES = frozenset({"success", "failure", "partial"})


@dataclass
class TraceEvent:
    """An immutable audit log entry. Append-only; must not be modified after creation."""

    event_id: str
    event_type: str
    timestamp: datetime
    capability_id: Optional[str] = None
    principal: Optional[str] = None
    decision_id: Optional[str] = None
    frame_id: Optional[str] = None
    handle_id: Optional[str] = None
    outcome: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("TraceEvent.event_id must be non-empty")
        if not self.event_type:
            raise ValueError("TraceEvent.event_type must be non-empty")
        if self.event_type not in TRACE_EVENT_TYPES:
            raise ValueError(
                f"TraceEvent.event_type must be one of {TRACE_EVENT_TYPES}"
            )
        if self.outcome is not None and self.outcome not in TRACE_EVENT_OUTCOMES:
            raise ValueError(
                f"TraceEvent.outcome must be one of {TRACE_EVENT_OUTCOMES} or None"
            )
