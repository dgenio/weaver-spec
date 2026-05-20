# Cross-Repo Integration Map

This document records the concrete handoff points between Weaver repositories.
Each integration point names the producer, the consumer, the trigger, the
contract that crosses the boundary, the applicable invariants, and an inline
JSON payload snippet.

This is a companion to [`docs/BOUNDARIES.md`](BOUNDARIES.md) (which records
artifact ownership) and [`docs/LIFECYCLE.md`](LIFECYCLE.md) (which records the
phase sequence). When this doc conflicts with either, those win.

Inline JSON convention: every JSON block is preceded by a
`<!-- schema: <name> -->` marker; CI extracts the block and validates it
against `contracts/json/<name>.schema.json`.

---

## Integration Point 1 — contextweaver → agent-kernel (route → call)

| Attribute | Value |
| --- | --- |
| **Producer** | `contextweaver` |
| **Consumer** | `agent-kernel` |
| **Trigger** | LLM selects a `SelectableItem` from a `ChoiceCard`. |
| **Contract crossing** | [`RoutingDecision`](../contracts/json/routing_decision.schema.json) (with `selected_item_id` populated) |
| **Lifecycle phases** | Phase 1 → Phase 2 ([`docs/LIFECYCLE.md`](LIFECYCLE.md)) |
| **BOUNDARIES.md row** | `RoutingDecision` — owned by contextweaver, may cross to agent-kernel. |
| **Invariants** | **I-03** (no full-schema injection on the routing side), **I-04** (`RoutingDecision` carries only the fields needed for the handoff). |
| **Consumer action** | agent-kernel resolves `selected_item_id` to a `capability_id` and proceeds to issue / validate a `CapabilityToken`. |

Payload at the boundary (subset — full sample at
[`examples/sample_payloads/routing_decision.json`](../examples/sample_payloads/routing_decision.json)):

<!-- schema: routing_decision -->
```json
{
  "id": "rd-20260308-001",
  "choice_cards": [
    {
      "id": "card-retrieval",
      "context_hint": "Select the most appropriate document retrieval action for the user's query.",
      "items": [
        {
          "id": "search-docs",
          "label": "Search documentation",
          "description": "Full-text search across the product documentation index.",
          "capability_id": "org.myapp.search_docs"
        }
      ]
    }
  ],
  "selected_item_id": "search-docs",
  "selected_card_id": "card-retrieval",
  "timestamp": "2026-03-08T06:00:00Z",
  "context_summary": "User asked: 'How do I configure retries?'. Routing to documentation retrieval."
}
```

---

## Integration Point 2 — agent-kernel → caller (interpret → answer)

| Attribute | Value |
| --- | --- |
| **Producer** | `agent-kernel` (firewall) |
| **Consumer** | caller (typically via `contextweaver` passthrough) |
| **Trigger** | Tool execution completes; firewall produces a safe summary. |
| **Contracts crossing** | [`Frame`](../contracts/json/frame.schema.json) and (when raw artifacts exist) [`Handle`](../contracts/json/handle.schema.json) |
| **Lifecycle phases** | Phase 3 → Phase 4 ([`docs/LIFECYCLE.md`](LIFECYCLE.md)) |
| **BOUNDARIES.md rows** | `Frame` (owned by agent-kernel, may cross to contextweaver / caller), `Handle` (owned by agent-kernel, crosses to caller only with authorization). |
| **Invariants** | **I-01** (raw tool output must not cross unfiltered), **I-05** (contextweaver receives `Frame` only). |
| **Consumer action** | contextweaver ingests `Frame` into the next-turn context; or the caller renders the summary. `Handle` resolution requires a separate authorized round-trip back through agent-kernel. |

Payload at the boundary (full sample at
[`examples/sample_payloads/frame_with_handles.json`](../examples/sample_payloads/frame_with_handles.json)):

<!-- schema: frame -->
```json
{
  "frame_id": "frame-20260308-001",
  "capability_id": "org.myapp.search_docs",
  "summary": "Found 3 documentation pages matching 'retry configuration': Retry Policies Overview, Configuring Exponential Backoff, Dead Letter Queues. The most relevant is 'Retry Policies Overview'.",
  "structured_data": {
    "result_count": 3,
    "top_result_slug": "docs/retry-policies"
  },
  "handle_refs": ["handle-rawresult-20260308-001"],
  "redaction_notes": "Raw search index response (internal document IDs and ranking signals) stored as Handle. Only titles, slugs, and relevance scores included in structured_data.",
  "created_at": "2026-03-08T06:00:05Z"
}
```

Paired `Handle` reference (raw artifact stays in the HandleStore):

<!-- schema: handle -->
```json
{
  "handle_id": "handle-rawresult-20260308-001",
  "capability_id": "org.myapp.search_docs",
  "artifact_type": "application/json",
  "created_at": "2026-03-08T06:00:05Z",
  "expires_at": "2026-03-09T06:00:05Z",
  "access_policy": "policy://agent-kernel/handle-default",
  "byte_size": 18432
}
```

---

## Integration Point 3 — agent-kernel → audit log (every execution)

| Attribute | Value |
| --- | --- |
| **Producer** | `agent-kernel` |
| **Consumer** | audit log infrastructure (append-only) |
| **Trigger** | Any significant execution event (authorization, firewall application, capability execution, handle creation, token issuance, etc.). |
| **Contract crossing** | [`TraceEvent`](../contracts/json/trace_event.schema.json) |
| **Lifecycle phases** | All phases (a `TraceEvent` is appended at every phase transition). |
| **BOUNDARIES.md row** | `TraceEvent` — owned by agent-kernel, crosses to the audit log. |
| **Invariants** | **I-02** (every execution authorized + auditable). |
| **Consumer action** | Audit log persists the event. The `decision_id`, `frame_id`, and `handle_id` fields chain events into per-request narratives. |

Payload at the boundary (full sample at
[`examples/sample_payloads/trace_event.json`](../examples/sample_payloads/trace_event.json)):

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260308-005",
  "event_type": "capability_executed",
  "timestamp": "2026-03-08T06:00:05Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "decision_id": "pd-20260308-001",
  "frame_id": "frame-20260308-001",
  "handle_id": "handle-rawresult-20260308-001",
  "outcome": "success"
}
```

---

## Integration Point 4 — ChainWeaver → contextweaver (re-routing on a multi-step flow)

| Attribute | Value |
| --- | --- |
| **Producer** | `ChainWeaver` |
| **Consumer** | `contextweaver` |
| **Trigger** | A multi-step flow needs the next agent. ChainWeaver hands the previous step's `Frame` plus the running context back to contextweaver to compile the next `RoutingDecision`. |
| **Contract crossing** | request envelope carrying the previous-step [`Frame`](../contracts/json/frame.schema.json) and the resulting next-step [`RoutingDecision`](../contracts/json/routing_decision.schema.json) |
| **Lifecycle phases** | Phase 4 → Phase 1 (loop) → Phase 2 → Phase 3 → Phase 5 ([`docs/LIFECYCLE.md`](LIFECYCLE.md)) |
| **BOUNDARIES.md rows** | `Frame` (agent-kernel → contextweaver passthrough), `RoutingDecision` (contextweaver → agent-kernel via ChainWeaver). |
| **Invariants** | **I-07** (ChainWeaver delegates execution to the kernel), **I-02** (each step audited). |
| **Consumer action** | contextweaver compiles a fresh `ChoiceCard` based on the previous-step `Frame`'s summary; the LLM (or the deterministic flow) selects the next capability. |

This handoff is illustrated end-to-end in
[`examples/multi_agent_orchestration.md`](../examples/multi_agent_orchestration.md).

`TraceEvent`s emitted at this boundary:

<!-- schema: trace_event -->
```json
{
  "event_id": "te-flow-20260308-007",
  "event_type": "flow_step_completed",
  "timestamp": "2026-03-08T06:00:06Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "outcome": "success"
}
```

---

## Summary

| # | From | To | Contract | Invariants |
| --- | --- | --- | --- | --- |
| 1 | contextweaver | agent-kernel | `RoutingDecision` | I-03, I-04 |
| 2 | agent-kernel | caller / contextweaver | `Frame` (+ optional `Handle`) | I-01, I-05 |
| 3 | agent-kernel | audit log | `TraceEvent` | I-02 |
| 4 | ChainWeaver | contextweaver | `Frame` / `RoutingDecision` | I-02, I-07 |

Every contract crossing in this table is owned by exactly one repo per
[`docs/BOUNDARIES.md`](BOUNDARIES.md). Implementations that surface
additional implementation-specific payloads at these boundaries must do so
via Extended contracts, not Core (invariant I-04).
