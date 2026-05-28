# Selection ↔ Execution Boundary

This page defines the implementation-neutral contracts for the boundary between
*selecting* a unit of work and *executing* it: `ExecutionCandidate`,
`ExecutionRoutingDecision`, `ExecutionFeedback`, and the `CompiledFlow` detail.
All four are **Extended** contracts (optional; not required for spec
compliance). Their JSON Schemas live under
[`contracts/json/extended/`](../contracts/json/extended/) and their Python
mirrors in [`weaver_contracts.extended`](../contracts/python/src/weaver_contracts/extended.py).

> [!NOTE]
> These contracts exist so that a static router, the `contextweaver` ChoiceCard
> layer, and a learned/feedback-aware external router can all describe a
> selection the same way, instead of each integration inventing its own
> router-to-executor payload. They were motivated by the ChainWeaver routing
> discussion but are deliberately generic (issues #61 and #66).

---

## Why a separate `ExecutionRoutingDecision`

The Core [`RoutingDecision`](../contracts/json/routing_decision.schema.json) is
the `contextweaver` artifact that wraps one or more `ChoiceCard`s with selection
state. It is intentionally kept separate from the generic decision type defined
here — see the "Design decisions not to reopen" table in
[`AGENTS.md`](../AGENTS.md). To avoid conflating the two, the generic,
runtime-neutral decision is named **`ExecutionRoutingDecision`**.

---

## The contracts

### `ExecutionCandidate`

Something that can be selected for execution. `candidate_type` is a fixed enum:
`tool`, `flow`, `capability`, `agent`, `workflow`. A runtime is not required to
support every kind. When `candidate_type` is `flow`, the candidate may carry a
`compiled_flow` detail.

### `CompiledFlow`

A compiled flow (e.g. a ChainWeaver flow) exposed as an item that can be routed
to and executed like a capability. It **references** (does not inline) its
input/output schemas, lists the capability IDs it depends on internally
(`tool_dependencies`), and carries `sensitivity` and `side_effects` metadata
typically derived from those tools.

> [!IMPORTANT]
> A `CompiledFlow` being pre-compiled does not bypass execution authorization. A
> flow step that invokes a tool MUST still delegate to the execution layer's
> authorization and audit path (invariant
> [I-07](INVARIANTS.md#i-07-chainweaver-delegates-execution-to-the-kernel)).
> `requires_authorization` defaults to `true`.

### `ExecutionRoutingDecision`

A router's recommendation of an `ExecutionCandidate`, with optional
`confidence` (standardized to `[0.0, 1.0]`), machine-readable `reason_codes`,
ordered `fallback_candidates`, router-side `constraints`, and references for
policy context and tracing. `decision_id` correlates the decision with
downstream execution traces and feedback.

> [!IMPORTANT]
> An `ExecutionRoutingDecision` is **advisory**. It MUST NOT be treated as a
> grant of execution rights. Before the selected candidate runs, the
> execution/policy layer (agent-kernel or another Weaver-compatible runtime)
> still validates a `CapabilityToken`, records a `PolicyDecision`, and emits a
> `TraceEvent` (invariant
> [I-02](INVARIANTS.md#i-02-every-execution-is-authorized-and-auditable)).
> `policy_context_ref` is a reference the router considered, not an
> authorization.

### `ExecutionFeedback`

The observed outcome of executing (or attempting to execute) the selected
candidate. It links back via `decision_id` and `candidate_id`, carries
`success`, optional `latency_ms`, `cost`, `quality_score` (also `[0.0, 1.0]`),
error fields, and a `trace_ref` that preserves the execution runtime's trace
identifier for end-to-end correlation.

> [!NOTE]
> Sending feedback is optional. A deterministic router need not consume it;
> `contextweaver` stays deterministic by default and may ignore feedback. A
> feedback-aware external router can use it to score future decisions.

---

## Example: `contextweaver` → ChainWeaver flow selection

**Example:** a routing decision selecting a compiled ChainWeaver flow. See
[`examples/sample_payloads/execution_routing_decision.json`](../examples/sample_payloads/execution_routing_decision.json).

```json
{
  "decision_id": "dec_123",
  "candidate": {
    "candidate_id": "invoice_reminder_flow",
    "candidate_type": "flow",
    "version": "1.2.0",
    "compiled_flow": {
      "flow_id": "invoice_reminder_flow",
      "version": "1.2.0",
      "tool_dependencies": [
        "org.billing.list_unpaid_invoices",
        "org.email.send_reminder"
      ],
      "sensitivity": "confidential",
      "side_effects": ["external_email", "data_read"],
      "requires_authorization": true
    }
  },
  "confidence": 0.86,
  "reason_codes": ["capability_match", "low_latency", "historical_success"]
}
```

---

## Example: external router → ChainWeaver → feedback

The contracts support this pattern without making the external router a
ChainWeaver dependency:

```text
user task
  → external router produces an ExecutionRoutingDecision
  → host application validates policy/auth (PolicyDecision + TraceEvent)
  → ChainWeaver resolves the selected flow
  → ChainWeaver executes the deterministic flow
  → the execution trace is converted into ExecutionFeedback
  → feedback is sent back to the router or stored for evaluation
```

**Example:** feedback preserving the ChainWeaver trace id. See
[`examples/sample_payloads/execution_feedback.json`](../examples/sample_payloads/execution_feedback.json).

```json
{
  "decision_id": "dec_123",
  "candidate_id": "invoice_reminder_flow",
  "success": true,
  "timestamp": "2026-05-25T08:00:00Z",
  "latency_ms": 842,
  "quality_score": 0.9,
  "trace_ref": "chainweaver:trace_id:abc123"
}
```

---

## Non-goals

These contracts do not define a routing algorithm, do not require learned
routing or an online decision service, do not make ChainWeaver depend on any
router, do not make `contextweaver` depend on feedback by default, and do not
let a routing decision bypass authorization, policy, or audit layers.

---

## Related

- [docs/INVARIANTS.md](INVARIANTS.md) — I-02 (authorized + auditable execution),
  I-07 (ChainWeaver delegates execution).
- [docs/BOUNDARIES.md](BOUNDARIES.md) — responsibility boundaries and artifact
  ownership across the routing and execution layers.
- [docs/ARTIFACT_CONTRACTS.md](ARTIFACT_CONTRACTS.md) — the broader Extended
  artifact vocabulary.
