# Agent Instructions — weaver-spec

This file is the shared source of truth for any coding agent working in this repository.
Read this file first. Consult the linked supporting docs when you need deeper context.

---

## Purpose and scope

This repository is **documentation + contracts only**.

- It defines the shared interfaces for three sibling repositories: **contextweaver** (routing), **agent-kernel** (execution), and **ChainWeaver** (orchestration).
- It contains JSON Schemas (language-agnostic source of truth), a Python `weaver_contracts` package (stdlib dataclasses mirroring the schemas), specification docs, and examples.
- **Never add runtime logic, CLI tools, helper utilities, or business logic to this repository.** Validation is limited to construction-time checks in dataclass `__post_init__`.

---

## Repo map

| Path | Contains | When to consult |
|------|----------|-----------------|
| `.github/pull_request_template.md` | PR checklist (six-artifact rule, invariants, cross-repo impact) | Opening or reviewing any PR |
| `.github/ISSUE_TEMPLATE/` | Issue forms (bug report, feature request, ADR proposal) | Triaging or filing issues; understanding required intake fields |
| `.github/CODEOWNERS` | Auto-assignment rules for PR review | Adding new paths or reviewers |
| `contracts/json/` | JSON Schemas (Draft 2020-12) | Adding or modifying contract definitions |
| `contracts/python/src/weaver_contracts/core.py` | Core contract dataclasses (9 types) | When schemas change — must update in same PR |
| `contracts/python/src/weaver_contracts/extended.py` | Extended metadata types | Adding optional metadata contracts |
| `contracts/python/src/weaver_contracts/version.py` | `CONTRACT_VERSION` constant | Every version bump |
| `contracts/python/pyproject.toml` | Package build config | Every version bump |
| `contracts/python/tests/` | Roundtrip + schema alignment tests | Every contract change |
| `examples/sample_payloads/` | Example JSON payloads | Every new or changed schema |
| `docs/` | Specification documents | When changing behavior, boundaries, or invariants |
| `docs/adr/` | Architecture Decision Records for breaking changes | When proposing or reviewing a breaking Core contract change |
| `docs/agent-context/` | Agent-oriented supporting docs | When you need workflow detail, invariant context, lessons learned, or a review checklist |

---

## Authority hierarchy

When documents conflict, higher-ranked sources win:

1. **`docs/INVARIANTS.md`** — non-negotiable rules (I-01 through I-07)
2. **`docs/BOUNDARIES.md`** — responsibility boundaries and artifact ownership
3. **`docs/ARCHITECTURE.md`** — structural model and data flow
4. Everything else (FAQ, Glossary, README, etc.) is supporting

For JSON schema conventions specifically, `contracts/json/README.md` is authoritative.

---

## Source of truth: schemas lead

JSON Schemas are the language-agnostic source of truth for all **Core** contract definitions. Python Core types must mirror them exactly — same field names, same types, same required/optional status. Zero divergence.

Extended contracts currently have no JSON Schemas — the Python dataclasses in `extended.py` are the source of truth for Extended types.

---

## Core contract change scope

Every Core contract change must update **all six artifacts in the same PR**:

1. JSON Schema (`contracts/json/`)
2. Python dataclass (`contracts/python/src/weaver_contracts/core.py`)
3. Sample payload (`examples/sample_payloads/`)
4. Roundtrip test (`contracts/python/tests/test_roundtrip_examples.py`)
5. CHANGELOG entry (`CHANGELOG.md`)
6. Version bump (`version.py` + `pyproject.toml`)

**Cross-repo impact:** Core contract changes affect contextweaver, agent-kernel, and ChainWeaver. Always flag the cross-repo impact in the PR description and consider whether sibling repos need coordinated updates.

See [docs/agent-context/workflows.md](docs/agent-context/workflows.md) for detailed sequences.

---

## Versioning rules

- **Breaking changes** to Core contracts require the ADR process: issue → 3-day discussion → PR with version bump + CHANGELOG + compatibility matrix update. See `CONTRIBUTING.md`.
- **Extended contracts** may have breaking changes in a MINOR version — this is an intentional exception to standard semver. See `docs/VERSIONING.md`.

---

## Invariants and boundaries

Before any Core contract change:

1. **Check invariants I-01 through I-07** in `docs/INVARIANTS.md`. These are non-negotiable. *(Review priority #2)*
2. **Check the artifact ownership table** in `docs/BOUNDARIES.md` for any change affecting data flow between layers. *(Review priority #3)*

Do not restate invariants in new docs or code comments — point to `docs/INVARIANTS.md` instead.

See [docs/agent-context/invariants.md](docs/agent-context/invariants.md) for forbidden shortcuts and constraint-safety rules.

---

## Forbidden behaviors

- **Never add a field to a Core contract** without confirming it is universally needed by all adopters. Proactively move non-universal fields to Extended contracts instead.
- **Never weaken a schema constraint** (remove `minLength`, loosen an enum, drop a `required` entry) without an ADR — constraint loosening affects consumers even when existing payloads remain valid.
- **Never write a schema `description` that contradicts structural constraints** — do not say "required" for a field not in the `required` array, and do not claim extensibility for a field with an `enum` constraint.
- **Never modify a Mermaid diagram without verifying it against the `BOUNDARIES.md` artifact ownership table** — the table is canonical; diagrams are derived.
- **Never describe aspirational features as current** — if a capability (e.g., token signing) is not enforced by a schema constraint or code mechanism, do not assert it as fact.

See [docs/agent-context/invariants.md](docs/agent-context/invariants.md) for the full forbidden-shortcuts list and safe-vs-unsafe simplification table.

---

## Design decisions not to reopen

These separations look like simplification targets but exist for deliberate architectural reasons:

| Separation | Why it exists |
|------------|---------------|
| **ChoiceCard vs RoutingDecision** | ChoiceCards carry only what the LLM needs for selection (no full tool schemas). RoutingDecisions wrap ChoiceCards with state. Merging them would re-introduce context bloat. |
| **Frame vs Handle** | Frames are safe to display. Handles are opaque references to raw artifacts requiring authorization to resolve. Merging them would collapse the safety boundary. |
| **CapabilityToken vs Capability** | Tokens are scoped, time-limited authorization credentials. Capabilities are stable definitions. Merging them would conflate identity with authorization. |

Do not merge, collapse, or "simplify" these types without a spec-level ADR.

---

## Domain clarifications

**CapabilityToken:** Currently a plain data structure. The word "signed" in the Glossary and schema descriptions is aspirational. Signing is an agent-kernel implementation concern, not enforced in this spec. Do not add signature fields or cryptographic logic here.

**ID format:** IDs are any non-empty string (`minLength: 1`). UUIDs are not required. Sample payloads use readable slug-style IDs (e.g., `rd-20260308-001`). If any other docs or examples ever conflict with this, treat the JSON Schemas as the authority.

---

## Code review expectations

- Review code changes and agent-facing docs together when one affects the other.
- Do not invent conventions not grounded in canonical docs or repository evidence.
- Surface contradictions or stale docs explicitly — do not silently work around authority conflicts.
- Invariants take priority over cleanup, simplification, or local refactors.
- PRs that change workflows, invariants, architecture intent, review conventions, or path-specific rules must trigger doc review.
- Use the validation commands listed below and in `CONTRIBUTING.md` — do not substitute alternatives.

---

## Definition of done

A change is ready for review when:

- [ ] All affected artifacts are updated in the same PR (see six-artifact list above)
- [ ] Invariants I-01 through I-07 are not violated
- [ ] No boundary from `docs/BOUNDARIES.md` is crossed without an ADR
- [ ] All local validation checks pass (see below)
- [ ] Cross-repo impact is flagged in the PR description (for Core contract changes)
- [ ] CHANGELOG is updated for any non-patch change

See [docs/agent-context/review-checklist.md](docs/agent-context/review-checklist.md) for the full review checklist.

---

## Local validation

Run all four checks before submitting a PR:

```bash
# 1. Python tests (with coverage)
cd contracts/python
pip install -e ".[dev]"
pytest --cov --cov-report=term-missing

# 2. Type checking
mypy src/

# 3. JSON schema validation
cd ../..
python -c "import json; [json.load(open(f)) for f in __import__('glob').glob('contracts/json/*.schema.json')]"

# 4. Markdown lint
# See CONTRIBUTING.md "Markdown Lint" section for the canonical command.
```

---

## Commit conventions

Prefixes: `docs:`, `contracts:`, `ci:`, `fix:`.

For mixed changes, use the prefix for the most impactful change. Mention the secondary scope in the commit body.

---

## Documentation map

| File | Scope |
|------|-------|
| `AGENTS.md` *(this file)* | Primary agent entrypoint — rules, navigation, authority |
| [docs/agent-context/architecture.md](docs/agent-context/architecture.md) | Pointers to canonical architecture and boundary docs |
| [docs/agent-context/workflows.md](docs/agent-context/workflows.md) | Authoritative commands, change sequences, documentation governance |
| [docs/agent-context/invariants.md](docs/agent-context/invariants.md) | Hard constraints, forbidden shortcuts, safe-vs-unsafe changes |
| [docs/agent-context/lessons-learned.md](docs/agent-context/lessons-learned.md) | Failure-capture workflow and pattern index |
| [docs/agent-context/review-checklist.md](docs/agent-context/review-checklist.md) | Definition-of-done and review gates |

---

## Update policy

- **When to update this file:** When a new shared rule is added, an existing rule changes, or a new agent-context doc is created.
- **When to update supporting docs:** When the topic they own changes. Each supporting doc states its own update triggers.
- **How contradictions are resolved:** The authority hierarchy above governs existing spec docs. Within the agent-facing layer, `AGENTS.md` is canonical; supporting docs elaborate but must not contradict it.
- **Duplication rule:** Each rule has one canonical home. If a rule appears in multiple files, one must be the canonical source and others must be explicit projections or cross-references.
