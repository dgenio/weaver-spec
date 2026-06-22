# Proposal: Substrate Engineering for the Weaver Stack

> [!NOTE]
> **Status: proposal / exploratory roadmap. Nothing in this document is normative.**
> This is a cross-repo idea map, not a specification and not an ADR. No contract,
> invariant, or boundary changes when this file merges. Any Core-contract change
> implied here requires its own ADR under [`docs/adr/`](../adr/README.md) and the
> six-artifact process in [`CONTRIBUTING.md`](../../CONTRIBUTING.md). Where this
> document appears to disagree with a canonical doc, the canonical doc wins
> (`docs/INVARIANTS.md` → `docs/BOUNDARIES.md` → `docs/ARCHITECTURE.md` → rest).

## Origin

This proposal is a response to a widely-shared argument (informally branded
"Substrate Engineering") that most AI systems are still just `Input → Model →
Output` with **no semantic protocol** in between. The claim: because the model
re-derives the meaning of a domain on every inference, meaning silently drifts
run-to-run — the post calls this **"interpretation drift."** The proposed fix is
a single **formal object that declares the semantic substrate of a domain**, with
seven facets:

`entities · identity rules · invariants · admissible states · operators · temporal constraints · acceptance criteria`

The analogy used is TCP/IP: networks scale because the protocol names the state
machine and its admissible transitions; ad-hoc agents do not scale because they
re-improvise that state machine on every call. The success bar proposed is
**reproducibility** — multiple frontier models, 100+ runs, perturbed
temperature / prompt / time, converging on type-identical output.

## Why this is relevant to the Weaver Stack

The Weaver Stack already implements nearly every *mechanism* the argument calls
for — but as the substrate of **the Weaver protocol itself**, not as a substrate
an *adopter* can declare for **their own domain**. The seven facets already have
homes:

| Substrate facet | Where it already lives | Reference |
| --------------- | ---------------------- | --------- |
| entities | Core contract types (`SelectableItem`, `Capability`, `Frame`, …) | `contracts/json/`, `docs/CONTRACT_REFERENCE.md` |
| identity rules | agent-kernel `Principal` + HMAC-bound `CapabilityToken` | agent-kernel `tokens.py`; I-06 |
| invariants | Spec invariants I-01…I-07; ChainWeaver's executor rules | `docs/INVARIANTS.md`; ChainWeaver `AGENTS.md` |
| admissible states | contextweaver sensitivity floor; `PolicyDecision`; vibeguard/agentfence verdicts | `docs/SECURITY_MAPPING.md` |
| operators | agent-kernel `Capability`; ChainWeaver `Flow` / `DAGFlow` | ChainWeaver `flow.py` |
| temporal constraints | ChainWeaver step sequencing, `depends_on`, governance lifecycle | ChainWeaver `flow.py` |
| acceptance criteria | intentflow typed `output` contracts + verification rules; skdr-eval estimators | intentflow `.iflow`; skdr-eval |
| reproducibility metric | ChainWeaver `attest_flow()`; skdr-eval trust diagnostics | ChainWeaver `contracts.py`; skdr-eval |

> [!NOTE]
> **The gap this proposal targets:** the seven facets are scattered across five
> tools and never unified into one declarative, versioned, hashable artifact that
> an adopter authors *once* to describe their domain. The stack has the runtime
> layers that would *enforce* and *measure* such an artifact, but no place to
> *declare* it.

## The seed: two candidate artifacts

This proposal does **not** ask to add a Core contract today. It names two
candidate artifacts so the cross-repo map below has something concrete to point
at. Both would start life as **Extended** contracts (faster-moving, optional,
implementation-shaped) and only graduate to Core via ADR if adoption proves them
out — consistent with I-04 (Core stays minimal and stable).

1. **`DomainSubstrate`** — a declarative object carrying the seven facets for a
   single adopter domain. Versioned and content-hashable so a given substrate
   version is a stable referent across runs, models, and repos.
2. **`InterpretationDrift` metric** — a measurable quantity: "given substrate
   version `S`, how stable is interpretation across N runs / M models?" This is
   the part that turns the marketing phrase into something falsifiable, and it is
   the most defensible idea in the original argument.

> [!NOTE]
> **Naming is not settled.** `DomainSubstrate` / `SemanticSubstrate` and
> `InterpretationDrift` / `SemanticStability` are placeholders. Naming, facet
> shape, and Core-vs-Extended placement are open questions (see end of doc).

## Cross-repo adoption map

> [!NOTE]
> This table is a *roadmap*, not a commitment. "Phase" is suggested sequencing,
> not a schedule. Each row is independently adoptable — no repo is blocked on
> another except where "depends on" is stated.

| Repo | Role under this proposal | Suggested change | Phase | Depends on |
| ---- | ------------------------ | ---------------- | ----- | ---------- |
| weaver-spec | Define the substrate vocabulary | Author `DomainSubstrate` + `InterpretationDrift` as Extended contracts; map facets to existing Core types | 1 | — |
| intentflow | Substrate *authoring* surface | Treat an `.iflow` program (goals + evidence + output contract + verification) as the human-facing way to declare a `DomainSubstrate`; emit one on compile | 2 | weaver-spec |
| agent-kernel | Substrate *enforcement* (runtime) | Derive policy / admissibility checks from a substrate's invariants + admissible-state facets instead of only hand-written rules | 2 | weaver-spec |
| ChainWeaver | Substrate *transition* validation | Validate that a flow's step graph only takes transitions admissible under the substrate's temporal-constraint facet | 3 | weaver-spec |
| contextweaver | Substrate-aware context selection | Use substrate entities + identity to stabilize what is surfaced (reduce drift at the prompt-construction layer) | 3 | weaver-spec |
| agentfence | Substrate *enforcement* (edge) | Compile substrate invariants into MCP allow/deny policy at the external proxy edge | 3 | weaver-spec |
| vibeguard | Substrate *enforcement* (dev-time) | Add rule(s) that check proposed code/artifacts against declared substrate invariants pre-merge | 3 | weaver-spec |
| skdr-eval | Substrate *measurement* | Implement the `InterpretationDrift` metric: estimate interpretation stability across runs/models against a fixed substrate version | 2 | weaver-spec |
| lessonweaver | Substrate *evolution* | When traces reveal recurring drift, propose substrate amendments (new invariant / tightened admissible state) through the existing human review gate | 4 | weaver-spec, skdr-eval |

### Per-repo detail

#### weaver-spec (Phase 1 — vocabulary)

Author `DomainSubstrate` and `InterpretationDrift` as **Extended** schemas +
dataclasses + sample payloads + roundtrip tests (the standard artifact set).
Add a glossary entry and a short concept doc. Do **not** touch Core or any
I-0x invariant. This phase is a pure docs+Extended-contract addition; it is
reversible and ships no behavior.

#### intentflow (Phase 2 — authoring)

intentflow is already the closest thing to a substrate-authoring language:
`.iflow` programs declare goals, evidence policy, action governance,
verification rules, uncertainty handling, and a typed `output` contract, then
compile to a hashed, replayable plan. Proposal: add a compile target that emits
a `DomainSubstrate` so an `.iflow` program *is* a substrate declaration the rest
of the stack can consume. No change to intentflow's determinism or audit story.

#### agent-kernel (Phase 2 — runtime enforcement)

The kernel already enforces I-01/I-02/I-06 and evaluates policy top-down,
first-match-wins, deterministically. Proposal: let a `DomainSubstrate` be an
*input* to policy — its invariants and admissible-state facets become generated
deny rules, evaluated before hand-written rules. This must respect the existing
ordering trap (new allow rules before sensitivity checks silently bypass them):
substrate-derived rules are deny/guard rules, never allow rules.

#### ChainWeaver (Phase 3 — transition validation)

ChainWeaver already models operators (tools), sequencing (`FlowStep`,
`depends_on`), and a determinism taxonomy (`FULL/PARTIAL/NONE`). Proposal: a
flow may reference a substrate; at compile/validate time, check that every step
transition is admissible under the substrate's temporal-constraint facet. The
executor's three hard invariants (no LLM, no network, no randomness) are
untouched — validation happens at build time, not in `executor.py`.

#### contextweaver (Phase 3 — drift reduction at the prompt)

Proposal: when a substrate is present, use its entity + identity facets to keep
the model-visible surface semantically stable (consistent naming, consistent
ChoiceCard framing for the same entity). This attacks interpretation drift at the
point it is introduced — prompt construction — without violating I-03/I-05.

#### agentfence + vibeguard (Phase 3 — enforcement edges)

Both are deterministic, offline policy gates. Proposal: compile a substrate's
invariant facet into their policy languages — agentfence at the runtime MCP edge,
vibeguard at the pre-merge code edge — so a single substrate declaration produces
consistent enforcement at every boundary. Both already emit weaver-spec audit /
report artifacts, so the wiring exists.

#### skdr-eval (Phase 2 — the measurement that makes this real)

This is the keystone. skdr-eval is a statistics-grade offline-evaluation library
with trust diagnostics (ESS, Pareto-k, calibration). Proposal: define and
implement `InterpretationDrift` as a first-class estimator — fix a substrate
version, run N×M (runs × models), and report a calibrated stability number with
confidence, not a vibe. This is what separates "Substrate Engineering" from
"better prompts": a falsifiable metric with known error bars.

#### lessonweaver (Phase 4 — closing the loop)

lessonweaver already turns traces into reviewed lessons through a human gate.
Proposal: when drift diagnostics or denial traces recur against a domain,
lessonweaver proposes a *substrate amendment* (a new invariant, a tightened
admissible state) as a reviewable candidate. The substrate becomes a living
artifact that hardens as the system learns — the closed learning loop, applied
to meaning rather than to skills.

## Suggested phasing

1. **Phase 1 — Name it (weaver-spec only).** Extended contracts + concept doc.
   Reversible, no behavior, no Core change.
2. **Phase 2 — Make it measurable and authorable.** skdr-eval drift metric +
   intentflow emit target + agent-kernel substrate-as-policy-input. Proves the
   idea is real before any wide rollout.
3. **Phase 3 — Enforce consistently.** ChainWeaver / contextweaver / agentfence /
   vibeguard adopt the substrate at their boundaries.
4. **Phase 4 — Evolve it.** lessonweaver feeds learned amendments back through
   review.

Only promote `DomainSubstrate` from Extended to Core (via ADR) **after** Phase 2
shows real adopters and a stable shape.

## Non-goals and risks

> [!NOTE]
> - **Do not over-claim determinism.** The original argument's "pick the exact
>   token every time" is marketing. The honest Weaver framing is: deterministic
>   *execution* (already true) plus *measured* interpretation drift (Phase 2).
>   Keep `DeterminismLevel`'s `FULL/PARTIAL/NONE` honesty; do not advertise
>   token-level determinism the stack cannot guarantee.
> - **Core-contract weight.** A Core change touches six artifacts and ripples to
>   contextweaver, agent-kernel, and ChainWeaver. Starting in Extended avoids
>   destabilizing Core for an unproven shape (I-04).
> - **Scope creep into runtime logic in weaver-spec.** weaver-spec stays
>   docs+contracts only. All enforcement and measurement live in sibling repos.
> - **Avoid reinventing ontology tooling.** The differentiator is the *runtime
>   enforcement + measurement* the stack already has, not a new ontology editor.

## Open questions

1. Name and home: `DomainSubstrate` vs `SemanticSubstrate`; Extended vs (later)
   Core; one object or a small family (one per facet)?
2. Is intentflow the canonical authoring surface, or should a substrate be
   authorable independently of intentflow?
3. What is the precise, calibrated definition of `InterpretationDrift` in
   skdr-eval, and what is a meaningful target value?
4. How does a substrate version interact with existing contract `VERSIONING.md`
   rules and the `attest_flow()` attestation in ChainWeaver?
5. Does any of this warrant a new lifecycle phase, or does it sit *under* the
   existing five phases as a cross-cutting input?

## Next steps

- Socialize this map with maintainers of each repo.
- If there is appetite, open a weaver-spec issue for the Phase 1 Extended
  contracts and a skdr-eval issue for the Phase 2 drift metric.
- Promotion to Core, if it happens, goes through the ADR process — not this doc.
