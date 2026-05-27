# Weaver Stack Ecosystem Map

A neutral map of the projects in the Weaver ecosystem: what each one is, where the boundaries are, and which contracts cross between them.

> [!NOTE]
> This page is a **derived, informative** overview. The canonical authorities are [`docs/BOUNDARIES.md`](BOUNDARIES.md) (responsibility boundaries and artifact ownership), [`docs/LIFECYCLE.md`](LIFECYCLE.md) (the normative five-phase lifecycle), and [`docs/ARTIFACT_CONTRACTS.md`](ARTIFACT_CONTRACTS.md) (cross-project artifacts). Where this page and a canonical doc differ, the canonical doc wins.

---

## Projects at a glance

> [!IMPORTANT]
> None of these projects requires adopting the others. Each is usable on its own as long as the contracts at any boundary it crosses are honored. See the [adoption paths](../README.md#adoption-paths) in the README.

| Project | One-line role | Position |
| ------- | ------------- | -------- |
| [contextweaver](https://github.com/dgenio/contextweaver) | Context compilation, tool routing, and `ChoiceCard` generation. | Runtime — routing |
| [agent-kernel](https://github.com/dgenio/agent-kernel) | Capability authorization, execution, output firewalling, and audit. | Runtime — execution |
| [ChainWeaver](https://github.com/dgenio/ChainWeaver) | Deterministic DAG / flow orchestration over a safe execution backend. | Runtime — orchestration |
| lessonweaver | Trace-to-lesson/skill learning loop; produces reviewed, reusable lessons and skills. | Adjacent — learning |
| vibeguard | Pre-merge safety gate for AI-generated code and file changes. | Adjacent — dev workflow |

> [!NOTE]
> Only contextweaver, agent-kernel, and ChainWeaver sit on the runtime request path. lessonweaver and vibeguard are adjacent tools that share contracts and conventions but are not required for a working Weaver stack. AgentFence (an external policy firewall/proxy) is a further adjacent option described in the [README ecosystem map](../README.md#ecosystem-map). Project names without a link do not yet have a public repository to point at.

---

## Boundary table

Each project owns a distinct, non-overlapping responsibility. The contracts named below are defined in [`contracts/json/`](../contracts/json/) (Core) and [`contracts/json/extended/`](../contracts/json/extended/) (Extended).

| Project | Owns | Does not own | Consumes contracts | Emits contracts |
| ------- | ---- | ------------ | ------------------ | --------------- |
| contextweaver | Context compilation, routing, ChoiceCard generation | Execution, firewalling, token issuance | `Frame`; passes `CapabilityToken` through | `RoutingDecision`, `ChoiceCard` |
| agent-kernel | Output firewall, capability execution, authorization, audit | Routing, flow orchestration | `RoutingDecision`; the `CapabilityToken` it issued | `CapabilityToken`, `PolicyDecision`, `Frame`, `Handle`, `TraceEvent` |
| ChainWeaver | DAG/flow definition, step sequencing, pure inter-step transforms | Direct tool execution, token issuance, raw output access | `RoutingDecision`, `CapabilityToken` (delegates execution to agent-kernel) | Flow orchestration state (per-step `RoutingDecision` usage) |
| lessonweaver | Trace → lesson/skill review and export | Routing, execution, authorization | `ReviewArtifact` / trace records | `LessonCard`, `SkillCard` |
| vibeguard | Pre-merge artifact safety gate | The runtime request path | `ArtifactSafetyGateRequest` | `ArtifactSafetyReport` |

> [!IMPORTANT]
> The runtime artifact-ownership rows (contextweaver, agent-kernel, ChainWeaver) are normative and defined in [`docs/BOUNDARIES.md`](BOUNDARIES.md). This table is a convenience view; it must not contradict that document. Changing a runtime boundary requires a spec-level ADR.

---

## Example end-to-end lifecycle

**Example:** an illustrative request flowing through the full ecosystem. The normative routing-to-execution phases are defined in [`docs/LIFECYCLE.md`](LIFECYCLE.md); the learning and safety-gate steps are adjacent and optional.

1. **Context selection** — contextweaver compiles context and emits a `RoutingDecision` carrying `ChoiceCard`s.
2. **Policy check** — agent-kernel evaluates authorization and emits a `PolicyDecision` (`allow` / `deny`).
3. **Deterministic execution** — agent-kernel executes the selected capability behind its firewall, emitting a `Frame` (safe view) plus a `Handle` (opaque reference to raw output). For multi-step work, ChainWeaver sequences the steps but still delegates each invocation to agent-kernel.
4. **Trace capture** — agent-kernel appends `TraceEvent`s to the audit log; these can be packaged as `ReviewArtifact`s for downstream review.
5. **Lesson review / export** — lessonweaver reviews captured traces and exports approved `LessonCard` / `SkillCard` artifacts for reuse.
6. **Repo safety gate** — when an agent proposes code or file changes, vibeguard consumes an `ArtifactSafetyGateRequest` and emits an `ArtifactSafetyReport` before merge.

> [!NOTE]
> A minimal request can stop after step 4. Steps 5 and 6 belong to adjacent tools and are not part of the runtime request path.

---

## What lives in weaver-spec vs the individual repos

| Concern | Home |
| ------- | ---- |
| Contract shapes (JSON Schemas + Python dataclasses) | **weaver-spec** |
| Invariants, responsibility boundaries, lifecycle definition | **weaver-spec** |
| Versioning rules and the compatibility manifest | **weaver-spec** |
| Routing algorithms, ChoiceCard scoring | contextweaver |
| Firewall rules, token issuance/verification, audit storage | agent-kernel |
| Flow/DAG engine, retry and step-sequencing logic | ChainWeaver |
| Lesson/skill extraction and review workflow | lessonweaver |
| Code-risk scanning rules and gate policy | vibeguard |

> [!IMPORTANT]
> weaver-spec is **documentation + contracts only**. Algorithms, runtime logic, and storage live in the individual repos — never here. See [`AGENTS.md`](../AGENTS.md).

---

## Compatibility and versioning

- Versioning rules and the compatibility status vocabulary: [`docs/VERSIONING.md`](VERSIONING.md).
- Machine-readable, sibling-by-sibling support manifest: [`compatibility.yaml`](../compatibility.yaml).
- Concrete cross-repo handoff payloads: [`docs/INTEGRATION_MAP.md`](INTEGRATION_MAP.md).

No sibling repository has published a verified compatibility declaration yet; every entry in the manifest is currently `unverified`.
