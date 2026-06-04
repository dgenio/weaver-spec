# Responsibility Boundaries

> [!IMPORTANT]
> Every boundary statement in this document is **normative**. Each "Decision" block and the artifact-ownership tables are binding on spec-compliant implementations. Sections labelled **Rationale** are **informative** — they explain *why*, not *what*. Changing a normative boundary requires a spec-level ADR (see `CONTRIBUTING.md`).

This document records the explicit boundary decisions that prevent overlap and duplication across the three Weaver repositories. These decisions are **non-negotiable**; changing them requires a spec-level ADR.

> [!NOTE]
> Doc markup conventions used throughout the spec are described in [docs/DOCS_CONVENTIONS.md](DOCS_CONVENTIONS.md). Authority order: `INVARIANTS.md > BOUNDARIES.md > ARCHITECTURE.md > everything else`.

---

## The Critical Boundary: Kernel Owns the Firewall

### Decision

> **agent-kernel owns**: raw tool output → firewall → `Frame` + `Handle` + access control + audit log.
>
> **contextweaver ingests only**: `Frame` (safe view). It never receives raw tool output by default.

### Rationale

This boundary exists for three reasons:

1. **Safety.** Raw tool output may contain secrets, PII, or large binary payloads that must never enter the LLM context window without filtering. Centralizing the firewall in agent-kernel ensures there is a single, auditable choke point.

2. **Separation of concerns.** contextweaver's job is context compilation and routing. It should not need to know anything about tool output formats, redaction rules, or storage backends. If contextweaver consumed raw output, every contextweaver implementation would have to re-implement firewalling.

3. **Partial adoption.** If you use only contextweaver (without agent-kernel), you bring your own execution layer. That layer must still honor the same contract: contextweaver receives a `Frame`, not raw output. This means the boundary holds regardless of which kernel implementation is present.

### What This Means Concretely

| Artifact | Owned by | May cross to |
| ---------- | ---------- | ------------- |
| Raw tool output | agent-kernel (internal only) | Nobody |
| `Frame` (safe summary) | agent-kernel (produces) | contextweaver, caller |
| `Handle` (opaque reference) | agent-kernel (produces) | HandleStore, caller with authorization |
| `CapabilityToken` | agent-kernel (issues) | contextweaver (passes through), tool executor |
| `PolicyDecision` | agent-kernel | Caller (for diagnostics) |
| `RoutingDecision` | contextweaver (produces) | agent-kernel |
| `ChoiceCard` | contextweaver (produces) | LLM prompt, caller |
| `TraceEvent` | agent-kernel (produces) | Audit log |

---

## The Two "Firewalls": the Canonical `Frame` Seam

### Decision

> The unqualified term **"firewall"** refers to the **agent-kernel output
> firewall** — the choke point that turns raw tool output into a `Frame` (+
> `Handle`). contextweaver's stage that decides what enters the prompt is
> **context budgeting / selection over already-safe `Frame`s**, not a second
> output firewall.
>
> The boundary between them is the **`Frame` seam**: agent-kernel *produces* a
> `Frame` at the firewall; contextweaver *consumes* `Frame`s. contextweaver must
> not re-derive output-firewalling from raw output on the canonical path.

### Rationale

The stack has historically called two different things a "context firewall": the
agent-kernel output firewall (above) and contextweaver's budgeted
selection/packing stage. Conflating them invites an implementer to rebuild
output-firewalling inside contextweaver from raw output, which would collapse the
safety boundary this document exists to protect. Naming one canonical seam — and
reserving "firewall" for the kernel side — keeps the choke point single and
auditable. This is a clarification of the ownership table above, not a change to
it. See [ADR 002](adr/002-context-firewall-frame-seam.md) and the cross-repo
[golden path](GOLDEN_PATH.md); the implementation-side counterpart is
contextweaver#352.

### What is statically checkable

The *artifact* half of the seam — a `Frame` that crosses it carries no raw output
— is the same property as invariant
[I-01](INVARIANTS.md#i-01-llm-never-sees-raw-tool-output-by-default) and is
asserted by the conformance runner's `frames_have_no_raw_output` check. The
*behavioral* half — an ingestion interface that refuses raw output — cannot be
asserted against a static artifact and is checked by sibling-repo harnesses (see
[`conformance/invariants.yaml`](../conformance/invariants.yaml)).

---

## Secondary Boundary: Routing Does Not Execute

**contextweaver must not execute tools.** Its output is always a `RoutingDecision` containing `ChoiceCard` objects. The actual capability invocation is always mediated by agent-kernel (or a compatible execution layer).

This boundary ensures:

- Routing is deterministic and testable without side effects.
- Authorization is always enforced at the execution layer, not the routing layer.
- contextweaver can be replaced or mocked without affecting execution safety guarantees.

---

## Secondary Boundary: ChainWeaver Does Not Own Execution

**ChainWeaver orchestrates flows but does not execute capabilities directly.** Each tool-invocation step in a flow is delegated to agent-kernel via the standard `CapabilityToken` + `RoutingDecision` contract. ChainWeaver may own:

- DAG definition and state machine.
- Step sequencing and retry logic.
- Pure (side-effect-free) data transformations between steps.

ChainWeaver must not:

- Call tools directly without going through agent-kernel.
- Issue or validate `CapabilityToken` objects.
- Access raw tool output.

---

## Why These Boundaries Enable Partial Adoption

Each boundary is defined in terms of contracts (data structures), not implementation coupling. This means:

- A team using only contextweaver can write their own execution layer that produces `Frame` objects. They get the routing benefits without needing agent-kernel.
- A team using only agent-kernel can use any routing mechanism that produces a `RoutingDecision`. They get the security benefits without needing contextweaver.
- A team using only ChainWeaver can use any execution backend that accepts a `CapabilityToken`.

The contracts are the interfaces. The repositories are the reference implementations.
