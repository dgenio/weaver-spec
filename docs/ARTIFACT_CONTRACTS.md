# Cross-Project Artifact Contracts

> [!NOTE]
> This page is **informative**. The artifact types below are **Extended**
> contracts: optional, not required for spec compliance (invariant I-04).
> Authority order remains `INVARIANTS.md > BOUNDARIES.md > ARCHITECTURE.md >
> everything else`. Nothing here redefines an invariant or a normative
> boundary.

The Weaver stack and its adjacent tools (lessonweaver, skdr-eval, vibeguard)
exchange several **standalone artifacts** that are neither Core request-path
contracts nor raw data. This page defines a small, language-neutral vocabulary
for them so projects interoperate without depending on each other's packages.

All schemas live under
[`contracts/json/extended/`](../contracts/json/extended/); the Python mirrors
are in
[`weaver_contracts.extended`](../contracts/python/src/weaver_contracts/extended.py).

---

## Shared envelope

Every artifact on this page shares a common envelope so producers and
consumers can treat them uniformly:

| Field | Meaning |
| ----- | ------- |
| `*_id` | Non-empty stable identifier. |
| `created_at` | ISO 8601 (`date-time`) creation timestamp. |
| `sensitivity` | One of `public` \| `internal` \| `confidential` \| `restricted` (where present). |
| `provenance` | Optional structured record of how/why the artifact was derived. |
| `metadata` | Open extension bag; namespace project-specific keys. |

IDs are any non-empty string (`minLength: 1`); UUIDs are not required (see
`AGENTS.md` → "ID format"). Timestamps are interchange strings, not parsed
types.

## Taxonomy

These artifacts are deliberately distinct from one another and from Core
contracts. Pick the narrowest type that fits:

| Type | Is | Is not |
| ---- | -- | ------ |
| `ReviewArtifact` | A generic interchange shape for any trace/review record. | A storage system; a Core `TraceEvent`. |
| `MemoryArtifact` | A durable/semi-durable, reusable memory record. | Transient context, raw tool output, or a trace. |
| `SessionHandoff` | A compact continuity pack between sessions. | Durable memory (it *references* memory). |
| `LessonCard` | A reviewed, reusable lesson derived from traces. | A raw trace, raw memory, or prompt fragment. |
| `SkillCard` | A reviewed, reusable procedure derived from traces. | A flow definition or a Core `Capability`. |
| `EvaluationArtifact` | A statistical evaluation report with semantics. | Proof of statistical validity; a deploy approval. |
| `ArtifactSafetyGateRequest` / `ArtifactSafetyReport` | Inputs/outputs of an artifact safety gate. | A specific scanner or rule set. |

---

## ReviewArtifact

The minimal cross-project interchange shape. `artifact_type` is producer-defined
(for example `context_build`, `execution_record`, `policy_decision`,
`review_note`, `safety_report`). Evidence and decisions are referenced, not
inlined.

**Produced/consumed by:** any project; commonly produced by agent-kernel,
contextweaver, lessonweaver and consumed by review/audit tooling.

<!-- schema: review_artifact -->
```json
{
  "artifact_id": "rev-20260527-001",
  "artifact_type": "review_note",
  "source_project": "agent-kernel",
  "created_at": "2026-05-27T08:00:00Z",
  "subject_ref": "flow:invoice_reminder_flow@1.2.0",
  "summary": "Execution completed within policy; no firewall bypass observed.",
  "evidence_refs": ["trace:evt-20260527-014"],
  "decision_refs": ["policy:pd-20260527-003"]
}
```

## MemoryArtifact

A durable or semi-durable memory record, distinct from transient context, raw
tool output, and traces. Because memory content may be sensitive, `sensitivity`
and `provenance` are first-class.

**Produced/consumed by:** contextweaver (memory source), agent-kernel, and
adjacent memory stores.

<!-- schema: memory_artifact -->
```json
{
  "memory_id": "mem-20260527-001",
  "memory_type": "repo_convention",
  "content": "This repo is docs + contracts only; never add runtime logic.",
  "source": "AGENTS.md",
  "created_at": "2026-05-27T08:00:00Z",
  "scope": "repo",
  "sensitivity": "internal",
  "confidence": 0.95
}
```

## SessionHandoff

A compact continuity pack carried between sessions. It references durable
memory via `memory_refs` rather than inlining it.

**Produced/consumed by:** the host application / orchestration layer at session
boundaries.

<!-- schema: session_handoff -->
```json
{
  "handoff_id": "ho-20260527-001",
  "from_session_id": "sess-20260527-am",
  "created_at": "2026-05-27T12:00:00Z",
  "summary": "Implemented Extended artifact contracts; tests green.",
  "sensitivity": "internal",
  "open_threads": ["Decide release date for 0.5.0."],
  "memory_refs": ["mem-20260527-001"]
}
```

## LessonCard and SkillCard

Reviewed, reusable knowledge derived from traces. `lifecycle_state`
(`draft` → `in_review` → `active` → `deprecated`) gates activation: a card
should pass through review before it is `active`.

**Produced/consumed by:** lessonweaver (producer); any agent that applies
approved lessons/skills.

<!-- schema: lesson_card -->
```json
{
  "lesson_id": "lsn-20260527-001",
  "title": "Regenerate generated artifacts before pushing",
  "body": "After any contracts/json change, regenerate the index and coverage table.",
  "created_at": "2026-05-27T09:00:00Z",
  "lifecycle_state": "active",
  "scope": "repo",
  "sensitivity": "internal",
  "applicability": ["changed:contracts/json/**"]
}
```

<!-- schema: skill_card -->
```json
{
  "skill_id": "skl-20260527-001",
  "name": "Add an Extended contract",
  "description": "End-to-end procedure for adding a new Extended contract type.",
  "created_at": "2026-05-27T09:30:00Z",
  "lifecycle_state": "in_review",
  "steps": ["Add the dataclass.", "Add the JSON schema.", "Add tests."],
  "preconditions": ["Type is non-universal (Extended, not Core) per I-04."]
}
```

## EvaluationArtifact

A statistical / offline evaluation report carried with explicit semantics so an
agent cannot misuse a headline score. `support_state` (`ok` \| `caution` \|
`high_risk`) summarizes diagnostic confidence; `recommendation_kind`
(`deploy` \| `do_not_deploy` \| `experiment_ready` \| `needs_more_data`) is the
machine-readable verdict.

> [!IMPORTANT]
> A `high_risk` evaluation must never recommend deployment. Both the JSON Schema
> and the Python contract reject `support_state = "high_risk"` together with
> `recommendation_kind = "deploy"`: a high-risk evaluation is not deployment
> evidence.

**Produced/consumed by:** skdr-eval (producer); contextweaver, ChainWeaver,
agent-kernel as interpreters/policy gates.

<!-- schema: evaluation_artifact -->
```json
{
  "artifact_id": "eval-20260527-001",
  "producer": "skdr-eval",
  "created_at": "2026-05-27T10:00:00Z",
  "artifact_type": "offline_policy_evaluation",
  "support_state": "caution",
  "metrics": {"estimated_value": 0.42},
  "uncertainty": {"value_ci": [0.31, 0.53]},
  "warnings": ["Limited overlap; estimate may be unstable."],
  "recommendation_kind": "experiment_ready"
}
```

## ArtifactSafetyGateRequest and ArtifactSafetyReport

An optional, implementation-neutral safety gate over agent-produced artifacts
(code, config, docs, manifests) before a high-impact action. The request
describes *what* and *how* to check; the report carries the verdict. `mode`
(`advisory` vs `blocking`) distinguishes an informational check from a gate
that must pass.

**Produced/consumed by:** vibeguard or an equivalent gate (producer); the host /
agent-kernel as the policy gate that acts on the result.

<!-- schema: artifact_safety_gate_request -->
```json
{
  "request_id": "asg-req-20260527-001",
  "repository_root": "/workspace/app",
  "artifact_paths": ["src/handlers/payment.py"],
  "diff_scope": "origin/main...HEAD",
  "policy_level": "strict",
  "output_format": "json"
}
```

<!-- schema: artifact_safety_report -->
```json
{
  "report_id": "asg-rep-20260527-001",
  "gate_id": "org.vibeguard.scan_changes",
  "decision": "fail",
  "created_at": "2026-05-27T10:30:00Z",
  "mode": "blocking",
  "findings": [
    {
      "finding_id": "f-001",
      "severity": "high",
      "message": "Hardcoded credential detected.",
      "remediation": "Move the secret to a secret store."
    }
  ]
}
```

---

## Status and versioning

These types are **Extended**: optional and opt-in. Per `docs/VERSIONING.md`,
Extended contracts may change (including breaking changes) in a MINOR version.
They were introduced in contract version `0.5.0`. Full sample payloads live in
[`examples/sample_payloads/`](../examples/sample_payloads/) and are validated in
CI against the schemas under
[`contracts/json/extended/`](../contracts/json/extended/).
