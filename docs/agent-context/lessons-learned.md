# Lessons Learned

> Consult this file when you need to record a new reusable lesson or understand how lessons are promoted.
> For the current rules derived from lessons, see [AGENTS.md](../../AGENTS.md) and
> [docs/agent-context/invariants.md](invariants.md).

---

## Failure-capture workflow

When a mistake is identified (during review, from a reverted commit, or from a CI failure):

1. **Determine if the mistake is reusable** — Could this pattern recur in a different file or context? If yes, continue. If it was a one-time typo or data error, fix it and stop.
2. **Generalize the lesson** — Extract the underlying pattern, not just the specific instance.
3. **Record the generalized lesson** — Add it to the "Known patterns" index below.
4. **Promote to a rule if warranted** — If the lesson is important enough to be a hard constraint, add it to [invariants.md](invariants.md) (forbidden shortcuts) and reference it from `AGENTS.md` if it is cross-cutting.
5. **Do not keep incident details** — This file captures patterns, not incident logs. Omit commit hashes, dates, and person-specific context.

### Criteria for inclusion

A lesson belongs here if:

- The mistake pattern could realistically recur across different files or contexts.
- Understanding the pattern helps prevent future occurrences.

A lesson does **not** belong here if:

- It was a one-time factual error.
- It is already fully captured as a forbidden shortcut in [invariants.md](invariants.md).
- It requires incident-specific context to be useful.

---

## Known patterns (derived rules live elsewhere)

1. **Description-constraint contradictions** — Schema descriptions that assert something contradicted by structural constraints. → Rule in [invariants.md](invariants.md) (forbidden shortcuts) and [contracts-json.instructions.md](../../.github/instructions/contracts-json.instructions.md).
2. **Diagram-boundary contradictions** — Mermaid diagrams showing data flow that contradicts the artifact ownership table. → Rule in [invariants.md](invariants.md) and [docs.instructions.md](../../.github/instructions/docs.instructions.md).
3. **Aspirational-as-current prose** — Documentation asserting features that are not enforced by schema or code. → Clarification in [AGENTS.md](../../AGENTS.md) (domain clarifications).

---

## How lessons get promoted

```text
Incident → generalized lesson (this file) → forbidden shortcut (invariants.md) → rule (AGENTS.md)
```

Not all lessons become rules. A lesson becomes a forbidden shortcut when it represents a pattern that has recurred or has high blast radius if it recurs. A forbidden shortcut becomes a rule in `AGENTS.md` when it is cross-cutting (applies globally, not just to one path or file type).

---

## Update triggers

Update this file when:

- A new reusable mistake pattern is discovered
- An existing lesson is promoted to a forbidden shortcut in [invariants.md](invariants.md)
- The failure-capture workflow itself changes
