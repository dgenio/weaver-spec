"""
Roundtrip tests: load example JSON payloads and construct Core contract
dataclasses from them, validating that required fields are present and
invariants hold.
"""

import json
import pathlib
from datetime import datetime, timezone

import pytest

from weaver_contracts.core import (
    CapabilityToken,
    ChoiceCard,
    Frame,
    Handle,
    PolicyDecision,
    RoutingDecision,
    SelectableItem,
    TraceEvent,
)
from weaver_contracts.version import CONTRACT_VERSION, is_compatible

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
PAYLOADS_DIR = REPO_ROOT / "examples" / "sample_payloads"


def load_payload(name: str) -> dict:
    path = PAYLOADS_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)


def parse_dt(s: str) -> datetime:
    """Parse an ISO 8601 string to a datetime (UTC)."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

class TestVersion:
    def test_contract_version_format(self):
        parts = CONTRACT_VERSION.split(".")
        assert len(parts) == 3, "CONTRACT_VERSION must be MAJOR.MINOR.PATCH"
        assert all(p.isdigit() for p in parts), "Version parts must be numeric"

    def test_is_compatible_same_major(self):
        assert is_compatible(CONTRACT_VERSION) is True

    def test_is_compatible_different_major(self):
        major = int(CONTRACT_VERSION.split(".")[0])
        incompatible = f"{major + 1}.0.0"
        assert is_compatible(incompatible) is False

    def test_is_compatible_invalid_version(self):
        with pytest.raises(ValueError):
            is_compatible("not-a-version")


# ---------------------------------------------------------------------------
# SelectableItem
# ---------------------------------------------------------------------------

class TestSelectableItem:
    def test_valid_construction(self):
        item = SelectableItem(id="item-1", label="Search docs", description="Search documentation")
        assert item.id == "item-1"
        assert item.capability_id is None

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="id must be non-empty"):
            SelectableItem(id="", label="x", description="x")

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="label must be non-empty"):
            SelectableItem(id="x", label="", description="x")

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="description must be non-empty"):
            SelectableItem(id="x", label="x", description="")


# ---------------------------------------------------------------------------
# ChoiceCard
# ---------------------------------------------------------------------------

class TestChoiceCard:
    def _item(self, i: int = 1) -> SelectableItem:
        return SelectableItem(id=f"item-{i}", label=f"Option {i}", description=f"Desc {i}")

    def test_valid_construction(self):
        card = ChoiceCard(id="card-1", items=[self._item()])
        assert len(card.items) == 1

    def test_empty_items_raises(self):
        with pytest.raises(ValueError, match="items must contain"):
            ChoiceCard(id="card-1", items=[])

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="id must be non-empty"):
            ChoiceCard(id="", items=[self._item()])


# ---------------------------------------------------------------------------
# RoutingDecision
# ---------------------------------------------------------------------------

class TestRoutingDecision:
    def _card(self) -> ChoiceCard:
        item = SelectableItem(id="i1", label="L", description="D")
        return ChoiceCard(id="card-1", items=[item])

    def test_valid_construction(self):
        rd = RoutingDecision(
            id="rd-1",
            choice_cards=[self._card()],
            timestamp=datetime.now(timezone.utc),
        )
        assert rd.selected_item_id is None

    def test_empty_choice_cards_raises(self):
        with pytest.raises(ValueError, match="choice_cards"):
            RoutingDecision(id="rd-1", choice_cards=[], timestamp=datetime.now(timezone.utc))

    def test_from_payload(self):
        payload = load_payload("routing_decision")
        card_data = payload["choice_cards"][0]
        items = [
            SelectableItem(
                id=it["id"],
                label=it["label"],
                description=it["description"],
                capability_id=it.get("capability_id"),
            )
            for it in card_data["items"]
        ]
        card = ChoiceCard(id=card_data["id"], items=items, context_hint=card_data.get("context_hint"))
        rd = RoutingDecision(
            id=payload["id"],
            choice_cards=[card],
            timestamp=parse_dt(payload["timestamp"]),
            selected_item_id=payload.get("selected_item_id"),
        )
        assert rd.id == payload["id"]


# ---------------------------------------------------------------------------
# CapabilityToken
# ---------------------------------------------------------------------------

class TestCapabilityToken:
    def test_valid_with_expiry(self):
        token = CapabilityToken(
            token_id="tok-1",
            principal="agent-1",
            scope=["cap.search"],
            issued_at=datetime.now(timezone.utc),
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        assert token.single_use is False

    def test_valid_single_use_no_expiry(self):
        token = CapabilityToken(
            token_id="tok-2",
            principal="agent-1",
            scope=["cap.search"],
            issued_at=datetime.now(timezone.utc),
            single_use=True,
        )
        assert token.expires_at is None

    def test_empty_scope_raises(self):
        with pytest.raises(ValueError, match="scope must contain"):
            CapabilityToken(
                token_id="tok-3",
                principal="agent-1",
                scope=[],
                issued_at=datetime.now(timezone.utc),
                expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            )

    def test_no_expiry_not_single_use_raises(self):
        """Invariant I-06: tokens must have expiry or single_use."""
        with pytest.raises(ValueError, match="expires_at"):
            CapabilityToken(
                token_id="tok-4",
                principal="agent-1",
                scope=["cap.x"],
                issued_at=datetime.now(timezone.utc),
                single_use=False,
                expires_at=None,
            )

    def test_from_payload(self):
        payload = load_payload("capability_token")
        token = CapabilityToken(
            token_id=payload["token_id"],
            principal=payload["principal"],
            scope=payload["scope"],
            issued_at=parse_dt(payload["issued_at"]),
            expires_at=parse_dt(payload["expires_at"]) if payload.get("expires_at") else None,
            single_use=payload.get("single_use", False),
        )
        assert token.token_id == payload["token_id"]
        assert len(token.scope) > 0


# ---------------------------------------------------------------------------
# PolicyDecision
# ---------------------------------------------------------------------------

class TestPolicyDecision:
    def test_allow(self):
        pd = PolicyDecision(
            decision_id="pd-1",
            decision="allow",
            capability_id="cap.search",
            principal="agent-1",
            timestamp=datetime.now(timezone.utc),
        )
        assert pd.decision == "allow"

    def test_deny(self):
        pd = PolicyDecision(
            decision_id="pd-2",
            decision="deny",
            capability_id="cap.delete",
            principal="agent-1",
            timestamp=datetime.now(timezone.utc),
            reason="Principal not authorized for destructive operations",
        )
        assert pd.decision == "deny"

    def test_invalid_decision_raises(self):
        with pytest.raises(ValueError, match="decision must be one of"):
            PolicyDecision(
                decision_id="pd-3",
                decision="maybe",
                capability_id="cap.x",
                principal="agent-1",
                timestamp=datetime.now(timezone.utc),
            )


# ---------------------------------------------------------------------------
# Frame
# ---------------------------------------------------------------------------

class TestFrame:
    def test_valid_construction(self):
        frame = Frame(
            frame_id="frame-1",
            capability_id="cap.search",
            summary="Found 3 documents matching the query.",
            created_at=datetime.now(timezone.utc),
        )
        assert frame.handle_refs == []

    def test_empty_summary_raises(self):
        with pytest.raises(ValueError, match="summary must be non-empty"):
            Frame(
                frame_id="frame-2",
                capability_id="cap.x",
                summary="",
                created_at=datetime.now(timezone.utc),
            )

    def test_from_payload(self):
        payload = load_payload("frame_with_handles")
        frame = Frame(
            frame_id=payload["frame_id"],
            capability_id=payload["capability_id"],
            summary=payload["summary"],
            created_at=parse_dt(payload["created_at"]),
            handle_refs=payload.get("handle_refs", []),
            redaction_notes=payload.get("redaction_notes"),
        )
        assert frame.frame_id == payload["frame_id"]

    def test_invariant_no_raw_output(self):
        """Frame dataclass does not expose a raw_output field (invariant I-01)."""
        frame = Frame(
            frame_id="f1",
            capability_id="c1",
            summary="ok",
            created_at=datetime.now(timezone.utc),
        )
        assert not hasattr(frame, "raw_output"), (
            "Frame must not have a raw_output attribute (invariant I-01)"
        )


# ---------------------------------------------------------------------------
# Handle
# ---------------------------------------------------------------------------

class TestHandle:
    def test_valid_construction(self):
        handle = Handle(
            handle_id="handle-1",
            capability_id="cap.search",
            artifact_type="application/json",
            created_at=datetime.now(timezone.utc),
        )
        assert handle.byte_size is None

    def test_negative_byte_size_raises(self):
        with pytest.raises(ValueError, match="byte_size must be non-negative"):
            Handle(
                handle_id="handle-2",
                capability_id="cap.x",
                artifact_type="text/plain",
                created_at=datetime.now(timezone.utc),
                byte_size=-1,
            )


# ---------------------------------------------------------------------------
# TraceEvent
# ---------------------------------------------------------------------------

class TestTraceEvent:
    def test_valid_construction(self):
        event = TraceEvent(
            event_id="evt-1",
            event_type="capability_executed",
            timestamp=datetime.now(timezone.utc),
            capability_id="cap.search",
            outcome="success",
        )
        assert event.outcome == "success"

    def test_invalid_outcome_raises(self):
        with pytest.raises(ValueError, match="outcome must be one of"):
            TraceEvent(
                event_id="evt-2",
                event_type="capability_executed",
                timestamp=datetime.now(timezone.utc),
                outcome="unknown",
            )

    def test_invalid_event_type_raises(self):
        with pytest.raises(ValueError, match="event_type must be one of"):
            TraceEvent(
                event_id="evt-3",
                event_type="invalid_type",
                timestamp=datetime.now(timezone.utc),
            )

    def test_no_event_id_raises(self):
        with pytest.raises(ValueError, match="event_id must be non-empty"):
            TraceEvent(
                event_id="",
                event_type="capability_executed",
                timestamp=datetime.now(timezone.utc),
            )
