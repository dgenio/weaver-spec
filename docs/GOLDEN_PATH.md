# Cross-Repo Golden Path — tracking + canonical sequence

> [!NOTE]
> This page is **informative** and exists to keep the cross-repo counterparts in
> sync. The canonical authorities remain [`docs/INVARIANTS.md`](INVARIANTS.md),
> [`docs/BOUNDARIES.md`](BOUNDARIES.md), and [`docs/LIFECYCLE.md`](LIFECYCLE.md);
> where this page and a canonical doc differ, the canonical doc wins. Authority
> order: `INVARIANTS.md > BOUNDARIES.md > ARCHITECTURE.md > everything else`.

The "golden path" is the one end-to-end story the whole Weaver Stack is built
around: a request flows through routing, execution, gating, and audit, and the
resulting traces feed a learning loop that improves the next request. It only
holds together if the per-repo pieces keep agreeing on the contracts at each
seam. This page is the coordination point (weaver-spec issue
[#82](https://github.com/dgenio/weaver-spec/issues/82)) so the counterparts do
not drift into incompatible shapes.

---

## The canonical sequence

Each step names the contract that crosses the boundary into the next step. The
contract shapes are defined in [`contracts/json/`](../contracts/json/) (Core)
and [`contracts/json/extended/`](../contracts/json/extended/) (Extended).

1. **contextweaver routes** — compiles context and emits a
   [`RoutingDecision`](../contracts/json/routing_decision.schema.json) carrying
   `ChoiceCard`s. *(Core: `RoutingDecision`, `ChoiceCard`, `SelectableItem`)*
2. **ChainWeaver executes** — for multi-step work, sequences the flow but
   delegates every tool invocation to the execution layer (invariant
   [I-07](INVARIANTS.md#i-07-chainweaver-delegates-execution-to-the-kernel)).
   *(Extended: `ExecutionRoutingDecision` / `CompiledFlow` where a learned router
   is involved; otherwise Core `RoutingDecision` per step.)*
3. **agent-kernel gates** — validates a `CapabilityToken`, records a
   `PolicyDecision` (allow/deny), then executes behind the firewall and returns a
   `Frame` (+ `Handle`) — never raw output (invariants
   [I-01](INVARIANTS.md#i-01-llm-never-sees-raw-tool-output-by-default),
   [I-02](INVARIANTS.md#i-02-every-execution-is-authorized-and-auditable),
   [I-05](INVARIANTS.md#i-05-contextweaver-receives-frames-not-raw-output)).
   *(Core: `CapabilityToken`, `PolicyDecision`, `Frame`, `Handle`)*
4. **AgentFence external gate** — an optional external policy firewall/proxy that
   can allow/deny/ask at the boundary before the call reaches the tool. It
   complements, and does not replace, the agent-kernel firewall.
   *(Shared policy vocabulary — tracked in
   [#78](https://github.com/dgenio/weaver-spec/issues/78), not yet a contract.)*
5. **Traces** — agent-kernel appends `TraceEvent`s; a complete request can be
   gathered into a [`TraceBundle`](TRACE_BUNDLE.md) (tamper-evident audit chain).
   *(Core: `TraceEvent`; Extended: `TraceBundle`)*
6. **lessonweaver learns** — consumes findings/failures (the canonical
   interchange: [`FailureCaseArtifact`](ARTIFACT_CONTRACTS.md#failurecaseartifact)
   referencing a `TraceBundle`) and reviews them into reusable knowledge.
   *(Extended: `FailureCaseArtifact`, `ReviewArtifact`)*
7. **Skill cards back into contextweaver** — reviewed `LessonCard` / `SkillCard`
   artifacts re-enter routing as applicable guidance, closing the loop.
   *(Extended: `LessonCard`, `SkillCard`)*

The routing-to-execution phases (steps 1–3, 5) are the **normative** request
path defined in [`docs/LIFECYCLE.md`](LIFECYCLE.md). Steps 4, 6, and 7 are
adjacent and optional: a minimal request stops after the trace is captured.

See the Mermaid renderings in [`SEQUENCE_DIAGRAMS.md`](SEQUENCE_DIAGRAMS.md)
(notably "Full Stack") for the runtime portion of this path.

---

## Per-step contract dependencies

| Step | Producer | Consumer | Contract(s) at the seam | Tier |
| ---- | -------- | -------- | ----------------------- | ---- |
| 1 | contextweaver | ChainWeaver / agent-kernel | `RoutingDecision` (+ `ChoiceCard`, `SelectableItem`) | Core |
| 2 | ChainWeaver | agent-kernel | per-step `RoutingDecision`; `ExecutionRoutingDecision` / `CompiledFlow` when routed | Core / Extended |
| 3 | agent-kernel | caller / contextweaver | `CapabilityToken`, `PolicyDecision`, `Frame`, `Handle` | Core |
| 4 | AgentFence | agent-kernel / host | shared Policy + safety-class vocabulary | Extended *(proposed)* |
| 5 | agent-kernel | audit / lessonweaver | `TraceEvent`, `TraceBundle` | Core / Extended |
| 6 | any producer | lessonweaver | `FailureCaseArtifact`, `ReviewArtifact` | Extended |
| 7 | lessonweaver | contextweaver | `LessonCard`, `SkillCard` | Extended |

---

## Cross-repo counterpart checklist

Status reflects the **weaver-spec** side only; the runtime/adjacent
implementations live in their own repositories and track their own counterparts.

| Concern | weaver-spec piece | Status (spec side) | Counterparts |
| ------- | ----------------- | ------------------ | ------------ |
| Closed learning loop | `FailureCaseArtifact` + `TraceBundle` as canonical interchange ([#83](https://github.com/dgenio/weaver-spec/issues/83)) | Contracts shipped; interchange finalized + producer mappings documented | lessonweaver#91, vibeguard#120, agentfence#77, ChainWeaver#210 |
| Firewall / Frame seam | I-05 clarified + boundary section + [ADR 002](adr/002-context-firewall-frame-seam.md) ([#84](https://github.com/dgenio/weaver-spec/issues/84)) | Documented; static-checkable portion under I-01 | contextweaver#352, agent-kernel firewall |
| Shared policy contract | `Policy` + safety-class contract ([#78](https://github.com/dgenio/weaver-spec/issues/78)) | Proposed (not yet a contract) | agentfence#76, agent-kernel policy |
| End-to-end golden-path demo | runnable [`examples/reference_impl/`](../examples/reference_impl/) | Core path shipped | contextweaver#353, lessonweaver#92, ChainWeaver examples |

> [!NOTE]
> This checklist is maintained as the counterpart issues land. It is a status
> view, not a contract; a row going stale here never changes what an invariant
> or boundary requires.

---

## Related

- [`docs/LIFECYCLE.md`](LIFECYCLE.md) — the normative five-phase lifecycle.
- [`docs/ECOSYSTEM.md`](ECOSYSTEM.md) — neutral ecosystem boundary map.
- [`docs/ARTIFACT_CONTRACTS.md`](ARTIFACT_CONTRACTS.md) — the closed-loop
  interchange vocabulary.
- [`docs/SEQUENCE_DIAGRAMS.md`](SEQUENCE_DIAGRAMS.md) — Mermaid renderings of the
  runtime path.
