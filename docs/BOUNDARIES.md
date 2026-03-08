# Responsibility Boundaries

This document records the explicit boundary decisions that prevent overlap and duplication across the three Weaver repositories. These decisions are **non-negotiable**; changing them requires a spec-level ADR.

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
|----------|----------|-------------|
| Raw tool output | agent-kernel (internal only) | Nobody |
| `Frame` (safe summary) | agent-kernel (produces) | contextweaver, caller |
| `Handle` (opaque reference) | agent-kernel (produces) | HandleStore, caller with authorization |
| `CapabilityToken` | agent-kernel (issues) | contextweaver (passes through), tool executor |
| `PolicyDecision` | agent-kernel | Caller (for diagnostics) |
| `RoutingDecision` | contextweaver (produces) | agent-kernel |
| `ChoiceCard` | contextweaver (produces) | LLM prompt, caller |
| `TraceEvent` | agent-kernel (produces) | Audit log |

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
