# Copilot Instructions — weaver-spec

## Review priorities (in order)

1. **All required artifacts present in same PR.** Core contract changes must update: JSON schema, Python dataclass, sample payload, roundtrip test, CHANGELOG, version bump (`version.py` + `pyproject.toml`). Missing any artifact fails review.
2. **Invariants hold.** Verify I-01 through I-07 in `docs/INVARIANTS.md` are not violated.
3. **Boundaries respected.** Check the artifact ownership table in `docs/BOUNDARIES.md` for changes affecting data flow between layers.

## Critical rules

- This repo is **docs + contracts only**. Never add runtime logic, CLI tools, or helper utilities.
- JSON schemas are the source of truth. Python types must mirror them exactly — same fields, types, required/optional status.
- Core contract changes affect sibling repos (contextweaver, agent-kernel, ChainWeaver). The PR description must flag cross-repo impact.
- Breaking Core changes require the ADR process (`CONTRIBUTING.md`), not a direct PR.

## Authority hierarchy

When documents conflict: `docs/INVARIANTS.md` → `docs/BOUNDARIES.md` → `docs/ARCHITECTURE.md` → everything else.

## Review expectations

- Review code changes and agent-facing docs together when one affects the other.
- PRs that change workflows, invariants, architecture intent, review conventions, or path-specific rules must trigger doc review.
- Do not invent conventions not grounded in canonical docs or repository evidence.
- Use the validation commands from `AGENTS.md` and `CONTRIBUTING.md` — do not substitute alternatives.
- Surface contradictions or stale docs explicitly. Do not silently work around authority conflicts.
- Invariants take priority over cleanup, simplification, or local refactors.

## Deeper context

See `AGENTS.md` for the full shared instruction set, repo map, definition of done, validation commands, and documentation map. Path-specific rules are in `.github/instructions/`.
