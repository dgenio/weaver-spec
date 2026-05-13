# Partial-Capability Routing

This example shows how contextweaver handles a request that overlaps several capabilities without being a perfect match for any of them. The routing layer ranks candidates and presents them as a single `ChoiceCard`. The LLM (or the caller's selector) picks one based on the ranked summary — no full tool schemas are injected.

The single-best-match happy path is in [`minimal_e2e_sequence.md`](minimal_e2e_sequence.md). Multi-step coordination across selected agents is in [`multi_agent_orchestration.md`](multi_agent_orchestration.md).

---

## Scenario

**User request:** "Show me yesterday's sales by region."

**Why this is a partial match:** the request is data-shaped but ambiguous. Several registered capabilities could plausibly serve it, and none is a single, unambiguous winner:

| Capability ID | What it does | Fit notes |
| --------------- | -------------- | ----------- |
| `org.myapp.run_sql_query` | Runs an ad-hoc SQL query against the sales warehouse | Strong fit — can compute the answer directly, but needs a query expression. |
| `org.myapp.open_saved_dashboard` | Opens an existing saved dashboard by name | Partial fit — a "Sales by region" dashboard exists, but it shows the trailing 7 days, not yesterday specifically. |
| `org.myapp.export_data` | Exports a filtered dataset slice to CSV/Parquet | Partial fit — can deliver the rows, but requires an explicit filter spec and does not aggregate by region. |

contextweaver presents all three as a ranked `ChoiceCard`. Ranking is the routing layer's job; **execution** is still gated by agent-kernel after the selection is made (per invariant I-07 / `docs/BOUNDARIES.md`).

Inline payload conventions: every JSON block is preceded by a `<!-- schema: <name> -->` marker that names the schema it validates against. CI extracts these blocks and validates them against `contracts/json/<name>.schema.json`.

---

## Step 1: contextweaver scores candidate capabilities

contextweaver evaluates the request intent against every capability in scope. It produces a numeric match score per capability using whatever signal mix it implements (semantic similarity on description text, tag overlap, recent caller success rate, etc. — the contract does not pin a specific ranking algorithm).

In this example the scores come out:

| Capability | Score | Rationale (recorded in `context_summary`) |
| ------------ | ------- | -------------------------------------------- |
| `org.myapp.run_sql_query` | 0.81 | Full semantic match for "sales by region"; arbitrary date filter is trivially expressible. |
| `org.myapp.open_saved_dashboard` | 0.62 | Named dashboard exists but timeframe mismatch (7-day vs. "yesterday"). |
| `org.myapp.export_data` | 0.47 | Can return raw rows but does not aggregate; would require a follow-up step. |

Only the top three are surfaced. Capabilities scoring below the cut-off threshold (e.g., document search at 0.18) are filtered out before the `ChoiceCard` is built. This is what keeps the `ChoiceCard` items list small (3 – 7 is the documented practical range — see `choice_card.schema.json`).

---

## Step 2: RoutingDecision produced with ranked items

contextweaver emits a single `ChoiceCard` containing the top three candidates in descending score order. Each `SelectableItem` carries the `label`, `description`, and `capability_id` the LLM needs to choose — nothing more. Full input schemas, argument types, and tool internals stay out of the prompt (invariant I-03).

<!-- schema: routing_decision -->
```json
{
  "id": "rd-20260513-partial-001",
  "choice_cards": [
    {
      "id": "card-sales-by-region",
      "context_hint": "Three capabilities partially match the request: show me yesterday's sales by region. They are listed in descending fit order; the first is the strongest match if a freshly-computed answer is acceptable.",
      "items": [
        {
          "id": "run-sql-query",
          "label": "Run an ad-hoc SQL query (recommended)",
          "description": "Compute yesterday's sales aggregated by region against the warehouse. Returns a result set in one call. Best when an authoritative, freshly-computed answer is required.",
          "capability_id": "org.myapp.run_sql_query"
        },
        {
          "id": "open-saved-dashboard",
          "label": "Open the 'Sales by region' saved dashboard",
          "description": "Open the curated dashboard. Caveat: the dashboard's default range is the trailing 7 days, not yesterday specifically. Prefer this when the caller wants the curated visualization.",
          "capability_id": "org.myapp.open_saved_dashboard"
        },
        {
          "id": "export-data",
          "label": "Export the raw sales slice for yesterday",
          "description": "Return raw rows for yesterday filtered to the sales fact table. Does not aggregate by region — a follow-up aggregation step is required. Use only when the caller wants the underlying data.",
          "capability_id": "org.myapp.export_data"
        }
      ]
    }
  ],
  "selected_item_id": "run-sql-query",
  "selected_card_id": "card-sales-by-region",
  "timestamp": "2026-05-13T13:45:00Z",
  "context_summary": "Partial-match routing for the request: Show me yesterday's sales by region. Top 3 candidates by fit score: run_sql_query=0.81 (full semantic match, expressible filter), open_saved_dashboard=0.62 (named dashboard exists, timeframe mismatch), export_data=0.47 (rows available, no aggregation). Cut-off threshold=0.40; 244 lower-scoring capabilities filtered out before card assembly."
}
```

The LLM (or the caller's selector logic) sees the ranked items and selects `run-sql-query` — the top-ranked option. contextweaver records the selection on the same `RoutingDecision` (`selected_item_id` + `selected_card_id`) and emits it.

---

## Step 3: Caller passes the selection to agent-kernel

agent-kernel will validate a `CapabilityToken` for `org.myapp.run_sql_query` and execute the query. That part of the flow follows the standard happy path documented in [`minimal_e2e_sequence.md`](minimal_e2e_sequence.md); only the routing phase is unusual here.

If the caller's selector picks a different ranked option (for example, `open-saved-dashboard` because the user wanted a visual), the same `RoutingDecision` shape is produced — only `selected_item_id` changes. Re-routing or re-ranking does **not** require a new `ChoiceCard`; the existing one already enumerates the alternatives.

---

## Why ChoiceCard and SelectableItem Are Separate

This walkthrough makes the rationale concrete (the separation is also called out in [`AGENTS.md`](../AGENTS.md) — "Design decisions not to reopen"):

- A **`SelectableItem`** is the minimum information the LLM needs to pick one option: a label, a short description, and an opaque `capability_id`. Crucially it does **not** carry the capability's input schema, internal arg types, or implementation hints. If `SelectableItem` carried full tool schemas, every routing turn would re-inflate the prompt (the exact problem invariant I-03 prevents).

- A **`ChoiceCard`** wraps an ordered set of `SelectableItem`s with a `context_hint` (how to interpret the choices), a stable `id` (for audit cross-reference), and structural constraints (`minItems: 1`, `maxItems: 20`). The card is the unit the LLM is asked to choose from. The card's `id` lets a follow-up step refer to "the same choice surface" without re-listing the items.

If the two were merged, the LLM prompt would have to carry either too much (per-item tool detail) or too little (no card-level framing). Keeping them separate lets adopters tune the card payload independently of the item payload.

The `RoutingDecision` then wraps the `ChoiceCard`s with the selection result (`selected_item_id`, `selected_card_id`) and audit-friendly metadata (`timestamp`, `context_summary`). That separation is what lets routing produce structurally identical payloads regardless of whether a selection has been made yet.

---

## Invariants Demonstrated

| Invariant | How it is satisfied |
| ----------- | --------------------- |
| I-03 — Routing without full schema injection | Each `SelectableItem` carries only `label`, `description`, and `capability_id` — no input schemas, no arg types. The full prompt for selection scales O(items), not O(tool surface area). |
| I-04 — Core contracts minimal and stable | The ranking signal is recorded in `context_summary` (free-form) rather than promoted to a Core field. Future ranking algorithms can record different signals without a Core contract change. |

---

## Cross-references

- Architecture: [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) — three-layer model; routing does not execute.
- Boundaries: [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md) — contextweaver produces `RoutingDecision` and `ChoiceCard`; agent-kernel handles execution.
- Invariants: [`docs/INVARIANTS.md`](../docs/INVARIANTS.md) — I-03 (no full schema injection), I-04 (Core minimal).
- Design rationale: [`AGENTS.md`](../AGENTS.md) — "Design decisions not to reopen" → ChoiceCard vs RoutingDecision separation.
- Happy-path single-best-match counterpart: [`minimal_e2e_sequence.md`](minimal_e2e_sequence.md).
- Multi-agent counterpart (when a flow needs two selections in sequence): [`multi_agent_orchestration.md`](multi_agent_orchestration.md).
