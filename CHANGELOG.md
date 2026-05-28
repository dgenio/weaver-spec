# Changelog

All notable changes to weaver-spec are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The spec and contracts follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- **v0.6.0 — Extended schema retrofit + signing + OpenTelemetry mapping.**
  Bumps `CONTRACT_VERSION` and the Python package to `0.6.0` and lands three
  related issues in one PR.
  - **JSON Schemas for the seven original Extended metadata types**
    (`TelemetryHint`, `SchemaFingerprint`, `RedactionPolicy`, `UIHint`,
    `RiskAssessment`, `ExtendedFrameMetadata`,
    `ExtendedSelectableItemMetadata`). Their `$id` URIs live under the
    `extended/` namespace; `ExtendedFrameMetadata` and
    `ExtendedSelectableItemMetadata` reference their child schemas via
    `$ref` resolved by the existing local schema store. The
    Python-source-of-truth carve-out in `AGENTS.md` and
    `docs/agent-context/workflows.md` is removed. Closes #46.
  - **`CapabilityTokenSignature` Extended contract** for RFC 8785 JCS
    canonicalization plus `ed25519` / `es256` detached signatures, attached
    to a `CapabilityToken` under the namespaced extension key
    `x_weaver_signature` (Core schema unchanged). New ADR
    `docs/adr/001-capability-token-signing.md` and verification guide
    `docs/SIGNING.md`. Two new sample payloads
    (`capability_token_signature.json`, `capability_token_signed.json`).
    The `AGENTS.md` "Domain clarifications" entry for `CapabilityToken` is
    updated to reflect that the word "signed" is accurate when the
    extension is present. Closes #44.
  - **`OtelTraceMapping` Extended contract** carrying W3C Trace Context
    identifiers and OTel GenAI semconv attributes
    (`gen_ai.operation.name`, `gen_ai.tool.name`, `gen_ai.agent.id`,
    `gen_ai.agent.name`, `gen_ai.system`). New normative mapping doc
    `docs/OTEL_MAPPING.md` (pinned to OTel semconv snapshot `1.30.0`) with
    a CI-validated inline payload, plus a sample payload. Closes #47.
  - Tests: `test_extended.py` gains `TestCapabilityTokenSignature` and
    `TestOtelTraceMapping` (8 + 9 cases each, including JCS/algorithm
    registry enforcement, W3C trace/span hex-format checks, and all five
    OTel span kinds). `test_extended_schema_alignment.py` adds the nine
    new schemas to its parametrized list plus six new negative cases
    (unknown signing algorithm, unknown canonicalization, signed
    CapabilityToken validation, invalid OTel span kind, malformed
    `trace_id`, missing fingerprint required fields).
- `compatibility.yaml` — machine-readable manifest of sibling-repository
  compatibility with each weaver-spec contract version (`contextweaver`,
  `agent-kernel`, `ChainWeaver`). Declares per-repo `status`
  (`verified` / `provisional` / `unverified` / `incompatible`),
  `supported_spec_versions`, `tested_version`, `declaration`, and
  `known_limitations`. The validation logic lives in stdlib-only
  `scripts/validate_compatibility.py` (with a self-test of its rejection
  paths) and runs both in the `validate-compatibility` CI job
  (`.github/workflows/ci.yml`, PyYAML) and locally via the
  `compatibility-manifest` pre-commit hook. It enforces the status
  vocabulary, semver formatting of every version field, that each
  `supported_spec_versions` entry is one of `contract_versions`, that
  `verified`/`provisional` entries carry concrete version and declaration
  references, and that every manifest repo is referenced in
  `docs/VERSIONING.md`; the manifest is also linted by the `yamllint` CI job
  and the pre-commit `yamllint` hook. Closes #57.
- `docs/ECOSYSTEM.md` — derived, informative ecosystem boundary map:
  per-project owns / does-not-own / consumes / emits table, an end-to-end
  lifecycle example, a weaver-spec-vs-individual-repo concern split, and
  compatibility pointers. Points to `docs/BOUNDARIES.md` and
  `docs/LIFECYCLE.md` as canonical and is linked from `README.md`. Closes #62.
- `docs/VERSIONING.md` — filled the compatibility matrix with an explicit
  status vocabulary and a documented declaration process, replacing the
  `— (TBD)` placeholders; references `compatibility.yaml` as the
  machine-readable source of truth. Closes #3.
- Eight new **Extended** cross-project artifact contracts in
  `weaver_contracts.extended`, each shipped with the full artifact set (JSON
  Schema under `contracts/json/extended/`, sample payload under
  `examples/sample_payloads/`, roundtrip test in `tests/test_extended.py`,
  schema-alignment test in the new `tests/test_extended_schema_alignment.py`,
  glossary entry, plus coverage/index regeneration):
  `ReviewArtifact` (Closes #65); `MemoryArtifact` + `SessionHandoff`
  (Closes #56); `LessonCard` + `SkillCard` (Closes #64); `EvaluationArtifact`
  (Closes #67); `ArtifactSafetyGateRequest` + `ArtifactSafetyReport`
  (Closes #63). `EvaluationArtifact` rejects — in both the JSON Schema and at
  Python construction time — a `high_risk` support state paired with a `deploy`
  recommendation (a high-risk evaluation is not deployment evidence).
- `contracts/json/extended/` — first Extended JSON Schemas (8 files). Their
  `$id` URIs live under the `extended/` namespace and are picked up
  automatically by `scripts/generate_contracts_index.py`.
- `docs/ARTIFACT_CONTRACTS.md` — consolidated, informative spec page for the
  cross-project artifact vocabulary: shared envelope, taxonomy, and a
  CI-validated inline example per type.
- `contracts/python/tests/test_extended_schema_alignment.py` — validates every
  Extended sample payload against its Extended schema, with targeted negative
  cases.
- `.pre-commit-config.yaml` — pre-commit hook bundle mirroring the CI gates: `pre-commit-hooks` (trailing whitespace, end-of-file, large file guard, JSON/YAML/TOML/merge-conflict checks), `yamllint`, `markdownlint-cli2`, a local hook running `scripts/check_schema_fields.py`, a local hook running `scripts/generate_contracts_index.py --check`, and a `pre-push`-staged hook that runs the `weaver_contracts` pytest suite. Setup instructions added to `CONTRIBUTING.md`. `pre-commit` and `yamllint` added to `[project.optional-dependencies] dev` in `contracts/python/pyproject.toml`. Closes #14.
- `.yamllint.yml` — yamllint config tuned for GitHub-flavored YAML (relaxed line length, `truthy.check-keys: false` to permit `on:` in workflows).
- CI job `yamllint` in `.github/workflows/ci.yml` — lints `.github/ISSUE_TEMPLATE/`, `.github/workflows/`, `.yamllint.yml`, and `.pre-commit-config.yaml` via `yamllint==1.35.1` so malformed templates fail in CI rather than at GitHub form-render time. Closes #35.
- `.github/prompts/add-contract-field.prompt.md` and `.github/prompts/add-new-schema.prompt.md` — VS Code `.prompt.md` workflow templates encoding the six-artifact rule and the `INVARIANTS.md → BOUNDARIES.md → ARCHITECTURE.md` authority hierarchy for two common Core contract workflows. Referenced from the `AGENTS.md` repo map. Closes #13.
- `docs/DOCS_CONVENTIONS.md` — markup convention distinguishing **normative** (`> [!IMPORTANT]`), **informative** (`> [!NOTE]`), and **example** (fenced code block) content. Conservative initial application to `docs/INVARIANTS.md` and `docs/BOUNDARIES.md`. Linked from `README.md`, `CONTRIBUTING.md` Style Guidelines, and the `AGENTS.md` documentation map. Closes #58.
- `scripts/check_schema_fields.py` — stdlib-only validator that enforces `$id`/`title`/`description`/`required` on every `contracts/json/*.schema.json`. Used by both CI (`validate-schemas` job) and the new pre-commit hook so the two stay in sync.
- Six missing Core sample payloads under `examples/sample_payloads/`:
  `selectable_item.json`, `choice_card.json`, `capability.json`,
  `policy_decision.json`, `handle.json`, `trace_event.json`. All validate
  against their Core JSON schemas; each is exercised by a new
  `Test<X>Payload` schema-validation class in
  `contracts/python/tests/test_json_schema_alignment.py` and a
  `test_from_payload` roundtrip case in
  `contracts/python/tests/test_roundtrip_examples.py`. Closes #11.
- `scripts/generate_coverage_table.py` — stdlib-only build-time generator
  for the schema-to-artifact coverage table. Supports `--check` for CI
  staleness detection. Closes #24.
- `contracts/COVERAGE.md` — auto-generated coverage table covering all 16
  contract types (9 Core + 7 Extended) across JSON schema, Python class,
  sample payload, roundtrip test, and schema validation test artifacts.
- `coverage-table` CI job in `.github/workflows/ci.yml` running
  `python scripts/generate_coverage_table.py --check` so stale tables fail
  the build.
- `docs/INTEGRATION_MAP.md` — concrete cross-repo integration points
  (contextweaver ↔ agent-kernel, agent-kernel → audit log, ChainWeaver →
  contextweaver) with JSON payload snippets at each handoff and explicit
  invariant references. Closes #27.
- README ecosystem map (including AgentFence and VibeGuard as adjacent,
  off-runtime-path tools) and Adoption Paths table. Closes #53.
- `docs/LIFECYCLE.md` — normative five-phase lifecycle contract
  (`route → call → interpret → answer → execute`) defining owner repo,
  inputs, outputs, boundary, and applicable invariants per phase, plus an
  informative "ambiguous cases" section. Closes #54.
- `examples/interoperability/` — minimal happy-path
  (`happy_path.md`: RoutingDecision → PolicyDecision(allow) →
  Frame + Handle → TraceEvent chain) and denied-path
  (`denied_path.md`: RoutingDecision → PolicyDecision(deny) → TraceEvent;
  no Frame, no Handle) walkthroughs using inline `<!-- schema: X -->`
  markers so existing CI validates every payload. Closes #55.

### Changed

- `.github/workflows/ci.yml` — the `validate-schemas` job now calls `scripts/check_schema_fields.py` instead of an inline `python -c` block (single source of truth for the schema-required-fields check; no behavior change).
- `markdownlint` CI job now globs `examples/**/*.md` recursively (was `examples/*.md`) and adds `.github/**/*.md` so prompt templates and instruction files are linted alongside the rest of the repo.
- README Quick Navigation gained links to `docs/LIFECYCLE.md`,
  `docs/INTEGRATION_MAP.md`, `contracts/COVERAGE.md`, and
  `examples/interoperability/`.
- `AGENTS.md` repo map updated with `.github/prompts/`, `.pre-commit-config.yaml`, `.yamllint.yml`, `docs/DOCS_CONVENTIONS.md`, `examples/interoperability/`, `docs/LIFECYCLE.md`, `docs/INTEGRATION_MAP.md`, `scripts/generate_coverage_table.py`, and `contracts/COVERAGE.md`.
- `scripts/check_schema_fields.py` now scans `contracts/json/**/*.schema.json`
  recursively so Extended schemas are validated alongside Core.
- `.github/workflows/ci.yml` — the walkthrough inline-JSON validator resolves
  schemas recursively (`contracts/json/**`), so inline examples can reference
  Extended schemas.
- `AGENTS.md` ("schemas lead" section, repo map, documentation map) and
  `docs/agent-context/workflows.md` (Extended-contract workflow) updated to
  reflect that Extended schemas now live under `contracts/json/extended/`; the
  original 7 Extended metadata types remain Python-source-of-truth pending #46.
- `contracts/json/README.md` documents the `extended/` subdirectory.
- Regenerated `contracts/COVERAGE.md` (now 24 contract types) and
  `well-known/contracts.json` (Extended entries populated; `contract_version`
  → 0.5.0).
- `README.md` — corrected the stale "Current contract version" value
  (`0.3.0` → `0.5.0`) to match `weaver_contracts.version.CONTRACT_VERSION`,
  and linked the new `docs/ECOSYSTEM.md` from the ecosystem map and Quick
  Navigation.

**No Core contract changes** — no Core JSON schema fields added or removed, no
Core Python dataclass surface changes. This cycle adds eight additive
**Extended** contract types, which bumps `CONTRACT_VERSION` 0.4.0 → 0.5.0
(MINOR, per the Extended-contract workflow). No sibling-repo coordination is
required: the new types are optional and opt-in.

---

## [0.4.0] — 2026-05-20

### Added

- `CHARTER.md` — governance roles (Contributor / Reviewer / Maintainer / Core Maintainer), decision flow, Working Group lifecycle, and current maintainer roster. Linked from `README.md` and `AGENTS.md`. Closes #42.
- `docs/SECURITY_MAPPING.md` — alignment map between invariants `I-01`–`I-07` and OWASP LLM Top 10 (2025), MITRE ATLAS, and NIST AI RMF 1.0. Uses "aligned with" wording only. Linked from `SECURITY.md` and `README.md`. Closes #39.
- `docs/DEPRECATIONS.md` — deprecation register and removal policy (≥1 MAJOR retention rule, removal requires ADR). Referenced from `.github/pull_request_template.md` and `CONTRIBUTING.md`. Closes #40.
- `docs/SCHEMA_HOSTING.md` — JSON Schema `$id` URL pattern, current hosting status, immutability rule, and content-addressed index policy.
- `well-known/contracts.json` — content-addressed index of the 9 Core JSON Schemas with SHA-256 per file.
- `scripts/generate_contracts_index.py` — stdlib-only generator for `well-known/contracts.json`. `--check` mode used in CI to fail on stale index.
- CI job `validate-contracts-index` in `.github/workflows/ci.yml` that runs `python scripts/generate_contracts_index.py --check`. Closes #41.

### Changed

- `.github/workflows/publish.yml` — adds `attestations: true` to the PyPI publish step and `attestations: write` permission, so each release emits a PEP 740 Sigstore-signed SLSA build provenance attestation. `SECURITY.md` and `contracts/python/README.md` document the `sigstore verify` flow for adopters. Closes #38.
- `.github/pull_request_template.md` — adds a Deprecations section linking to `docs/DEPRECATIONS.md`.
- `.github/workflows/ci.yml` and `CONTRIBUTING.md` — markdownlint command extended to lint `CHARTER.md`.

**No Core contract changes** — JSON Schemas, Python types, and existing sample payloads are unchanged.

---

## [0.3.0] — 2026-05-19

### Added

- `examples/failure_scenarios.md` — three failure-path walkthroughs (routing failure, authorization denial, partial execution failure) with contract payloads at every boundary. Closes #18.
- `examples/multi_agent_orchestration.md` — two-agent ChainWeaver-coordinated walkthrough showing the full `RoutingDecision` → `Frame` → re-routing cycle. Closes #22.
- `examples/partial_capability_routing.md` — partial-match routing walkthrough with three overlapping candidates and a ranked `ChoiceCard`. Closes #26.
- `docs/SEQUENCE_DIAGRAMS.md` — three new Mermaid sequence diagrams (sections 4 — 6) for the routing-failure, authorization-denial, and partial-execution-failure paths. Diagrams use the same scenarios as `examples/failure_scenarios.md`. Closes #25.
- CI step in `.github/workflows/ci.yml` that extracts inline JSON payloads from the new walkthroughs (and `docs/SEQUENCE_DIAGRAMS.md`) and validates each against its declared schema in `contracts/json/` using `jsonschema`, with `format`-keyword enforcement (e.g., `date-time`) and a non-zero-marker guard to fail loud on accidental marker removal. Blocks merges on walkthrough/contract drift.
- `docs/QUICKSTART.md` — quick-start integration guide with Python and JS/TS code, schema validation patterns, and one integration snippet per sibling repo (contextweaver, agent-kernel, ChainWeaver). No runtime dependencies added. Closes #19.
- `docs/CONTRACT_REFERENCE.md` — single-page field reference for all 16 contract types (9 Core + 7 Extended) with per-field type/required/description tables, source-of-truth links, and per-Extended-type usage guidance, Core relationship, and inline JSON example. Supersedes #21. Closes #20.
- `docs/FAQ.md` — eight new task-oriented entries covering capability registration, Extended metadata composition, language-agnostic schema validation, version-mismatch handling, telemetry, the Core-field proposal workflow, the Frame-vs-Handle distinction, and spec-conformance testing. Closes #23.
- `README.md` — Quick Navigation table now links to `docs/QUICKSTART.md` and `docs/CONTRACT_REFERENCE.md`.

**No Core contract changes** — JSON Schemas, Python types, and existing sample payloads are unchanged.

---

## [0.2.0] — 2026-04-11

### Added

- GitHub Issue Forms (`.github/ISSUE_TEMPLATE/`): structured intake for bug reports,
  feature requests, and ADR proposals (breaking contract changes). Blank issues
  disabled; Discussions available as an escape hatch.
- `.markdownlint.json` config file at repo root (disables MD013, MD033, MD041; enables MD024 siblings-only for changelog headings).
- `docs/adr/README.md` — ADR directory README: scope, naming convention (`NNN-short-title.md`), and link to `CONTRIBUTING.md` process.
- `docs/adr/template.md` — Fillable ADR template with eight required sections (Status, Context, Decision, Consequences, Affected Contracts, Migration Path, Cross-Repo Impact).
- `CONTRIBUTING.md` — ADR section now links to template and README; breaking-change PR checklist explicitly requires an ADR file.
- `AGENTS.md` — Repo map updated with `docs/adr/` entry.
- Extended contract sample payloads (`examples/sample_payloads/`): `extended_frame_metadata.json`, `extended_selectable_item_metadata.json`, `redaction_policy.json`, `risk_assessment.json`, `schema_fingerprint.json`, `telemetry_hint.json`, `ui_hint.json`.
- `contracts/python/tests/test_extended.py` — unit tests covering all Extended contract types.

### Changed

- CI Markdown lint job renamed and reconfigured: `markdown-lint` → `markdownlint` — inline `--disable` flags replaced by `.markdownlint.json`.
- CI markdownlint glob widened from `docs/*.md` to `docs/**/*.md` to cover `docs/adr/` and `docs/agent-context/` subdirectories.

### Fixed

- Markdown lint violations corrected across all linted files (MD031, MD032, MD036, MD040, MD060).
- Corrected SHA-256 `content_hash` length in Extended sample payloads (was 63 hex chars, now correct 64).
- `pytest-cov` coverage threshold raised from 64% to 80% following Extended contract test additions.

---

## [0.1.1] — 2026-03-13

### Added

- `mypy --strict` type checking added to CI and dev workflow (closes #12).
- `pytest-cov` coverage tracking with 64% threshold (scope expansion of #12). Raise to 80% once Extended tests land (#17).
- Agent-facing documentation system:
  - `AGENTS.md` — shared entrypoint for all coding agents (rules, repo map, authority hierarchy, forbidden behaviors, design decisions not to reopen).
  - `docs/agent-context/architecture.md` — thin pointer to canonical architecture and boundary docs.
  - `docs/agent-context/workflows.md` — contract change workflows, validation commands, commit conventions, documentation governance.
  - `docs/agent-context/invariants.md` — forbidden shortcuts, must-preserve constraints, safe-vs-unsafe simplification table.
  - `docs/agent-context/lessons-learned.md` — failure-capture workflow and known pattern index.
  - `docs/agent-context/review-checklist.md` — self-review and maintainer-review checklist with checkbox items.
- GitHub Copilot instructions:
  - `.github/copilot-instructions.md` — compact review-priority entrypoint for GitHub code review.
  - `.github/instructions/contracts-json.instructions.md` — path-scoped rules for `contracts/json/**`.
  - `.github/instructions/contracts-python.instructions.md` — path-scoped rules for `contracts/python/**`.
  - `.github/instructions/docs.instructions.md` — path-scoped rules for `docs/**`.
- Claude Code instructions:
  - `.claude/CLAUDE.md` — Claude-specific operating behavior, contradiction handling, lesson promotion workflow.
- CI / process:
  - `.github/pull_request_template.md` — PR checklist enforcing six-artifact rule, invariant verification, and cross-repo impact flagging.
  - `.github/CODEOWNERS` — blanket auto-assignment (`* @dgenio`) for PR review.

### Fixed

- `docs/FAQ.md` — corrected ID format claim from "UUIDs or stable strings" to "non-empty strings (`minLength: 1`)" to match JSON schema authority.
- `CONTRIBUTING.md` — added missing Markdown Lint section with exact `markdownlint-cli` command matching CI configuration.

---

## [0.1.0] — 2026-03-08

### Added

- Initial spec documentation:
  - `docs/VISION.md` — problem statement and goals.
  - `docs/ARCHITECTURE.md` — three-layer model with Mermaid diagram.
  - `docs/BOUNDARIES.md` — explicit kernel/contextweaver boundary decision.
  - `docs/INVARIANTS.md` — non-negotiable invariants.
  - `docs/GLOSSARY.md` — canonical term definitions.
  - `docs/SEQUENCE_DIAGRAMS.md` — Mermaid sequence diagrams for all adoption modes.
  - `docs/VERSIONING.md` — semantic versioning rules and compatibility matrix.
  - `docs/ADOPTION_GUIDE.md` — per-component and combination adoption guides.
  - `docs/FAQ.md` — frequently asked questions.
- Core JSON Schemas (9): `selectable_item`, `choice_card`, `routing_decision`, `capability`, `capability_token`, `policy_decision`, `frame`, `handle`, `trace_event`.
- Python package `weaver_contracts` 0.1.0:
  - `core.py` — dataclasses for all Core contracts.
  - `extended.py` — optional Extended metadata types.
  - `version.py` — version constants and compatibility helpers.
  - Tests: JSON schema alignment and roundtrip validation.
- Sample payloads for `routing_decision`, `frame_with_handles`, and `capability_token`.
- CI workflows: `ci.yml` (Python tests + schema lint) and `links.yml` (link checker).

[Unreleased]: https://github.com/dgenio/weaver-spec/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/dgenio/weaver-spec/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/dgenio/weaver-spec/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dgenio/weaver-spec/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/dgenio/weaver-spec/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dgenio/weaver-spec/releases/tag/v0.1.0
