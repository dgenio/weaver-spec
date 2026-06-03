#!/usr/bin/env python3
"""Runnable Weaver reference implementation (issue #76).

This is an **example**, not part of the ``weaver_contracts`` package: it is never
imported by the package and never published to PyPI. It exists so a newcomer can
read one file and see every Core contract produced, signed, verified, and
validated end-to-end with nothing from the sibling repos required. See
``README.md`` in this directory for the "Become Weaver-compatible in 30 minutes"
guide, and ``AGENTS.md`` for the repository scope rule that places executable
demonstrations here (CI-checked example tier) rather than in the package.

What it does, in order:

1. Constructs every **Core** artifact with the ``weaver_contracts`` dataclasses
   (``RoutingDecision``, ``CapabilityToken``, ``PolicyDecision``, ``Frame``,
   ``Handle``, ``TraceEvent``) — exercising their construction-time validation.
2. Gathers them into an Extended ``TraceBundle``.
3. **Mints a real signature**: generates an *ephemeral* ed25519 keypair,
   canonicalizes the bundle (RFC 8785 JCS, excluding ``signature``), signs it,
   and attaches a ``CapabilityTokenSignature``. The private key never leaves
   this process and is discarded on exit.
4. **Verifies** that signature against the ephemeral public key.
5. **Validates** every emitted payload — and the signed bundle — against the
   JSON Schemas in ``contracts/json/`` (the language-agnostic source of truth).
6. Asserts invariants **I-01** (no Frame carries raw output) and **I-02** (every
   PolicyDecision has a matching TraceEvent). See ``docs/INVARIANTS.md``.

Exit code is non-zero if any construction, signature, schema, or invariant check
fails, so CI catches contract drift the moment a Core schema changes.

Usage::

    pip install -e "contracts/python[dev]"   # weaver_contracts + jcs/cryptography/jsonschema
    python examples/reference_impl/reference_impl.py
"""

from __future__ import annotations

import base64
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import jcs
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

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
from weaver_contracts.extended import CapabilityTokenSignature, TraceBundle
from weaver_contracts.version import CONTRACT_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
EXTENDED_SCHEMA_DIR = CORE_SCHEMA_DIR / "extended"

# Forbidden raw-output keys on a Frame (I-01); mirrors conformance/run.py.
FORBIDDEN_FRAME_KEYS = frozenset({"raw_output", "raw", "raw_result", "tool_output"})

PRINCIPAL = "agent-session-ref-001"
CAPABILITY = "org.example.search_docs"


# ---------------------------------------------------------------------------
# Wire serialization — dataclass -> JSON-ready dict (omit None / empty)
# ---------------------------------------------------------------------------

def _iso_z(value: datetime) -> str:
    """Render a datetime as an RFC 3339 / ISO 8601 UTC string ending in ``Z``."""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _prune(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Drop ``None`` values and empty collections so the wire form matches the
    style of ``examples/sample_payloads/`` (optional, absent fields are omitted)."""
    out: Dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        out[key] = value
    return out


def selectable_item_wire(item: SelectableItem) -> Dict[str, Any]:
    return _prune(
        {
            "id": item.id,
            "label": item.label,
            "description": item.description,
            "capability_id": item.capability_id,
            "metadata": item.metadata,
        }
    )


def choice_card_wire(card: ChoiceCard) -> Dict[str, Any]:
    return _prune(
        {
            "id": card.id,
            "context_hint": card.context_hint,
            "items": [selectable_item_wire(i) for i in card.items],
            "metadata": card.metadata,
        }
    )


def routing_decision_wire(rd: RoutingDecision) -> Dict[str, Any]:
    return _prune(
        {
            "id": rd.id,
            "choice_cards": [choice_card_wire(c) for c in rd.choice_cards],
            "selected_item_id": rd.selected_item_id,
            "selected_card_id": rd.selected_card_id,
            "timestamp": _iso_z(rd.timestamp),
            "context_summary": rd.context_summary,
            "metadata": rd.metadata,
        }
    )


def capability_token_wire(tok: CapabilityToken) -> Dict[str, Any]:
    return _prune(
        {
            "token_id": tok.token_id,
            "principal": tok.principal,
            "scope": tok.scope,
            "issued_at": _iso_z(tok.issued_at),
            "expires_at": _iso_z(tok.expires_at) if tok.expires_at else None,
            "single_use": tok.single_use,
            "issuer": tok.issuer,
            "metadata": tok.metadata,
        }
    )


def policy_decision_wire(pd: PolicyDecision) -> Dict[str, Any]:
    return _prune(
        {
            "decision_id": pd.decision_id,
            "decision": pd.decision,
            "capability_id": pd.capability_id,
            "principal": pd.principal,
            "token_id": pd.token_id,
            "reason": pd.reason,
            "timestamp": _iso_z(pd.timestamp),
            "metadata": pd.metadata,
        }
    )


def frame_wire(frame: Frame) -> Dict[str, Any]:
    return _prune(
        {
            "frame_id": frame.frame_id,
            "capability_id": frame.capability_id,
            "summary": frame.summary,
            "structured_data": frame.structured_data,
            "handle_refs": frame.handle_refs,
            "redaction_notes": frame.redaction_notes,
            "created_at": _iso_z(frame.created_at),
            "metadata": frame.metadata,
        }
    )


def handle_wire(handle: Handle) -> Dict[str, Any]:
    return _prune(
        {
            "handle_id": handle.handle_id,
            "capability_id": handle.capability_id,
            "artifact_type": handle.artifact_type,
            "created_at": _iso_z(handle.created_at),
            "expires_at": _iso_z(handle.expires_at) if handle.expires_at else None,
            "access_policy": handle.access_policy,
            "byte_size": handle.byte_size,
            "metadata": handle.metadata,
        }
    )


def trace_event_wire(event: TraceEvent) -> Dict[str, Any]:
    return _prune(
        {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "timestamp": _iso_z(event.timestamp),
            "capability_id": event.capability_id,
            "principal": event.principal,
            "decision_id": event.decision_id,
            "frame_id": event.frame_id,
            "handle_id": event.handle_id,
            "outcome": event.outcome,
            "error_message": event.error_message,
            "metadata": event.metadata,
        }
    )


def signature_wire(sig: CapabilityTokenSignature) -> Dict[str, Any]:
    return _prune(
        {
            "alg": sig.alg,
            "kid": sig.kid,
            "sig": sig.sig,
            "canonicalization": sig.canonicalization,
            "signed_at": sig.signed_at,
        }
    )


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

@dataclass
class Schemas:
    by_stem: Dict[str, dict]
    registry: Registry


def load_schemas() -> Schemas:
    by_stem: Dict[str, dict] = {}
    registry = Registry()
    for path in sorted(CORE_SCHEMA_DIR.glob("*.schema.json")) + sorted(
        EXTENDED_SCHEMA_DIR.glob("*.schema.json")
    ):
        schema = json.loads(path.read_text(encoding="utf-8"))
        by_stem[path.name.removesuffix(".schema.json")] = schema
        if "$id" in schema:
            registry = registry.with_resource(
                uri=schema["$id"],
                resource=Resource(contents=schema, specification=DRAFT202012),
            )
    return Schemas(by_stem=by_stem, registry=registry)


def schema_errors(payload: dict, schema: dict, registry: Registry) -> List[str]:
    validator = Draft202012Validator(
        schema, registry=registry, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    out: List[str] = []
    for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out


# ---------------------------------------------------------------------------
# Reference flow
# ---------------------------------------------------------------------------

def build_bundle() -> TraceBundle:
    """Construct one complete request's Core audit chain as a TraceBundle.

    Every dataclass below runs its ``__post_init__`` validation on construction,
    so this function also exercises the Python-side invariants.
    """
    t0 = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)

    routing = RoutingDecision(
        id="rd-ref-001",
        choice_cards=[
            ChoiceCard(
                id="card-retrieval",
                context_hint="Select a documentation retrieval action.",
                items=[
                    SelectableItem(
                        id="search-docs",
                        label="Search documentation",
                        description="Full-text search across the docs index.",
                        capability_id=CAPABILITY,
                    )
                ],
            )
        ],
        selected_item_id="search-docs",
        selected_card_id="card-retrieval",
        timestamp=t0,
        context_summary="User asked how to configure retries; routing to docs search.",
    )

    # A scoped, expiring authorization credential (I-06: scoped + expiring).
    token = CapabilityToken(
        token_id="tok-ref-001",
        principal=PRINCIPAL,
        scope=[CAPABILITY],
        issued_at=t0,
        expires_at=t0 + timedelta(hours=1),
        issuer="reference-impl",
    )

    policy = PolicyDecision(
        decision_id="pd-ref-001",
        decision="allow",
        capability_id=CAPABILITY,
        principal=PRINCIPAL,
        token_id=token.token_id,
        timestamp=t0 + timedelta(seconds=1),
    )

    # The firewall returns a Frame (safe to display) plus a Handle (opaque
    # reference to the raw artifact). The Frame carries NO raw output (I-01).
    handle = Handle(
        handle_id="handle-ref-001",
        capability_id=CAPABILITY,
        artifact_type="application/json",
        created_at=t0 + timedelta(seconds=5),
        expires_at=t0 + timedelta(days=1),
        byte_size=4096,
    )
    frame = Frame(
        frame_id="frame-ref-001",
        capability_id=CAPABILITY,
        summary="Found 2 documentation pages matching the query.",
        handle_refs=[handle.handle_id],
        created_at=t0 + timedelta(seconds=5),
    )

    # Every PolicyDecision is mirrored by a TraceEvent via decision_id (I-02).
    event = TraceEvent(
        event_id="te-ref-001",
        event_type="capability_executed",
        timestamp=t0 + timedelta(seconds=5),
        capability_id=CAPABILITY,
        principal=PRINCIPAL,
        decision_id=policy.decision_id,
        frame_id=frame.frame_id,
        handle_id=handle.handle_id,
        outcome="success",
    )

    return TraceBundle(
        bundle_id="tb-ref-001",
        routing_decision=routing,
        policy_decisions=[policy],
        frames=[frame],
        handles=[handle],
        trace_events=[event],
        created_at=_iso_z(t0 + timedelta(seconds=6)),
    )


def bundle_to_wire(bundle: TraceBundle) -> Dict[str, Any]:
    """Serialize a TraceBundle to its unsigned wire form (no ``signature``)."""
    return {
        "bundle_id": bundle.bundle_id,
        "routing_decision": routing_decision_wire(bundle.routing_decision),
        "policy_decisions": [policy_decision_wire(p) for p in bundle.policy_decisions],
        "frames": [frame_wire(f) for f in bundle.frames],
        "handles": [handle_wire(h) for h in bundle.handles],
        "trace_events": [trace_event_wire(e) for e in bundle.trace_events],
        "canonicalization": bundle.canonicalization,
        "created_at": bundle.created_at,
    }


def b64url_nopad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def sign_bundle(unsigned: Dict[str, Any]) -> tuple[CapabilityTokenSignature, Ed25519PublicKey]:
    """Mint a real ed25519 signature over the JCS canonical form of ``unsigned``.

    The keypair is ephemeral: the private key lives only for this call and is
    never written anywhere, so running the example mints a genuine signature
    without managing secrets.
    """
    private_key = Ed25519PrivateKey.generate()
    canonical = jcs.canonicalize(unsigned)
    raw_sig = private_key.sign(canonical)
    signature = CapabilityTokenSignature(
        alg="ed25519",
        kid="reference-impl-ephemeral",
        sig=b64url_nopad(raw_sig),
        canonicalization="JCS",
        signed_at=unsigned.get("created_at"),
    )
    return signature, private_key.public_key()


def verify_signature(
    unsigned: Dict[str, Any],
    signature: CapabilityTokenSignature,
    public_key: Ed25519PublicKey,
) -> None:
    """Verify the detached signature; raises on failure (cryptography raises
    ``InvalidSignature``)."""
    canonical = jcs.canonicalize(unsigned)
    raw_sig = base64.urlsafe_b64decode(signature.sig + "=" * (-len(signature.sig) % 4))
    public_key.verify(raw_sig, canonical)


def check_invariants(bundle_wire: Dict[str, Any]) -> List[str]:
    """Assert I-01 and I-02 over the bundle wire form."""
    failures: List[str] = []
    for frame in bundle_wire.get("frames", []):
        present = sorted(FORBIDDEN_FRAME_KEYS & set(frame))
        if present:
            failures.append(f"I-01: Frame {frame.get('frame_id')!r} carries raw-output keys {present}")
    traced = {
        e.get("decision_id")
        for e in bundle_wire.get("trace_events", [])
        if e.get("decision_id") is not None
    }
    for pd in bundle_wire.get("policy_decisions", []):
        if pd.get("decision_id") not in traced:
            failures.append(f"I-02: PolicyDecision {pd.get('decision_id')!r} has no matching TraceEvent")
    return failures


def main() -> int:
    print(f"Weaver reference implementation — contract version {CONTRACT_VERSION}\n")
    schemas = load_schemas()
    failures: List[str] = []

    # 1-2. Construct the Core artifacts and gather them into a TraceBundle.
    bundle = build_bundle()
    unsigned_wire = bundle_to_wire(bundle)
    print("[1] Constructed RoutingDecision, CapabilityToken, PolicyDecision, "
          "Frame, Handle, TraceEvent and gathered them into a TraceBundle.")

    # 3. Mint a real ed25519 signature over the JCS canonical bundle.
    signature, public_key = sign_bundle(unsigned_wire)
    signed_wire = dict(unsigned_wire)
    signed_wire["signature"] = signature_wire(signature)
    print(f"[2] Signed the bundle (alg=ed25519, kid={signature.kid!r}).")

    # 4. Verify the signature against the ephemeral public key.
    try:
        verify_signature(unsigned_wire, signature, public_key)
        print("[3] Signature verified against the ephemeral public key.")
    except Exception as exc:  # InvalidSignature or decoding error
        failures.append(f"signature verification failed: {exc}")

    # 5. Validate every Core artifact and the signed bundle against the schemas.
    to_validate = [
        ("routing_decision", routing_decision_wire(bundle.routing_decision)),
        ("policy_decision", policy_decision_wire(bundle.policy_decisions[0])),
        ("frame", frame_wire(bundle.frames[0])),
        ("handle", handle_wire(bundle.handles[0])),
        ("trace_event", trace_event_wire(bundle.trace_events[0])),
        ("trace_bundle", signed_wire),
    ]
    for stem, payload in to_validate:
        errs = schema_errors(payload, schemas.by_stem[stem], schemas.registry)
        if errs:
            failures.extend(f"{stem}: {e}" for e in errs)
    if not any(f for stem, _ in to_validate for f in failures if f.startswith(stem)):
        print(f"[4] Validated {len(to_validate)} payloads against contracts/json/ schemas.")

    # 6. Assert the cross-field invariants.
    inv_failures = check_invariants(signed_wire)
    failures.extend(inv_failures)
    if not inv_failures:
        print("[5] Invariants I-01 (no raw output in Frames) and I-02 "
              "(PolicyDecisions are traced) hold.")

    print()
    if failures:
        print(f"FAILED ({len(failures)}):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("Reference implementation: all checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
