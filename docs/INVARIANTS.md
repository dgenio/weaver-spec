# Invariants

These are the non-negotiable properties of the Weaver stack. Any implementation that violates these invariants is not spec-compliant, regardless of other behavior.

---

## Core Invariants

### I-01: LLM Never Sees Raw Tool Output by Default

The LLM context window must never receive raw tool output unless an explicit, auditable override is configured. All tool output must pass through the agent-kernel firewall and be represented as a `Frame` before being made available to contextweaver or the LLM.

**Rationale:** Raw tool output may contain secrets, PII, large binary content, or injection vectors. The default must be safe.

**What "default" means:** Without explicit opt-in configuration, the firewall is always active. An implementation may expose a `raw_passthrough` mode for trusted internal pipelines, but this must be explicitly declared in the `CapabilityToken` and recorded in the audit log.

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
