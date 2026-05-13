# Multi-Agent ChainWeaver Orchestration

This example traces a two-agent flow coordinated by ChainWeaver: a research agent gathers context, then a code-generation agent uses that context to produce a config snippet. The walkthrough shows the full contract lifecycle across both turns — `RoutingDecision` → `PolicyDecision` → `Frame` + `Handle` + `TraceEvent` → re-routing on the second cycle.

The single-agent happy path is in [`minimal_e2e_sequence.md`](minimal_e2e_sequence.md). Failure paths (auth denial, partial execution) are in [`failure_scenarios.md`](failure_scenarios.md).

---

## Scenario

**User request:** "Find the recommended retry configuration in our docs and generate a `config.yaml` snippet for it."

**Two-step decomposition (decided by ChainWeaver):**

1. **Research step** — invoke the research agent to find the recommended retry policy in the documentation.
2. **Code-generation step** — invoke the code-generation agent with the research `Frame` as context, producing the requested config snippet.

**Why ChainWeaver and not a single agent:** the research and code-generation capabilities live in different agents with different `CapabilityToken` scopes. ChainWeaver mediates the handoff without ever touching raw tool output (per invariant I-07).

---

## Layer ownership for this flow

| Step | Layer that owns it | Boundary crossing |
| ------ | -------------------- | ------------------- |
| Decompose request into steps | ChainWeaver | n/a (internal) |
| Route step 1 to a capability | contextweaver | ChainWeaver → contextweaver |
| Authorize + execute step 1 | agent-kernel | ChainWeaver → agent-kernel |
| Firewall step 1 output | agent-kernel | internal to kernel |
| Pass `Frame` to step 2 routing | ChainWeaver | agent-kernel → ChainWeaver → contextweaver |
| Authorize + execute step 2 | agent-kernel | ChainWeaver → agent-kernel |
| Aggregate final response | ChainWeaver | ChainWeaver → caller |

Every "raw output" arrow stays strictly inside agent-kernel — this is the firewall guarantee from [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md).

Inline payload conventions: every JSON block is preceded by a `<!-- schema: <name> -->` marker that names the schema it validates against. CI extracts these blocks and validates them against `contracts/json/<name>.schema.json`.

---

## Step 1: ChainWeaver decomposes the request

ChainWeaver receives the caller's request and decides it needs two sequential capability invocations. It assembles the flow state, then asks contextweaver to route the first step.

ChainWeaver does **not** call tools or inspect raw output. Its only responsibilities at this point are step sequencing and forwarding `Frame` objects between steps (per invariant I-07).

---

## Step 2: contextweaver routes the research step

contextweaver receives the conversation state plus the candidate capabilities relevant to the research intent ("find recommended retry configuration in docs"). It selects three retrieval-flavored capabilities and emits a `RoutingDecision`.

<!-- schema: routing_decision -->
```json
{
  "id": "rd-20260513-step1-001",
  "choice_cards": [
    {
      "id": "card-research",
      "context_hint": "Select the documentation retrieval capability that best answers: 'recommended retry configuration'.",
      "items": [
        {
          "id": "search-docs",
          "label": "Search documentation",
          "description": "Full-text search across the product documentation index.",
          "capability_id": "org.myapp.search_docs"
        },
        {
          "id": "fetch-page",
          "label": "Fetch a known documentation page",
          "description": "Retrieve a specific documentation page by slug.",
          "capability_id": "org.myapp.fetch_doc_page"
        },
        {
          "id": "list-recent",
          "label": "List recently updated docs",
          "description": "Retrieve the 10 most recently modified documentation articles.",
          "capability_id": "org.myapp.list_recent_docs"
        }
      ]
    }
  ],
  "selected_item_id": "search-docs",
  "selected_card_id": "card-research",
  "timestamp": "2026-05-13T11:02:00Z",
  "context_summary": "ChainWeaver flow flow-20260513-001, step 1 of 2 (research). Routed to documentation search."
}
```

ChainWeaver receives this `RoutingDecision` and forwards it (with the appropriate `CapabilityToken`) to agent-kernel.

---

## Step 3: agent-kernel authorizes and executes the research step

agent-kernel validates the `CapabilityToken` for the research scope, authorizes the capability, and invokes the search tool. The firewall produces a `Frame` summarizing the result, plus a `Handle` for the raw search response.

### CapabilityToken used

<!-- schema: capability_token -->
```json
{
  "token_id": "tok-20260513-research-step1",
  "principal": "chainweaver-flow-20260513-001",
  "scope": [
    "org.myapp.search_docs",
    "org.myapp.fetch_doc_page",
    "org.myapp.list_recent_docs"
  ],
  "issued_at": "2026-05-13T11:02:00Z",
  "expires_at": "2026-05-13T11:07:00Z",
  "single_use": true,
  "issuer": "agent-kernel-prod-1",
  "metadata": {
    "flow_id": "flow-20260513-001",
    "step_index": 1
  }
}
```

### PolicyDecision (allow)

<!-- schema: policy_decision -->
```json
{
  "decision_id": "pd-20260513-step1-allow",
  "decision": "allow",
  "capability_id": "org.myapp.search_docs",
  "principal": "chainweaver-flow-20260513-001",
  "token_id": "tok-20260513-research-step1",
  "timestamp": "2026-05-13T11:02:01Z"
}
```

### Frame produced (research result, firewall-filtered)

<!-- schema: frame -->
```json
{
  "frame_id": "frame-20260513-step1-001",
  "capability_id": "org.myapp.search_docs",
  "summary": "Found the canonical retry-policy guidance in 'Retry Policies Overview'. Recommended values: max_attempts=5, initial_backoff_ms=200, multiplier=2.0, max_backoff_ms=5000, jitter=true. The recommendation is enforced via the retry_policy block in job-level config.",
  "structured_data": {
    "top_result": {
      "title": "Retry Policies Overview",
      "slug": "docs/retry-policies",
      "relevance_score": 0.96
    },
    "recommended_values": {
      "max_attempts": 5,
      "initial_backoff_ms": 200,
      "multiplier": 2.0,
      "max_backoff_ms": 5000,
      "jitter": true
    }
  },
  "handle_refs": ["handle-20260513-step1-raw"],
  "redaction_notes": "Raw search response (internal document IDs, ranking signals, shard metadata) stored as Handle. Only the top result's title, slug, score, and the extracted recommended values are exposed.",
  "created_at": "2026-05-13T11:02:02Z"
}
```

### Handle for the raw research artifact

<!-- schema: handle -->
```json
{
  "handle_id": "handle-20260513-step1-raw",
  "capability_id": "org.myapp.search_docs",
  "artifact_type": "application/json",
  "created_at": "2026-05-13T11:02:02Z",
  "expires_at": "2026-05-13T12:02:02Z",
  "access_policy": "policy.researcher.session-scoped",
  "byte_size": 184320
}
```

### TraceEvents appended

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-step1-auth",
  "event_type": "capability_authorized",
  "timestamp": "2026-05-13T11:02:01Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "chainweaver-flow-20260513-001",
  "decision_id": "pd-20260513-step1-allow",
  "outcome": "success"
}
```

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-step1-exec",
  "event_type": "capability_executed",
  "timestamp": "2026-05-13T11:02:02Z",
  "capability_id": "org.myapp.search_docs",
  "principal": "chainweaver-flow-20260513-001",
  "decision_id": "pd-20260513-step1-allow",
  "frame_id": "frame-20260513-step1-001",
  "handle_id": "handle-20260513-step1-raw",
  "outcome": "success"
}
```

agent-kernel returns the `Frame` to ChainWeaver. The `Handle` reference is included; the raw artifact remains in the kernel-controlled `HandleStore`.

---

## Step 4: ChainWeaver hands the research Frame to step 2 routing

ChainWeaver receives the step 1 `Frame`. It does not inspect the underlying raw response (it has no access to the `Handle`'s contents without authorization). It folds the `Frame.summary` and the relevant `structured_data` slice into the conversation state for step 2.

ChainWeaver then asks contextweaver to route step 2, with the step 1 `Frame` available as context.

---

## Step 5: contextweaver routes the code-generation step

contextweaver scores code-generation capabilities against the new intent ("produce a `config.yaml` snippet for these retry values"). It emits a new `RoutingDecision`.

<!-- schema: routing_decision -->
```json
{
  "id": "rd-20260513-step2-002",
  "choice_cards": [
    {
      "id": "card-codegen",
      "context_hint": "Select the code-generation capability that produces a YAML snippet for the retry values extracted in step 1.",
      "items": [
        {
          "id": "gen-yaml",
          "label": "Generate YAML config snippet",
          "description": "Render a YAML snippet from a structured key-value map.",
          "capability_id": "org.myapp.gen_yaml_snippet"
        },
        {
          "id": "gen-json",
          "label": "Generate JSON config snippet",
          "description": "Render a JSON snippet from a structured key-value map.",
          "capability_id": "org.myapp.gen_json_snippet"
        }
      ]
    }
  ],
  "selected_item_id": "gen-yaml",
  "selected_card_id": "card-codegen",
  "timestamp": "2026-05-13T11:02:03Z",
  "context_summary": "ChainWeaver flow flow-20260513-001, step 2 of 2 (codegen). Input: structured_data.recommended_values from frame-20260513-step1-001. Selected YAML output per caller's original phrasing ('config.yaml')."
}
```

---

## Step 6: agent-kernel authorizes and executes the code-generation step

A fresh `CapabilityToken` is issued for the code-generation scope. Each flow step gets its own token — re-using the research token would either fail the scope check or violate I-06 (`single_use: true` on the prior token already invalidated it).

### CapabilityToken used (step 2)

<!-- schema: capability_token -->
```json
{
  "token_id": "tok-20260513-codegen-step2",
  "principal": "chainweaver-flow-20260513-001",
  "scope": [
    "org.myapp.gen_yaml_snippet",
    "org.myapp.gen_json_snippet"
  ],
  "issued_at": "2026-05-13T11:02:03Z",
  "expires_at": "2026-05-13T11:07:03Z",
  "single_use": true,
  "issuer": "agent-kernel-prod-1",
  "metadata": {
    "flow_id": "flow-20260513-001",
    "step_index": 2,
    "prior_frame_id": "frame-20260513-step1-001"
  }
}
```

### PolicyDecision (allow)

<!-- schema: policy_decision -->
```json
{
  "decision_id": "pd-20260513-step2-allow",
  "decision": "allow",
  "capability_id": "org.myapp.gen_yaml_snippet",
  "principal": "chainweaver-flow-20260513-001",
  "token_id": "tok-20260513-codegen-step2",
  "timestamp": "2026-05-13T11:02:04Z"
}
```

### Frame produced (final code snippet)

<!-- schema: frame -->
```json
{
  "frame_id": "frame-20260513-step2-002",
  "capability_id": "org.myapp.gen_yaml_snippet",
  "summary": "Generated a 7-line YAML snippet for the retry policy block. The snippet follows the schema documented in docs/retry-policies and is ready to paste into a job-level config.",
  "structured_data": {
    "language": "yaml",
    "snippet": "retry_policy:\n  max_attempts: 5\n  initial_backoff_ms: 200\n  multiplier: 2.0\n  max_backoff_ms: 5000\n  jitter: true\n",
    "byte_size": 132
  },
  "handle_refs": [],
  "redaction_notes": "Output is a pure transformation of structured_data from frame-20260513-step1-001 plus a static template. No external artifact retained; no Handle produced.",
  "created_at": "2026-05-13T11:02:04Z"
}
```

### TraceEvents appended

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-step2-auth",
  "event_type": "capability_authorized",
  "timestamp": "2026-05-13T11:02:04Z",
  "capability_id": "org.myapp.gen_yaml_snippet",
  "principal": "chainweaver-flow-20260513-001",
  "decision_id": "pd-20260513-step2-allow",
  "outcome": "success"
}
```

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-step2-exec",
  "event_type": "capability_executed",
  "timestamp": "2026-05-13T11:02:04Z",
  "capability_id": "org.myapp.gen_yaml_snippet",
  "principal": "chainweaver-flow-20260513-001",
  "decision_id": "pd-20260513-step2-allow",
  "frame_id": "frame-20260513-step2-002",
  "outcome": "success"
}
```

---

## Step 7: ChainWeaver aggregates the final response

ChainWeaver has both step `Frame`s. It assembles a final response that surfaces the code snippet (step 2) plus a one-line provenance note pointing at the research source (step 1's `summary`). Optionally, the aggregated payload is emitted as a flow-completion `TraceEvent`:

<!-- schema: trace_event -->
```json
{
  "event_id": "te-20260513-flow-complete",
  "event_type": "flow_completed",
  "timestamp": "2026-05-13T11:02:05Z",
  "principal": "chainweaver-flow-20260513-001",
  "outcome": "success",
  "metadata": {
    "flow_id": "flow-20260513-001",
    "step_count": 2,
    "frame_ids": ["frame-20260513-step1-001", "frame-20260513-step2-002"]
  }
}
```

The caller receives the aggregated result. The LLM that drives the next conversation turn sees only the two `Frame.summary` strings and the structured snippet — never any raw search index payload, ranking signal, or backend metadata.

---

## Invariants Demonstrated

| Invariant | How it is satisfied in this flow |
| ----------- | ----------------------------------- |
| I-01 — LLM never sees raw tool output | The step 1 raw search response is held only in the `Handle`-referenced store; the LLM sees only the firewall-filtered `Frame` |
| I-02 — Every execution is authorized and auditable | Each step produces a paired `PolicyDecision` + `TraceEvent`; the flow ends with a `flow_completed` event |
| I-03 — Routing without full schema injection | Each `ChoiceCard` carries 2 – 3 items; no full tool schemas are injected into the LLM prompt for either step |
| I-05 — contextweaver receives Frames, not raw output | The step 2 routing input is the step 1 `Frame`; contextweaver never sees the raw search response |
| I-06 — `CapabilityToken`s are scoped | Each step uses its own token with a narrow scope and `single_use: true` |
| I-07 — ChainWeaver delegates execution to the kernel | ChainWeaver issues no tool calls of its own; every capability invocation passes through agent-kernel |

---

## Cross-references

- Architecture: [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) — three-layer model and data flow.
- Boundaries: [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md) — artifact ownership; ChainWeaver does not own execution.
- Invariants: [`docs/INVARIANTS.md`](../docs/INVARIANTS.md) — I-01 through I-07.
- Sequence diagrams: [`docs/SEQUENCE_DIAGRAMS.md`](../docs/SEQUENCE_DIAGRAMS.md) section 3 (full-stack happy path).
- Failure modes for the same flow shape: [`failure_scenarios.md`](failure_scenarios.md).
- Partial-match routing decisions: [`partial_capability_routing.md`](partial_capability_routing.md).
