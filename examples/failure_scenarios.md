# Failure Scenarios Walkthrough

This example traces three failure paths through the Weaver stack: routing failure (no matching capabilities), authorization denial (`CapabilityToken` rejected by the policy engine), and partial execution failure (tool errors mid-stream). Each scenario shows the contract payloads produced at every boundary so adopters can build error-tolerant integrations.

The happy path is covered in [`minimal_e2e_sequence.md`](minimal_e2e_sequence.md). The Mermaid diagrams for the same three scenarios are in [`docs/SEQUENCE_DIAGRAMS.md`](../docs/SEQUENCE_DIAGRAMS.md) sections 4 — 6.

---

## Scenarios

| Scenario | Where it fails | Caller receives | Primary invariants exercised |
| ---------- | ---------------- | ----------------- | ------------------------------ |
| 1. Routing failure | contextweaver — no capability matches the request | `RoutingDecision` with a fallback `ChoiceCard` and a `context_summary` explaining the miss | I-03 |
| 2. Authorization denial | agent-kernel — policy engine rejects the `CapabilityToken` | `PolicyDecision` with `decision = "deny"` and a `TraceEvent` of type `capability_denied` | I-02, I-06 |
| 3. Partial execution failure | agent-kernel — tool starts but errors before producing a usable artifact | `Frame` with an error summary, empty `handle_refs`, and a `TraceEvent` with `outcome = "failure"` | I-01, I-02, I-05 |

Inline payload conventions: every JSON block is preceded by a `<!-- schema: <name> -->` marker that names the schema it validates against. CI extracts these blocks and validates them against `contracts/json/<name>.schema.json`.

---

## Scenario 1: Routing failure (no matching capabilities)

### Setup

A caller submits a request whose intent does not overlap any capability registered in the agent's tool inventory.

- **User request:** "Calculate my company's tax liability for Q3."
- **Registered capabilities (excerpt):** `org.myapp.search_docs`, `org.myapp.fetch_doc_page`, `org.myapp.list_recent_docs`. None of them perform tax calculations or numeric reasoning.

### Step 1: contextweaver evaluates the request

contextweaver scores every registered capability against the request intent. None of them clear the minimum match threshold.

Rather than emit an empty payload (the schema requires `choice_cards` with `minItems: 1` and each `ChoiceCard` requires `items` with `minItems: 1`), contextweaver emits a fallback `ChoiceCard` carrying a single sentinel `SelectableItem`. The fallback item has no `capability_id`, so the caller can detect it programmatically.

### Step 2: RoutingDecision emitted

<!-- schema: routing_decision -->
```json
{
  "id": "rd-20260513-fail-001",
  "choice_cards": [
    {
      "id": "card-no-match",
      "context_hint": "No registered capability matches the request. Surface the fallback to the caller for clarification or escalation.",
      "items": [
        {
          "id": "no-match",
          "label": "No matching capability",
          "description": "No registered capability can satisfy this request. Ask the caller to rephrase or escalate to a human reviewer."
        }
      ]
    }
  ],
  "selected_item_id": "no-match",
  "selected_card_id": "card-no-match",
  "timestamp": "2026-05-13T09:14:22Z",
  "context_summary": "0 of 247 registered capabilities scored above the match threshold for request: 'Calculate my company's tax liability for Q3'. Returning fallback ChoiceCard."
}
```

### Step 3: Caller receives the RoutingDecision

The caller inspects `selected_item_id`. The literal value `"no-match"` (or absence of `capability_id` on the resolved item) is the documented signal that no execution will occur.

Because contextweaver does not execute capabilities (per [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md) — "Routing does not execute"), agent-kernel is never invoked, no `PolicyDecision` is produced, and no `TraceEvent` is appended for this turn. The caller decides how to surface the miss — typically a clarification prompt back to the user.

---

## Scenario 2: Authorization denial (CapabilityToken rejected)

### Setup

Routing succeeds and selects a real capability, but the caller's `CapabilityToken` does not authorize that capability. The denial happens inside agent-kernel's policy engine.

- **User request:** "Delete the production retry-policy document."
- **Selected capability:** `org.myapp.delete_doc_page`.
- **Token scope:** the caller's session token authorizes `org.myapp.search_docs`, `org.myapp.fetch_doc_page`, and `org.myapp.list_recent_docs` — but **not** `org.myapp.delete_doc_page`.

### Step 1: RoutingDecision produced (succeeds)

contextweaver returns a normal `RoutingDecision`. Routing has no visibility into authorization; the scope mismatch is detected one layer later by agent-kernel.

### Step 2: CapabilityToken presented to agent-kernel

<!-- schema: capability_token -->
```json
{
  "token_id": "tok-20260513-readonly-42",
  "principal": "agent-session-7f3a",
  "scope": [
    "org.myapp.search_docs",
    "org.myapp.fetch_doc_page",
    "org.myapp.list_recent_docs"
  ],
  "issued_at": "2026-05-13T09:00:00Z",
  "expires_at": "2026-05-13T10:00:00Z",
  "single_use": false,
  "issuer": "agent-kernel-prod-1",
  "metadata": {
    "session_id": "sess-20260513-xyz",
    "request_id": "req-20260513-002"
  }
}
```

### Step 3: Policy engine evaluates the request

The policy engine checks the requested `capability_id` against the token scope:

- Is `org.myapp.delete_doc_page` listed in `scope`? **No.**
- Is the token unexpired? Yes (`expires_at` 2026-05-13T10:00:00Z is after `2026-05-13T09:14:30Z`).
- Result: scope mismatch — deny.

### Step 4: PolicyDecision emitted

<!-- schema: policy_decision -->
```json
{
  "decision_id": "pd-20260513-deny-001",
  "decision": "deny",
  "capability_id": "org.myapp.delete_doc_page",
  "principal": "agent-session-7f3a",
  "token_id": "tok-20260513-readonly-42",
  "reason": "Token scope does not include the requested capability. Requested 'org.myapp.delete_doc_page'; scope authorizes only documentation read operations.",
  "timestamp": "2026-05-13T09:14:30Z"
}
```

### Step 5: TraceEvent appended to the audit log

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-deny-001",
  "event_type": "capability_denied",
  "timestamp": "2026-05-13T09:14:30Z",
  "capability_id": "org.myapp.delete_doc_page",
  "principal": "agent-session-7f3a",
  "decision_id": "pd-20260513-deny-001",
  "outcome": "failure",
  "error_message": "Token scope does not include requested capability."
}
```

### Step 6: Caller receives the PolicyDecision

agent-kernel does **not** invoke the tool, does **not** produce a `Frame`, and does **not** generate a `Handle`. The caller receives the `PolicyDecision` (`docs/BOUNDARIES.md` artifact ownership: PolicyDecision may cross from agent-kernel to caller for diagnostics). The denial is fully attributable through `decision_id` ↔ `event_id`.

---

## Scenario 3: Partial execution failure (tool errors mid-stream)

### Setup

Routing and authorization both succeed. Tool invocation begins but fails before producing a usable artifact (a timeout, a network error, or an exception inside the tool implementation).

- **User request:** "Search the docs for 'retry policies'."
- **Selected capability:** `org.myapp.search_docs`.
- **Token:** authorizes `org.myapp.search_docs`, unexpired.
- **Failure mode:** the search index backend times out 8 seconds into the request; the tool wrapper raises `BackendTimeoutError` before any result rows are produced.

### Step 1: PolicyDecision allow (succeeds)

<!-- schema: policy_decision -->
```json
{
  "decision_id": "pd-20260513-allow-077",
  "decision": "allow",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "token_id": "tok-20260513-readonly-42",
  "timestamp": "2026-05-13T09:21:00Z"
}
```

### Step 2: TraceEvent `capability_authorized` appended

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-auth-077",
  "event_type": "capability_authorized",
  "timestamp": "2026-05-13T09:21:00Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "decision_id": "pd-20260513-allow-077",
  "outcome": "success"
}
```

### Step 3: Tool invocation begins and fails

The tool wrapper calls the backend search service. After 8 seconds the backend returns no rows and the wrapper raises `BackendTimeoutError("upstream timeout after 8000ms")`. No raw result document is produced.

### Step 4: Firewall produces an error Frame

Even with no raw artifact to summarize, the firewall must still emit a `Frame` so the caller has an LLM-safe record of what happened. `handle_refs` is empty because no artifact was stored — there is nothing to reference. `structured_data` carries the error envelope (firewall-filtered: only the error class and a sanitized message, not stack traces or backend internals).

<!-- schema: frame -->
```json
{
  "frame_id": "frame-20260513-err-077",
  "capability_id": "org.myapp.search_docs",
  "summary": "Search failed: the documentation backend timed out after 8 seconds. No results were returned. The caller may retry; if the failure persists, escalate to the docs platform team.",
  "structured_data": {
    "status": "error",
    "error_class": "BackendTimeoutError",
    "error_message": "upstream timeout after 8000ms",
    "retriable": true
  },
  "handle_refs": [],
  "redaction_notes": "No raw artifact was produced. Backend hostname, internal request ID, and stack trace were stripped from the error envelope before populating structured_data.",
  "created_at": "2026-05-13T09:21:08Z"
}
```

### Step 5: TraceEvent `capability_executed` with failure outcome

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-exec-077",
  "event_type": "capability_executed",
  "timestamp": "2026-05-13T09:21:08Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "agent-session-7f3a",
  "decision_id": "pd-20260513-allow-077",
  "frame_id": "frame-20260513-err-077",
  "outcome": "failure",
  "error_message": "BackendTimeoutError: upstream timeout after 8000ms"
}
```

### Step 6: Caller receives the error Frame

The caller (or ChainWeaver, when present) receives the `Frame`. Because `handle_refs` is empty, there is nothing to resolve via the `HandleStore`. The `summary` is safe to inject into a subsequent LLM turn; the LLM never sees the raw `BackendTimeoutError` traceback, only the firewall-filtered message.

---

## Invariants Demonstrated

| Scenario | Invariant | How it is satisfied |
| ---------- | ----------- | --------------------- |
| 1 | I-03 — Routing does not require full schema injection | contextweaver decides "no match" using `ChoiceCard` scoring, not by injecting full tool schemas |
| 2 | I-02 — Every execution is authorized and auditable | The denial produces both a `PolicyDecision` (`decision = "deny"`) and a paired `TraceEvent` (`event_type = "capability_denied"`) |
| 2 | I-06 — `CapabilityToken`s are scoped | The token's `scope` array drives the denial; an unscoped token would be rejected at issuance |
| 3 | I-01 — LLM never sees raw tool output by default | The error envelope in `structured_data` is firewall-filtered; the raw `BackendTimeoutError` traceback stays inside agent-kernel |
| 3 | I-02 — Every execution is authorized and auditable | `capability_authorized` (success) and `capability_executed` (failure) `TraceEvent`s are both appended |
| 3 | I-05 — contextweaver receives `Frame`s, not raw output | The caller and any downstream contextweaver ingest only the error `Frame` — never the underlying exception |

---

## Cross-references

- Boundary rules referenced: [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md) — routing does not execute; `PolicyDecision` may cross to caller for diagnostics; raw tool output never leaves agent-kernel.
- Invariants: [`docs/INVARIANTS.md`](../docs/INVARIANTS.md) — I-01, I-02, I-03, I-05, I-06.
- Sequence diagrams for the same three scenarios: [`docs/SEQUENCE_DIAGRAMS.md`](../docs/SEQUENCE_DIAGRAMS.md) sections 4 — 6.
- Happy-path counterpart: [`minimal_e2e_sequence.md`](minimal_e2e_sequence.md).
- Multi-agent orchestration counterpart: [`multi_agent_orchestration.md`](multi_agent_orchestration.md).
