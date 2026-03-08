# Invariants and Constraints for Agents

> Consult this file when you need to understand what you must not break, what shortcuts are forbidden,
> and how to distinguish safe simplifications from unsafe ones.
> For the rules themselves, see [AGENTS.md](../../AGENTS.md).
> For the canonical invariant definitions, see [docs/INVARIANTS.md](../INVARIANTS.md).

---

## Hard invariants

Invariants I-01 through I-07 in `docs/INVARIANTS.md` are non-negotiable. Violating any of them makes an implementation non-compliant. Before any Core contract change, verify that your change does not weaken, contradict, or circumvent any invariant.

The invariants most often relevant to contract changes:

| Invariant | What it prevents |
|-----------|-----------------|
| **I-01 / I-05** — LLM and contextweaver never see raw tool output | Adding fields that expose unfiltered data |
| **I-04** — Core contracts are minimal and stable | Adding implementation-specific fields to Core |
| **I-06** — CapabilityTokens are scoped and time-limited | Removing `expires_at`/`single_use` constraints |

Always check the full list. The invariants above are highlighted because they are the ones most frequently relevant to contract editing, not because the others are less binding.

---

## Forbidden shortcuts

These patterns are confirmed traps. Each is a generalized rule — not tied to any single incident.

### Schema descriptions must not contradict structural constraints

Every `description` string in a JSON schema must be consistent with the structural constraints (`required`, `enum`, `minLength`, `type`, etc.) on the same field. Read both before writing either.

- Do not say a field is "required" in a `description` if the field is not in the `required` array.
- Do not claim extensibility (e.g., "additional values may be used") when an `enum` constraint is present on the same field.

### Diagrams must not contradict boundaries

Any visual representation of data flow must match the artifact ownership table in `docs/BOUNDARIES.md`. The table is canonical; the diagram is derived. Do not modify a Mermaid diagram without verifying it against the table.

### Never weaken schema constraints without an ADR

Removing a `minLength`, loosening an `enum`, dropping a `required` field, or widening a type — these are high-risk changes that affect consumers even when existing payloads remain valid. They require the ADR process regardless of whether they meet the formal "breaking change" definition in `CONTRIBUTING.md`.

### Never add non-universal fields to Core

A field belongs in Core only if every adopter needs it. If a field is useful to one implementation or one use case, it belongs in Extended. When reviewing a Core contract change, ask: "Would an adopter using *only* contextweaver or *only* agent-kernel need this field?" If not, move it to Extended.

---

## Must-preserve constraints

These constraints must not be removed or weakened without an ADR:

- `minLength: 1` on all ID fields
- `additionalProperties: true` on all schemas
- `anyOf` constraint on CapabilityToken requiring `expires_at` or `single_use` (enforces I-06)
- `required` arrays on all schemas — never remove a field from `required` without an ADR

---

## Safe vs unsafe simplifications

| Simplification | Safe? | Why |
|---------------|-------|-----|
| Add an optional field to a schema | Yes | `additionalProperties: true` makes additive changes backward-compatible |
| Add a new enum value | Yes | Existing values remain valid |
| Remove an optional field from a schema | **No** | Affects Python API consumers and downstream readers; requires ADR even though payloads remain valid |
| Remove a required field | **No** | Breaking change; requires ADR |
| Change a field's type | **No** | Breaking change; requires ADR |
| Refactor Python code without changing fields | Yes | As long as field names, types, and required status still match the schema |
| Add a new Extended type | Yes | Extended types don't affect Core stability |
| Merge two separate contract types | **No** | Changes the interface contract; requires ADR |

---

## Update triggers

Update this file when:
- A new invariant is added to `docs/INVARIANTS.md`
- A new forbidden pattern is identified (see failure-capture workflow in `lessons-learned.md`)
- The safe-vs-unsafe classification changes due to a versioning policy change
