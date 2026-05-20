# Lifecycle Contract

This document defines the canonical five-phase lifecycle that ties the Weaver
contracts together end-to-end: **route → call → interpret → answer → execute**.
Phases 1–4 each have a single owner repo, declared inputs and outputs, and a
non-negotiable safety boundary. Phase 5 is an orchestration phase: ChainWeaver
owns the orchestration (DAG advancement, step sequencing) and delegates each
step's execution back to agent-kernel via Phases 2–3 (invariant I-07). The
"single owner" rule still holds within each delegated sub-phase.

This document is normative for phase ownership and boundary rules. It is
informative for sequencing — implementations may interleave phases (for
example, ChainWeaver may run several `route → call → execute` cycles before
producing a final answer), but they must not violate the per-phase ownership
or boundary rules.

Higher-authority documents:

- [`docs/INVARIANTS.md`](INVARIANTS.md) — non-negotiable rules (I-01..I-07).
- [`docs/BOUNDARIES.md`](BOUNDARIES.md) — artifact ownership.
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — three-layer model.

When this doc conflicts with any of the above, the higher-authority doc wins.

---

## Phases at a glance

| # | Phase | Owner repo | Primary input(s) | Primary output(s) | Boundary it crosses |
| --- | --- | --- | --- | --- | --- |
| 1 | **Route** | contextweaver | conversation state, capability registry | `RoutingDecision` (with `ChoiceCard`s) | contextweaver → caller / agent-kernel |
| 2 | **Call** | agent-kernel | `RoutingDecision`, `CapabilityToken` | `PolicyDecision`, validated invocation | caller / contextweaver → agent-kernel |
| 3 | **Interpret** | agent-kernel (firewall) | raw tool output (internal only) | `Frame` (+ optional `Handle`) | internal to agent-kernel |
| 4 | **Answer** | contextweaver (or caller) | `Frame` | enriched LLM context / final reply | agent-kernel → contextweaver → LLM/caller |
| 5 | **Execute** | agent-kernel (under ChainWeaver orchestration when present) | `Frame`, next `RoutingDecision`, refreshed `CapabilityToken` | next-step `Frame`, `TraceEvent` chain | ChainWeaver → agent-kernel → audit log |

A `TraceEvent` is appended to the audit log around each authorization and
execution event (Phases 2, 3, and 5) per invariant I-02. Implementations are
free to emit additional `TraceEvent`s at other transitions for richer
audit trails, but only the I-02 events are required to claim spec
compliance.

---

## Phase 1 — Route

The contextweaver layer compiles the current conversation state and picks a
bounded set of options for the LLM to choose between. Routing is pure: it
produces a decision artifact and **does not invoke any tool**.

| Attribute | Value |
| --- | --- |
| **Owner repo** | `contextweaver` |
| **Input** | conversation history, candidate capability registry |
| **Output** | [`RoutingDecision`](../contracts/json/routing_decision.schema.json) containing one or more [`ChoiceCard`](../contracts/json/choice_card.schema.json) objects |
| **Boundary** | contextweaver → (caller \| agent-kernel) |
| **Invariants enforced** | **I-03** (no full-schema injection), **I-05** (contextweaver consumes only `Frame`s on subsequent cycles) |
| **Sample payload** | [`routing_decision.json`](../examples/sample_payloads/routing_decision.json) |

**Must not** call any tool, materialize a `Frame`, or issue a
`CapabilityToken`.

---

## Phase 2 — Call

The selected `SelectableItem` (with its `capability_id`) and a
`CapabilityToken` are presented to agent-kernel. The policy engine returns a
`PolicyDecision`. If `allow`, the tool is invoked; if `deny`, no execution
happens and the caller receives the `PolicyDecision` plus a
`capability_denied` `TraceEvent`.

| Attribute | Value |
| --- | --- |
| **Owner repo** | `agent-kernel` |
| **Input** | `RoutingDecision`, [`CapabilityToken`](../contracts/json/capability_token.schema.json) |
| **Output** | [`PolicyDecision`](../contracts/json/policy_decision.schema.json); on `allow`, a tool invocation |
| **Boundary** | (caller \| contextweaver) → agent-kernel |
| **Invariants enforced** | **I-02** (every execution authorized + audited), **I-06** (tokens scoped + expiring or single-use) |
| **Sample payloads** | [`capability_token.json`](../examples/sample_payloads/capability_token.json), [`policy_decision.json`](../examples/sample_payloads/policy_decision.json) |

**Must not** allow execution before a `PolicyDecision` is recorded. **Must
not** accept tokens lacking scope or both `expires_at` and `single_use`.

---

## Phase 3 — Interpret

The tool produces raw output inside agent-kernel. The firewall transforms it
into a safe `Frame` (summary + optional structured data) and stores any
sensitive or large payload as a `Handle`. **Raw output never leaves the
kernel.** The `Frame` is the only representation that crosses any boundary.

| Attribute | Value |
| --- | --- |
| **Owner repo** | `agent-kernel` (firewall) |
| **Input** | raw tool output (internal only — never serialized to a contract type) |
| **Output** | [`Frame`](../contracts/json/frame.schema.json) and optionally [`Handle`](../contracts/json/handle.schema.json); `firewall_applied` `TraceEvent` |
| **Boundary** | internal to agent-kernel; nothing crosses unfiltered |
| **Invariants enforced** | **I-01** (LLM never sees raw output by default), **I-05** (contextweaver gets `Frame` only) |
| **Sample payloads** | [`frame_with_handles.json`](../examples/sample_payloads/frame_with_handles.json), [`handle.json`](../examples/sample_payloads/handle.json) |

**Must not** emit raw output to any other layer. **Must** record a
`firewall_applied` `TraceEvent` for any output that was redacted or
materialized as a `Handle`.

---

## Phase 4 — Answer

contextweaver (or the caller, if contextweaver is not adopted) folds the
`Frame` back into the conversation context for the next LLM turn or as the
final reply to the caller. If the conversation continues, the cycle returns
to Phase 1 with the updated context.

| Attribute | Value |
| --- | --- |
| **Owner repo** | `contextweaver` (or caller, in partial-adoption stacks) |
| **Input** | `Frame` (and optionally referenced `Handle` IDs) |
| **Output** | enriched LLM context, or final reply to the original caller |
| **Boundary** | agent-kernel → contextweaver → LLM/caller |
| **Invariants enforced** | **I-01** / **I-05** (no raw output ingestion), **I-04** (no implementation-specific fields fan out) |
| **Sample payload** | [`frame_with_handles.json`](../examples/sample_payloads/frame_with_handles.json) |

**Must not** dereference a `Handle` and inline its contents without going
back through agent-kernel for authorization.

---

## Phase 5 — Execute (multi-step orchestration)

When a flow needs multiple tool invocations, ChainWeaver advances the cursor
through its DAG. Each step is a delegated `Call → Interpret` cycle against
agent-kernel; ChainWeaver never executes tools directly.

| Attribute | Value |
| --- | --- |
| **Owner repo** | `ChainWeaver` (orchestration) + `agent-kernel` (execution) |
| **Input** | current `Frame`, next step's `RoutingDecision`, fresh or replayed `CapabilityToken` |
| **Output** | next-step `Frame`; chained `TraceEvent`s (`flow_step_started`, `flow_step_completed`, `flow_completed` \| `flow_failed`) |
| **Boundary** | ChainWeaver → agent-kernel → audit log |
| **Invariants enforced** | **I-02** (every step audited), **I-07** (ChainWeaver delegates execution to the kernel) |
| **Sample payloads** | [`trace_event.json`](../examples/sample_payloads/trace_event.json), plus the multi-step walkthrough in [`examples/multi_agent_orchestration.md`](../examples/multi_agent_orchestration.md) |

**Must not** invoke tools without going through agent-kernel's `Call` phase.
**Must** emit a `flow_step_started` and `flow_step_completed` `TraceEvent`
per step.

---

## Ambiguous cases (informative)

These cases are not yet pinned down by any higher-authority document. The
recommendations below are conservative defaults — change them only via ADR.

### Pre-route context compilation

Context compilation that happens **before** Phase 1 (e.g. retrieval to
shrink the candidate capability set) is treated as part of contextweaver's
internal routing pipeline, not as a separate phase. It produces no Weaver
contract artifacts and crosses no contract boundary.

### Post-execute summarization

If an implementation summarizes a `Frame` further before showing it to the
LLM, the summarization happens inside contextweaver during **Phase 4
(Answer)**. The original `Frame` remains the authoritative artifact in
the audit log; the summarized form is a UI / prompt-construction concern
that does not produce a new contract object.

### Deterministic multi-step flows without routing

A ChainWeaver step that invokes a single, pinned capability (no `ChoiceCard`
needed) still produces a `RoutingDecision` for audit and replay symmetry —
the `RoutingDecision` contains a single-item `ChoiceCard` with the pinned
capability and `selected_item_id` already set. Skipping the
`RoutingDecision` would break invariant I-02's audit chain.

### Reading a `Handle`

Resolving a `Handle` is a separate `Call → Interpret` cycle against
agent-kernel: it produces a `handle_resolved` `TraceEvent` and a new
`Frame`. The `Handle` itself never crosses the firewall as a raw artifact.

---

## See also

- [`docs/SEQUENCE_DIAGRAMS.md`](SEQUENCE_DIAGRAMS.md) — Mermaid diagrams of
  the happy path and three failure paths.
- [`docs/INTEGRATION_MAP.md`](INTEGRATION_MAP.md) — concrete inter-repo
  handoffs with JSON payloads at each boundary.
- [`examples/minimal_e2e_sequence.md`](../examples/minimal_e2e_sequence.md)
  — annotated single-turn walkthrough.
- [`examples/multi_agent_orchestration.md`](../examples/multi_agent_orchestration.md)
  — two-agent ChainWeaver-coordinated walkthrough.
- [`examples/failure_scenarios.md`](../examples/failure_scenarios.md) —
  Phase 1 / Phase 2 / Phase 3 failure walkthroughs.
- [`examples/interoperability/`](../examples/interoperability/) — minimal
  happy-path and denied-path examples linking the contracts.
