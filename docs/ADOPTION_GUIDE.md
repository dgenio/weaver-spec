# Adoption Guide

This guide explains how to adopt one, two, or all three Weaver components. Each section describes what you get, what you need to build yourself, and the tradeoffs.

---

## Adopting Only contextweaver

**What you get:**
- Smart, bounded tool routing: the LLM selects from ChoiceCards, not from 1000+ tool schemas.
- Context compilation that fits within a practical prompt window.
- A `RoutingDecision` that tells your execution layer what to run.

**What you need to build:**
- Your own execution layer that invokes the selected tool.
- Your own firewall: your execution layer must produce a `Frame` before passing output back to contextweaver. contextweaver will not accept raw tool output.

**What you don't get without agent-kernel:**
- Capability authorization and token validation.
- A standardized audit log.
- Built-in firewall / output redaction.

**Tradeoffs:**
- Simpler stack; you own execution safety.
- Suitable for trusted internal tools where authorization is handled at the infrastructure level.

**Contract requirements:**
- Implement the `Frame` contract for your execution layer's output.
- Consume the `RoutingDecision` contract from contextweaver.

---

## Adopting Only agent-kernel

**What you get:**
- Capability authorization via `CapabilityToken` and policy engine.
- Safe execution with firewall: raw output → `Frame` + `Handle`.
- Audit log (`TraceEvent`) for every execution.

**What you need to build:**
- Your own routing layer that produces a `RoutingDecision`.
- Your own context compilation.

**What you don't get without contextweaver:**
- ChoiceCard-based bounded routing.
- Context window optimization.

**Tradeoffs:**
- You get full security and auditability without adopting contextweaver's routing model.
- Suitable for systems with existing routing that need to add safety and compliance.

**Contract requirements:**
- Produce a `RoutingDecision` from your router.
- Issue and validate `CapabilityToken` objects.

---

## Adopting Only ChainWeaver

**What you get:**
- Deterministic DAG-based flow execution.
- Retry logic, partial failure handling, and state management for multi-step pipelines.
- Pure (side-effect-free) transformation steps between tool calls.

**What you need to build:**
- An execution backend that ChainWeaver can delegate tool-invocation steps to.
- That execution backend must honor the `CapabilityToken` + `RoutingDecision` contracts.

**What you don't get without agent-kernel:**
- Authorization and auditing for tool calls within flows.
- Firewall for tool output.

**Tradeoffs:**
- Suitable for deterministic pipelines with trusted tools where authorization is external.

---

## contextweaver + agent-kernel (No ChainWeaver)

**What you get:**
- Full routing + safe execution for single-step agentic tool use.
- The complete safety stack: ChoiceCard routing → authorization → firewall → Frame.

**What you don't get without ChainWeaver:**
- Multi-step DAG orchestration.
- Flow state management.

**Tradeoffs:**
- The right choice for single-turn or simple multi-turn interactions.
- Add ChainWeaver only when you need deterministic multi-step flows.

---

## agent-kernel + ChainWeaver (No contextweaver)

**What you get:**
- Deterministic flows with safe, authorized execution at each step.
- You provide your own routing for each flow step.

**What you don't get without contextweaver:**
- Bounded ChoiceCard routing.
- Context window optimization.

**Tradeoffs:**
- Suitable when flow steps are fully predefined and don't require dynamic tool selection by an LLM.

---

## Full Stack (contextweaver + agent-kernel + ChainWeaver)

**What you get:**
- End-to-end: dynamic routing → safe execution → deterministic orchestration.
- All invariants enforced: bounded routing, authorized execution, firewalled output, full audit trail.
- The complete composability story: each component replaceable independently.

**Tradeoffs:**
- More components to operate.
- Correct choice for production agentic systems that need the full safety, auditability, and composability guarantees.

---

## Minimum Contract Checklist by Adoption Mode

| Mode | Contracts you must implement |
|------|----------------------------|
| contextweaver only | `RoutingDecision`, `ChoiceCard`, `SelectableItem`, `Frame` (produced by your layer) |
| agent-kernel only | `RoutingDecision` (consumed), `Capability`, `CapabilityToken`, `PolicyDecision`, `Frame`, `Handle`, `TraceEvent` |
| ChainWeaver only | `RoutingDecision` (passed to executor), `CapabilityToken` (passed to executor) |
| cw + kernel | All Core contracts |
| kernel + flows | All Core contracts |
| Full stack | All Core contracts |
