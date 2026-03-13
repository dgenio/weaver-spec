# Claude Instructions — weaver-spec

Read `AGENTS.md` at the repo root for the full shared instruction set.
This file adds Claude-specific operating behavior only.

---

## Critical rules (projected from AGENTS.md)

- This repo is **docs + contracts only**. Never add runtime logic, CLI tools, or helper utilities.
- **Authority hierarchy:** `docs/INVARIANTS.md` → `docs/BOUNDARIES.md` → `docs/ARCHITECTURE.md` → everything else.
- **Every Core contract change must update all six artifacts in the same PR:** JSON schema, Python dataclass, sample payload, roundtrip test, CHANGELOG, version bump.
- **Core contract changes affect sibling repos** (contextweaver, agent-kernel, ChainWeaver). Flag cross-repo impact in the PR description.

---

## Before acting

1. Read `AGENTS.md` for rules, repo map, and authority hierarchy.
2. Read the relevant supporting doc under `docs/agent-context/` for the area of your change (workflows, invariants, lessons learned, review checklist). For architecture and boundary context, consult `docs/ARCHITECTURE.md` and `docs/BOUNDARIES.md` directly.
3. Inspect the files you will modify — verify current structure before assuming patterns.
4. If working in `contracts/json/`, `contracts/python/`, or `docs/`, check the corresponding `.github/instructions/*.instructions.md` file for path-specific rules.
5. Do not infer repo-wide conventions from a single file. Verify against canonical docs.

---

## Safe implementation

- Preserve invariants I-01 through I-07 (`docs/INVARIANTS.md`). These override cleanup, simplification, or refactoring goals.
- Do not invent conventions. Use workflows, commands, and commit prefixes from `AGENTS.md` and `CONTRIBUTING.md`.
- Do not merge or collapse contract types without understanding the architectural reason for their separation. Consult `docs/ARCHITECTURE.md` and `docs/BOUNDARIES.md`, and check the "Design decisions not to reopen" section in `AGENTS.md`.
- Treat scoped rules (`.github/instructions/*.instructions.md`) as mandatory within their declared scope.

---

## Validation before completion

Before proposing that work is done:

1. Verify all required artifacts are updated (see definition of done in `AGENTS.md`).
2. Run the local validation commands from `AGENTS.md`: pytest (with coverage), mypy, JSON schema validation, markdownlint.
3. Check whether the change triggers doc updates — consult the governance table in `docs/agent-context/workflows.md`.
4. Check cross-file consistency: Python fields match JSON schema, sample payloads validate, tests cover changed fields.
5. For Core contract changes, draft the cross-repo impact section for the PR description.

---

## Handling contradictions

- If canonical docs contradict each other, follow the authority hierarchy: `INVARIANTS.md` → `BOUNDARIES.md` → `ARCHITECTURE.md` → rest.
- If code contradicts canonical docs, flag the discrepancy. Do not silently follow the code.
- If a Claude-specific rule contradicts canonical shared docs, canonical docs win. Flag the inconsistency for cleanup.
- If you encounter stale, ambiguous, or conflicting guidance, surface it explicitly — do not silently choose one interpretation.
- When genuinely uncertain after checking all sources, prefer the safer, more conservative option and note the ambiguity.

---

## Lessons learned — capture and promotion

When you encounter a failure pattern or discover a non-obvious constraint during work:

1. **Assess reusability.** Could this pattern recur across different files or contexts? If not, it is a one-off fix — do not promote it.
2. **Generalize.** Extract the underlying pattern, not the specific instance.
3. **Decide placement:**
   - If the lesson is shared and durable → it belongs in canonical docs (`docs/agent-context/lessons-learned.md` or `invariants.md`). Update canonical docs first.
   - If the lesson is Claude-specific operating behavior → it could belong in this file. But verify it is truly Claude-specific.
   - If the lesson is too fresh or narrow → note it in your working context but do not promote it into durable guidance yet.
4. **Promotion order:** Canonical docs first, Claude-specific files second. Never add durable shared knowledge only to Claude files.
5. **Do not promote prematurely.** A single occurrence is an observation. A recurring pattern with reusable prevention guidance is a lesson.

See `docs/agent-context/lessons-learned.md` for the full failure-capture workflow and promotion chain.

---

## Update order

1. Shared durable knowledge → update canonical docs (`AGENTS.md`, `docs/agent-context/*`) first.
2. Claude-specific behavior → update this file second.
3. If a rule in this file becomes shared and durable, promote it to canonical docs and reduce or remove it here.
4. Do not let Claude-specific files become a shadow copy of canonical docs.
