"""
weaver_contracts — Minimal Python contracts for the Weaver Stack.

Core contracts:  SelectableItem, ChoiceCard, RoutingDecision,
                 Capability, CapabilityToken, PolicyDecision,
                 Frame, Handle, TraceEvent

Extended contracts: see weaver_contracts.extended

Version info: see weaver_contracts.version
"""

from .core import (
    SelectableItem,
    ChoiceCard,
    RoutingDecision,
    Capability,
    CapabilityToken,
    PolicyDecision,
    Frame,
    Handle,
    TraceEvent,
)
from .version import CONTRACT_VERSION, SCHEMA_VERSION_PREFIX

__all__ = [
    "SelectableItem",
    "ChoiceCard",
    "RoutingDecision",
    "Capability",
    "CapabilityToken",
    "PolicyDecision",
    "Frame",
    "Handle",
    "TraceEvent",
    "CONTRACT_VERSION",
    "SCHEMA_VERSION_PREFIX",
]
