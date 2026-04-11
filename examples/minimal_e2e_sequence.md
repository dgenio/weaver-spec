# Minimal End-to-End Sequence

This example traces a complete single-turn interaction through the full Weaver stack: contextweaver routing → agent-kernel authorization and execution → Frame returned to caller.

---

## Scenario

**User request:** "How do I configure retries?"

**Available tools (1000+ registered):** The agent has access to documentation search, database queries, API calls, and many other capabilities. Without routing, all schemas would need to be injected into the prompt.

---

## Step 1: Context Compilation (contextweaver)

contextweaver receives the conversation state and the full capability registry. It identifies that the user's intent is documentation retrieval and compiles a bounded `ChoiceCard` with 3 relevant options.

**Payload produced:** [`routing_decision.json`](sample_payloads/routing_decision.json)

Key properties:

- Only 3 tools are presented to the LLM (not 1000+).
- The LLM selects `search-docs` → `selected_item_id = "search-docs"`.
- contextweaver does not execute anything.

---

## Step 2: Authorization (agent-kernel)

agent-kernel receives the `RoutingDecision` and the `CapabilityToken` for the current session.

**Token used:** [`capability_token.json`](sample_payloads/capability_token.json)

The policy engine checks:

- Is `org.myapp.search_docs` in the token's scope? ✅
- Is the token unexpired? ✅
- Is the principal allowed to invoke this capability? ✅

**PolicyDecision produced:** `{ "decision": "allow", "capability_id": "org.myapp.search_docs", ... }`

A `TraceEvent` of type `capability_authorized` is appended to the audit log.

---

## Step 3: Execution and Firewalling (agent-kernel)

agent-kernel invokes the `search_docs` tool with the query extracted from the routing context.

**Raw output (stays inside agent-kernel, never exposed):**

```json
{
  "hits": [
    { "internal_id": "doc://internal/retry-policies", "title": "Retry Policies Overview", ... },
    ...
  ],
  "ranking_signals": { "bm25": [...], "semantic": [...] },
  "index_metadata": { "shard": 3, "version": "2026.03" }
}
```

The firewall processes the raw output:

- Strips internal IDs and ranking signals (sensitive).
- Extracts titles, slugs, and relevance scores (safe).
- Stores the full raw response as a Handle in the HandleStore.
- Produces a Frame.

**Frame produced:** [`frame_with_handles.json`](sample_payloads/frame_with_handles.json)

A `TraceEvent` of type `capability_executed` is appended to the audit log.
A `TraceEvent` of type `firewall_applied` is appended to the audit log.

---

## Step 4: Frame Ingestion (contextweaver)

contextweaver receives the `Frame`. It incorporates the summary and structured data into the context for the next LLM turn.

The LLM sees:
> "Found 3 documentation pages matching 'retry configuration': (1) Retry Policies Overview, ..."

The LLM **never** sees:

- Internal document IDs
- Ranking signals
- Raw search index metadata

---

## Invariants Demonstrated

| Invariant | How it's satisfied in this example |
| ----------- | ----------------------------------- |
| I-01: LLM never sees raw tool output | Raw output stays in agent-kernel; only Frame reaches contextweaver |
| I-02: Every execution authorized and auditable | PolicyDecision + 3 TraceEvents recorded |
| I-03: Routing without full schema injection | Only 3 ChoiceCard items in the prompt, not 1000+ schemas |
| I-05: contextweaver ingests Frames only | contextweaver receives Frame, not raw output |
| I-06: Tokens are scoped | Token scope explicitly lists 3 capability IDs |
