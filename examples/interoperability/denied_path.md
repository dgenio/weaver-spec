# Denied Path: Authorization Refused

Counterpart to [`happy_path.md`](happy_path.md). The setup is identical
through Step 1 (Route). At Step 2 (Call) the policy engine **denies** the
request because the presented `CapabilityToken`'s scope does not cover the
target capability. No tool runs. No `Frame` is produced. No `Handle` is
materialized.

Inline payload convention: every JSON block is preceded by a
`<!-- schema: <name> -->` marker. CI extracts and validates each block.

---

## Setup

- **Caller request:** "How do I configure retries?"
- **Owning principal:** `agent-session-7f3a`
- **Capability targeted:** `org.myapp.search_docs`
- **Token presented:** scoped to a different capability
  (`org.myapp.list_recent_docs`).

---

## Step 1 — Route (contextweaver, unchanged)

<!-- schema: routing_decision -->
```json
{
  "id": "rd-denied-001",
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

## Step 2 — Call (agent-kernel: deny)

The caller presents a token whose `scope` covers a sibling capability but
**not** `org.myapp.search_docs`. The schema accepts the token (it is
well-formed and meets invariant I-06: scoped + expiring), but the policy
engine refuses it.

<!-- schema: capability_token -->
```json
{
  "token_id": "tok-denied-001",
  "principal": "agent-session-7f3a",
  "scope": ["org.myapp.list_recent_docs"],
  "issued_at": "2026-03-08T06:00:00Z",
  "expires_at": "2026-03-08T07:00:00Z",
  "single_use": false,
  "issuer": "agent-kernel-prod-1"
}
```

<!-- schema: policy_decision -->
```json
{
  "decision_id": "pd-denied-001",
  "decision": "deny",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "token_id": "tok-denied-001",
  "reason": "Token scope does not include org.myapp.search_docs. Issue a token with the correct scope or route to a capability the existing scope covers.",
  "timestamp": "2026-03-08T06:00:01Z"
}
```

A `capability_denied` `TraceEvent` is appended.

<!-- schema: trace_event -->
```json
{
  "event_id": "te-denied-001",
  "event_type": "capability_denied",
  "timestamp": "2026-03-08T06:00:01Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "decision_id": "pd-denied-001",
  "outcome": "failure",
  "error_message": "Authorization denied: token scope mismatch."
}
```

---

## Step 3 — No execution, no firewall

Because the `PolicyDecision` is `deny`, agent-kernel does not invoke the
tool. No `Frame` is produced. No `Handle` is materialized. No
`capability_executed` or `firewall_applied` events appear in the trace.

The caller receives the `PolicyDecision` and the `capability_denied`
`TraceEvent`. It can:

- request a re-issued `CapabilityToken` with the correct scope and retry,
  or
- route to a different capability the existing token already covers, or
- surface the denial reason to the human user.

---

## What changed vs. the happy path

| Step | Happy path | Denied path |
| --- | --- | --- |
| Step 1 Route — `RoutingDecision` | Same shape; only `id` differs. | Same shape; only `id` differs. |
| Step 2 Call — `CapabilityToken` | Token scope covers the target capability. | Token scope does **not** cover the target capability. |
| Step 2 Call — `PolicyDecision` | `decision: "allow"`. | `decision: "deny"` with a `reason`. |
| Step 2 Call — first `TraceEvent` | `capability_authorized`, `outcome: success`. | `capability_denied`, `outcome: failure`. |
| Step 3 Interpret | Tool runs; `Frame` + `Handle` produced; two more `TraceEvent`s. | Tool does not run; no `Frame`, no `Handle`, no further `TraceEvent`s. |
| Step 4 Answer | Caller receives the `Frame`. | Caller receives the `PolicyDecision` + denied `TraceEvent`. |

## Invariants exercised

| Invariant | Where it's enforced in this walkthrough |
| --- | --- |
| **I-02** (every execution authorized + auditable) | Step 2 — denial is recorded as a `PolicyDecision` and a `capability_denied` `TraceEvent`. |
| **I-06** (tokens scoped + expiring or single-use) | Step 2 — the presented token has explicit `scope` and `expires_at`; it is denied on scope mismatch, not on token shape. |

A richer walkthrough of routing-failure, authorization-denial, and
partial-execution-failure scenarios is in
[`examples/failure_scenarios.md`](../failure_scenarios.md).
