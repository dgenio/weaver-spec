# TraceBundle — end-to-end audit-chain envelope

> [!NOTE]
> This page is **informative**. `TraceBundle` is an **Extended** contract:
> optional, not required for spec compliance (invariant I-04). Authority order
> remains `INVARIANTS.md > BOUNDARIES.md > ARCHITECTURE.md > everything else`.
> Nothing here redefines an invariant or a normative boundary.

Today a request's audit trail is implicit: a `RoutingDecision` lives in one log
line, a `PolicyDecision` somewhere else, a `Frame` in a third place, and
`TraceEvent`s scattered across an append-only log. There is no single artifact
that says "here is what happened, end-to-end, tamper-evident."

`TraceBundle` is that artifact. It is a hosting envelope that **inlines** one
request's Core audit chain so the whole thing can be canonicalized, hashed, and
optionally signed as a unit. The schema lives at
[`contracts/json/extended/trace_bundle.schema.json`](../contracts/json/extended/trace_bundle.schema.json);
the Python mirror is `TraceBundle` in
[`weaver_contracts.extended`](../contracts/python/src/weaver_contracts/extended.py).

---

## Shape

| Field | Required | Meaning |
| ----- | :------: | ------- |
| `bundle_id` | yes | Non-empty stable identifier for the bundle. |
| `routing_decision` | yes | The Core `RoutingDecision` that opened the chain. |
| `policy_decisions` | yes | Array of Core `PolicyDecision`s recorded for the request. |
| `frames` | yes | Array of Core `Frame`s produced (safe to display; never raw output). |
| `handles` | yes | Array of Core `Handle`s referenced by the frames. |
| `trace_events` | yes | Array of Core `TraceEvent`s, in emission order. |
| `canonicalization` | no | Canonicalization scheme; fixed to `JCS` (RFC 8785). |
| `signature` | no | Optional detached signature (see below). |
| `created_at` | no | Optional ISO 8601 assembly timestamp. |
| `metadata` | no | Open extension bag; namespace project-specific keys. |

The full audit chain is required: a `TraceBundle` describes a **complete**
request, not a fragment. Each nested member is validated against its own Core
schema via `$ref`, so a bundle is only valid if every artifact it carries is
valid.

---

## Invariants it preserves (does not redefine)

> [!IMPORTANT]
> A `TraceBundle` carries the same artifacts the request already produced; it
> adds no new authority and relaxes no rule.
>
> - **I-01** — `Frame`s in the bundle carry no raw output; raw artifacts remain
>   behind `Handle`s.
> - **I-02** — each `PolicyDecision` is still expected to have a matching
>   `TraceEvent`. The bundle makes this checkable in one place, but a
>   conformance runner (tracked separately) is what asserts it.

---

## Signing

`signature` reuses the existing detached-signature shape,
[`CapabilityTokenSignature`](SIGNING.md) (`alg` / `kid` / `sig` /
`canonicalization` / `signed_at`), applied to the **JCS-canonicalized bundle**
with the `signature` field excluded from the canonical form before hashing.
This deliberately avoids inventing a second signature shape (see `AGENTS.md` →
"Domain clarifications").

> [!IMPORTANT]
> Signing is opt-in. When `signature` is absent the bundle is **unsigned**, and
> producers must not describe it as signed (`AGENTS.md` forbidden behavior:
> never describe aspirational features as current).

---

## Example (unsigned)

<!-- schema: trace_bundle -->
```json
{
  "bundle_id": "tb-20260308-001",
  "routing_decision": {
    "id": "rd-20260308-001",
    "choice_cards": [
      {
        "id": "card-retrieval",
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
    "timestamp": "2026-03-08T06:00:00Z"
  },
  "policy_decisions": [
    {
      "decision_id": "pd-20260308-001",
      "decision": "allow",
      "capability_id": "org.myapp.search_docs",
      "principal": "agent-session-7f3a",
      "token_id": "tok-20260308-abc123",
      "timestamp": "2026-03-08T06:00:01Z"
    }
  ],
  "frames": [
    {
      "frame_id": "frame-20260308-001",
      "capability_id": "org.myapp.search_docs",
      "summary": "Found 3 documentation pages matching 'retry configuration'.",
      "handle_refs": ["handle-rawresult-20260308-001"],
      "created_at": "2026-03-08T06:00:05Z"
    }
  ],
  "handles": [
    {
      "handle_id": "handle-rawresult-20260308-001",
      "capability_id": "org.myapp.search_docs",
      "artifact_type": "application/json",
      "created_at": "2026-03-08T06:00:05Z",
      "expires_at": "2026-03-09T06:00:05Z"
    }
  ],
  "trace_events": [
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
  ],
  "canonicalization": "JCS",
  "created_at": "2026-03-08T06:00:06Z"
}
```

A signed variant lives at
[`examples/sample_payloads/trace_bundle_signed.json`](../examples/sample_payloads/trace_bundle_signed.json).

---

## TraceBundle vs neighbouring artifacts

| Compared with | Difference |
| ------------- | ---------- |
| Raw append-only trace log | A bundle is a single, self-contained, hashable document for one request, not a stream. |
| `ReviewArtifact` | `ReviewArtifact` is a thin interchange shape that *references* evidence; a `TraceBundle` *inlines* the actual Core artifacts. |
| [`FailureCaseArtifact`](ARTIFACT_CONTRACTS.md) | A `FailureCaseArtifact` *references* a replayable failure (via `trace_ref`); a `TraceBundle` inlines a full successful-or-failed audit chain and may itself be the referenced evidence. |
| `EvaluationArtifact` | `EvaluationArtifact` is a statistical decision report; a `TraceBundle` is a literal audit chain of one request. |

---

## Status and versioning

`TraceBundle` is **Extended**: optional and opt-in. Per
[`docs/VERSIONING.md`](VERSIONING.md), Extended contracts may change (including
breaking changes) in a MINOR version. It was introduced in the `0.6.0` set.
