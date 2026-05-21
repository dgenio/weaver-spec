# Happy Path: Single-Turn Tool Use

Minimal end-to-end happy path linking the Core contracts. The user asks a
documentation question; contextweaver routes; agent-kernel authorizes,
executes, firewalls; the caller receives a `Frame` and a `TraceEvent`.

For the same flow with prose narration, see
[`examples/minimal_e2e_sequence.md`](../minimal_e2e_sequence.md). For the
phase model, see [`docs/LIFECYCLE.md`](../../docs/LIFECYCLE.md).

Inline payload convention: every JSON block is preceded by a
`<!-- schema: <name> -->` marker. CI extracts and validates each block.

---

## Setup

- **Caller request:** "How do I configure retries?"
- **Owning principal:** `agent-session-7f3a`
- **Capability targeted:** `org.myapp.search_docs`

---

## Step 1 — Route (contextweaver)

contextweaver compiles a bounded `ChoiceCard` and the LLM selects
`search-docs`. No tool runs yet.

<!-- schema: routing_decision -->
```json
{
  "id": "rd-happy-001",
  "choice_cards": [
    {
      "id": "card-retrieval",
      "context_hint": "Select the most appropriate documentation retrieval action.",
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
  "context_summary": "Route user's retry-configuration question to documentation search."
}
```

---

## Step 2 — Call (agent-kernel: token + policy)

The caller presents a scoped `CapabilityToken` to agent-kernel.

<!-- schema: capability_token -->
```json
{
  "token_id": "tok-happy-001",
  "principal": "agent-session-7f3a",
  "scope": ["org.myapp.search_docs"],
  "issued_at": "2026-03-08T06:00:00Z",
  "expires_at": "2026-03-08T07:00:00Z",
  "single_use": false,
  "issuer": "agent-kernel-prod-1"
}
```

The policy engine evaluates scope, expiry, and principal allowlist, then
returns an allow verdict.

<!-- schema: policy_decision -->
```json
{
  "decision_id": "pd-happy-001",
  "decision": "allow",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "token_id": "tok-happy-001",
  "reason": "Token scope includes target capability; token unexpired; principal allowed.",
  "timestamp": "2026-03-08T06:00:01Z"
}
```

A `capability_authorized` `TraceEvent` is appended to the audit log.

<!-- schema: trace_event -->
```json
{
  "event_id": "te-happy-001",
  "event_type": "capability_authorized",
  "timestamp": "2026-03-08T06:00:01Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "decision_id": "pd-happy-001",
  "outcome": "success"
}
```

---

## Step 3 — Interpret (agent-kernel firewall)

The tool runs inside agent-kernel. Raw output is processed by the firewall:
sensitive fields are stripped, the raw response is parked as a `Handle`, and
a safe `Frame` is emitted. **The raw response never leaves agent-kernel.**

<!-- schema: handle -->
```json
{
  "handle_id": "handle-happy-001",
  "capability_id": "org.myapp.search_docs",
  "artifact_type": "application/json",
  "created_at": "2026-03-08T06:00:05Z",
  "expires_at": "2026-03-09T06:00:05Z",
  "access_policy": "policy://agent-kernel/handle-default",
  "byte_size": 18432
}
```

<!-- schema: frame -->
```json
{
  "frame_id": "frame-happy-001",
  "capability_id": "org.myapp.search_docs",
  "summary": "Found 3 documentation pages matching 'retry configuration'. Most relevant: 'Retry Policies Overview' (docs/retry-policies).",
  "structured_data": {
    "result_count": 3,
    "top_result_slug": "docs/retry-policies"
  },
  "handle_refs": ["handle-happy-001"],
  "redaction_notes": "Raw search index response (internal document IDs and ranking signals) parked as Handle. Only titles, slugs, and relevance scores included in structured_data.",
  "created_at": "2026-03-08T06:00:05Z"
}
```

A `firewall_applied` `TraceEvent` records the redaction.

<!-- schema: trace_event -->
```json
{
  "event_id": "te-happy-002",
  "event_type": "firewall_applied",
  "timestamp": "2026-03-08T06:00:05Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "frame_id": "frame-happy-001",
  "handle_id": "handle-happy-001",
  "outcome": "success"
}
```

A `capability_executed` `TraceEvent` closes the call.

<!-- schema: trace_event -->
```json
{
  "event_id": "te-happy-003",
  "event_type": "capability_executed",
  "timestamp": "2026-03-08T06:00:05Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "decision_id": "pd-happy-001",
  "frame_id": "frame-happy-001",
  "handle_id": "handle-happy-001",
  "outcome": "success"
}
```

---

## Step 4 — Answer (contextweaver / caller)

contextweaver receives the `Frame` (never the `Handle`'s contents, never
the raw output) and folds it into the next-turn context, or returns it as
the final reply.

The `Handle` reference remains available for an authorized follow-up
resolution if the caller needs deeper detail (a separate `Call → Interpret`
cycle, producing a `handle_resolved` `TraceEvent`).

---

## Invariants exercised

| Invariant | Where it's enforced in this walkthrough |
| --- | --- |
| **I-01** / **I-05** (LLM never sees raw tool output; contextweaver consumes only `Frame`) | Step 3 — raw output is parked as a `Handle`; `Frame.summary` carries only safe content. |
| **I-02** (every execution authorized + auditable) | Steps 2 and 3 — `PolicyDecision` + three `TraceEvent`s (`capability_authorized`, `firewall_applied`, `capability_executed`). |
| **I-03** (no full-schema injection) | Step 1 — `ChoiceCard` carries only label / description / `capability_id`, not the tool's full input schema. |
| **I-04** (Core contracts minimal) | Throughout — only fields declared in the Core schemas appear. |
| **I-06** (tokens scoped + expiring) | Step 2 — `scope` is non-empty and `expires_at` is set. |

## Compare with the denied path

See [`denied_path.md`](denied_path.md) — same Steps 1 and 2 setup; Step 2
produces `decision: "deny"`; Steps 3 and 4 do not run.
