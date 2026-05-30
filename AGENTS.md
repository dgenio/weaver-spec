# Agent Instructions — weaver-spec

This file is the shared source of truth for any coding agent working in this repository.
Read this file first. Consult the linked supporting docs when you need deeper context.

---

## Purpose and scope

This repository is **documentation + contracts only**.

- It defines the shared interfaces for three sibling repositories: **contextweaver** (routing), **agent-kernel** (execution), and **ChainWeaver** (orchestration).
- It contains JSON Schemas (language-agnostic source of truth), a Python `weaver_contracts` package (stdlib dataclasses mirroring the schemas), specification docs, and examples.
- **Never add runtime logic, adopter-facing CLI tools, adopter-facing helper utilities, or business logic to this repository.** Validation is limited to construction-time checks in dataclass `__post_init__`.
- **Build-time spec-maintenance tooling is permitted** under `scripts/`, narrowly scoped: stdlib-only Python that consumes the spec and emits or validates artifacts checked into this repo (e.g., the content-addressed schema index). Such tooling must not be imported by `weaver_contracts` and must not be published to PyPI. Any new script must be added to the repo map below with that scope explicitly stated.
- **The conformance suite under `conformance/` is build-time / CI tooling**, not runtime code. Unlike `scripts/` it may use the schema-validation/signing dependencies (`jsonschema`, `referencing`, `PyYAML`, `jcs`, `cryptography`), because it defines what "spec-compliant" means as a runnable check (positive/negative corpus + executable invariant assertions + TraceBundle signature verification). The same constraints apply: it is never imported by `weaver_contracts` and never published. See [docs/CONFORMANCE.md](docs/CONFORMANCE.md).

---

## Repo map

| Path | Contains | When to consult |
|------|----------|-----------------|
| `.github/pull_request_template.md` | PR checklist (six-artifact rule, invariants, cross-repo impact) | Opening or reviewing any PR |
| `.github/ISSUE_TEMPLATE/` | Issue forms (bug report, feature request, ADR proposal) | Triaging or filing issues; understanding required intake fields |
| `.github/prompts/` | VS Code `.prompt.md` templates encoding the six-artifact rule (add field, add schema) | Driving a Core contract change end-to-end without re-reading the full spec |
| `.github/CODEOWNERS` | Auto-assignment rules for PR review | Adding new paths or reviewers |
| `.pre-commit-config.yaml` | Pre-commit hook bundle mirroring the CI gates (JSON/YAML/markdown lint, contracts-index freshness, pytest on push) | Onboarding a new contributor; adding a new local validation gate |
| `.yamllint.yml` | yamllint config tuned for GitHub-flavored YAML (issue forms, workflows) | Adding new YAML files or adjusting workflow style |
| `contracts/json/` | Core JSON Schemas (Draft 2020-12) | Adding or modifying Core contract definitions |
| `contracts/json/extended/` | Extended JSON Schemas (Draft 2020-12) | Adding or modifying Extended contract definitions |
| `contracts/python/src/weaver_contracts/core.py` | Core contract dataclasses (9 types) | When schemas change — must update in same PR |
| `contracts/python/src/weaver_contracts/extended.py` | Extended metadata types | Adding optional metadata contracts |
| `contracts/python/src/weaver_contracts/version.py` | `CONTRACT_VERSION` constant | Every version bump |
| `contracts/python/pyproject.toml` | Package build config | Every version bump |
| `contracts/python/tests/` | Roundtrip + schema alignment tests | Every contract change |
| `examples/sample_payloads/` | Example JSON payloads | Every new or changed schema |
| `examples/interoperability/` | Minimal happy-path and denied-path walkthroughs linking the Core contracts | When you need a tiny end-to-end illustration of contract handoffs |
| `docs/` | Specification documents | When changing behavior, boundaries, or invariants |
| `docs/LIFECYCLE.md` | Five-phase lifecycle (route → call → interpret → answer → execute) — owner, inputs, outputs, boundary per phase | When reasoning about phase ownership or phase transitions |
| `docs/INTEGRATION_MAP.md` | Concrete inter-repo handoff points with JSON payloads at each boundary | When adding or reviewing cross-repo contract crossings |
| `docs/adr/` | Architecture Decision Records for breaking changes | When proposing or reviewing a breaking Core contract change |
| `docs/agent-context/` | Agent-oriented supporting docs | When you need workflow detail, invariant context, lessons learned, or a review checklist |
| `scripts/generate_coverage_table.py` | Build-time tooling (stdlib only) that regenerates `contracts/COVERAGE.md` from the filesystem | When adding a new contract type, sample payload, or test class |
| `scripts/validate_compatibility.py` | Build-time tooling (stdlib only — no YAML parser) holding the `compatibility.yaml` validation logic + self-test; callers (the `validate-compatibility` CI job and the `compatibility-manifest` pre-commit hook) parse the YAML and call `validate()` | When changing the compatibility manifest's required fields or validation rules |
| `contracts/COVERAGE.md` | Auto-generated artifact coverage table (JSON Schema / Python class / payload / roundtrip / schema test per type) | Re-read after any contract artifact change; CI fails if stale |
| `docs/DEPRECATIONS.md` | Deprecation register (≥1 MAJOR retention rule) | Any PR that deprecates or removes a field, type, or constraint |
| `docs/SCHEMA_HOSTING.md` | `$id` URL policy and content-addressed index policy | When changing schema `$id` URIs or the index format |
| `well-known/contracts.json` | Generated content-addressed schema index (SHA-256 per file) | Regenerate via `scripts/generate_contracts_index.py` after any `contracts/json/` change |
| `compatibility.yaml` | Machine-readable sibling-repo compatibility manifest (human-readable view in `docs/VERSIONING.md`). Validated by the `validate-compatibility` CI job | When a sibling repo declares or changes its supported spec versions |
| `scripts/` | Build-time, stdlib-only utilities (e.g., index generator, coverage table generator). Not runtime code. | When the build-time tooling itself changes |
| `conformance/` | Build-time / CI conformance suite: `run.py` runner, `corpus.yaml` (positive + negative payloads), `invariants.yaml` (executable I-01/I-02/I-04/I-06 assertions), negative fixtures, and a signed TraceBundle fixture + test keyring. Consumes the schema-validation/signing deps; never imported by `weaver_contracts`, never published. | When changing what spec-compliance verifies, or adding fixtures/invariant checks |
| `CHARTER.md` | Governance roles, decision flow, Working Groups | When governance roles or process change |

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

Extended contracts define JSON Schemas under `contracts/json/extended/`. The Python dataclass in `extended.py` must mirror its schema (same as Core).

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

- **Breaking changes** to Core contracts require the ADR process: issue → 3-day discussion → PR with version bump + CHANGELOG + compatibility matrix update. See `CONTRIBUTING.md` and [`docs/adr/README.md`](docs/adr/README.md).
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

**CapabilityToken:** The Core token remains a plain data structure. As of v0.6.0 the spec defines an Extended detached-signature contract (`CapabilityTokenSignature`, attached under `x_weaver_signature`) per [ADR 001](docs/adr/001-capability-token-signing.md) — the word "signed" is accurate when that extension is present. Signing is opt-in in v0.x; do not add signature fields or cryptographic logic to the Core schema, and do not invent alternative signature shapes — use the Extended contract.

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

Run all five checks before submitting a PR:

```bash
# 1. Python tests (with coverage)
cd contracts/python
pip install -e ".[dev]"
pytest --cov --cov-report=term-missing

# 2. Type checking
mypy src/

# 3. JSON schema validation (required fields + valid JSON)
cd ../..
python scripts/check_schema_fields.py

# 4. Contracts index freshness — regenerate first if any contracts/json/ file changed
python scripts/generate_contracts_index.py --check

# 5. Markdown lint
# See CONTRIBUTING.md "Markdown Lint" section for the canonical command.

# 6. Conformance suite (positive/negative corpus + invariants + signature checks)
python conformance/run.py
```

Or, if pre-commit is installed (recommended): `pre-commit run --all-files` runs checks 3–5 automatically. Add `pre-commit install --hook-type pre-push` to also gate check 1 on push.

---

## Commit conventions

Prefixes: `docs:`, `contracts:`, `ci:`, `fix:`.

For mixed changes, use the prefix for the most impactful change. Mention the secondary scope in the commit body.

---

## Documentation map

| File | Scope |
|------|-------|
| `AGENTS.md` *(this file)* | Primary agent entrypoint — rules, navigation, authority |
| [CHARTER.md](CHARTER.md) | Governance roles, decision flow, Working Groups |
| [docs/SECURITY_MAPPING.md](docs/SECURITY_MAPPING.md) | Alignment map between invariants and OWASP / MITRE ATLAS / NIST AI RMF |
| [docs/DEPRECATIONS.md](docs/DEPRECATIONS.md) | Deprecation register and removal policy |
| [docs/SCHEMA_HOSTING.md](docs/SCHEMA_HOSTING.md) | `$id` URL pattern, immutability rule, content-addressed index |
| [docs/DOCS_CONVENTIONS.md](docs/DOCS_CONVENTIONS.md) | Markup convention for normative requirements vs informative notes vs examples |
| [docs/ARTIFACT_CONTRACTS.md](docs/ARTIFACT_CONTRACTS.md) | Cross-project Extended artifact vocabulary (memory, session handoff, lesson/skill cards, evaluation, safety gate, failure case) |
| [docs/EXECUTION_BOUNDARY.md](docs/EXECUTION_BOUNDARY.md) | Selection ↔ execution boundary Extended contracts (ExecutionCandidate, CompiledFlow, ExecutionRoutingDecision, ExecutionFeedback) |
| [docs/TRACE_BUNDLE.md](docs/TRACE_BUNDLE.md) | TraceBundle Extended contract: end-to-end audit-chain envelope (inlines RoutingDecision + PolicyDecisions + Frames + Handles + TraceEvents; optional JCS signature) |
| [docs/CONFORMANCE.md](docs/CONFORMANCE.md) | Conformance suite: what spec-compliance checks (positive/negative corpus, executable invariant assertions, TraceBundle signature verification) and how siblings adopt the reusable workflow |
| [docs/ECOSYSTEM.md](docs/ECOSYSTEM.md) | Derived ecosystem boundary map (owns/consumes/emits per project, end-to-end lifecycle); points to BOUNDARIES.md/LIFECYCLE.md as canonical |
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
