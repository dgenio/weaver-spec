# Invariants

> [!IMPORTANT]
> Every statement under each `I-NN` heading in this document is **normative**. An implementation that violates any of I-01 through I-07 is not spec-compliant. Subsections labelled **Rationale** are **informative** — they explain *why*, not *what*.

These are the non-negotiable properties of the Weaver stack. Any implementation that violates these invariants is not spec-compliant, regardless of other behavior.

> [!NOTE]
> This document is the highest-authority spec page in the repo. When other docs appear to contradict an invariant here, **this page wins** — see the authority hierarchy in `AGENTS.md`. Doc markup conventions are described in [docs/DOCS_CONVENTIONS.md](DOCS_CONVENTIONS.md).

---

## Core Invariants

### I-01: LLM Never Sees Raw Tool Output by Default

The LLM context window must never receive raw tool output unless an explicit, auditable override is configured. All tool output must pass through the agent-kernel firewall and be represented as a `Frame` before being made available to contextweaver or the LLM.

**Rationale:** Raw tool output may contain secrets, PII, large binary content, or injection vectors. The default must be safe.

**What "default" means:** Without explicit opt-in configuration, the firewall is always active. An implementation may expose a `raw_passthrough` mode for trusted internal pipelines, but this must be explicitly declared in the `CapabilityToken` and recorded in the audit log.

> [!NOTE]
> A structural wire representation for this override — and a corresponding
> conformance check that exempts a correctly declared-and-audited passthrough
> without weakening the default check — is **proposed, not yet accepted**, in
> [ADR 003](adr/003-raw-passthrough-override.md) ([#117](https://github.com/dgenio/weaver-spec/issues/117)). Until it is accepted, any `Frame` carrying raw output is treated as an I-01 violation by the conformance suite.

---

### I-02: Every Execution Is Authorized and Auditable

Every tool invocation must be preceded by a `PolicyDecision` (allow/deny) and followed by a `TraceEvent` entry in the audit log. There is no mechanism for "silent" execution.

**Required for compliance:**

- A `CapabilityToken` must be present and validated before execution.
- The resulting `PolicyDecision` must be recorded.
- The `TraceEvent` must include the capability ID, principal, timestamp, and outcome.

---

### I-03: Routing Does Not Require Full Tool Schema Injection

contextweaver must be able to produce a `RoutingDecision` without injecting full tool schemas (argument definitions, descriptions) into the LLM prompt. The `ChoiceCard` contract is designed to carry only the information needed for the LLM to make a selection.

**Rationale:** Injecting all tool schemas at every turn is the primary cause of context bloat. The routing layer must solve selection without this.

---

### I-04: Contracts Are Minimal and Stable

Core contracts must contain only the fields that are necessary for interoperability. No implementation-specific metadata belongs in a Core contract. The goal is a small, stable surface that changes infrequently.

**Corollary:** Extended contracts exist for optional metadata. If a field is only useful to one implementation, it belongs in that implementation's Extended contract or local extension, not in the Core.

---

### I-05: contextweaver Receives Frames, Not Raw Output

This is a restatement of I-01 from the perspective of contextweaver. contextweaver's ingestion interface accepts `Frame` objects. An implementation of contextweaver that accepts raw tool output as a first-class input is not spec-compliant.

**Canonical path:** The `Frame` seam — agent-kernel produces a `Frame`, contextweaver consumes it — is the default and only compliant path for **first-class** ingestion. The sole exception is the explicit, auditable `raw_passthrough` override of [I-01](#i-01-llm-never-sees-raw-tool-output-by-default), declared in the `CapabilityToken` and recorded in the audit log; absent that override, any raw-output ingestion is **non-canonical** and not spec-compliant. contextweaver's budgeted selection/packing stage operates over already-safe `Frame`s; it is *not* a second output firewall and must not re-derive firewalling from raw output. See [BOUNDARIES.md → "The Two 'Firewalls'"](BOUNDARIES.md#the-two-firewalls-the-canonical-frame-seam) and [ADR 002](adr/002-context-firewall-frame-seam.md).

**Rationale:** The artifact half of this invariant (a `Frame` carries no raw output) is the same property as I-01 and is conformance-checkable. The behavioral half (the ingestion interface refuses raw output) is a layer behavior verified by the contextweaver conformance harness, not against a static artifact.

---

### I-06: CapabilityTokens Are Single-Use or Scoped

A `CapabilityToken` must have an explicit scope (capability IDs it authorizes) and must either be single-use or have an expiry. Tokens must not grant unlimited, unscoped execution authority.

---

### I-07: ChainWeaver Delegates Execution to the Kernel

A ChainWeaver flow step that invokes a tool must delegate to agent-kernel (or a compatible execution layer). ChainWeaver must not call tools directly without going through the authorization and auditing path.

---

## Invariant Summary Table

| ID | Invariant | Enforced at |
| ---- | ----------- | ------------- |
| I-01 | LLM never sees raw tool output by default | agent-kernel firewall |
| I-02 | Every execution is authorized and auditable | agent-kernel policy engine + audit log |
| I-03 | Routing without full schema injection | contextweaver ChoiceCard design |
| I-04 | Core contracts minimal and stable | This spec (ADR process) |
| I-05 | contextweaver ingests Frames only | contextweaver ingestion interface |
| I-06 | CapabilityTokens are scoped | agent-kernel token issuance |
| I-07 | ChainWeaver delegates execution | ChainWeaver step executor |
