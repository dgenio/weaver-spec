# Changelog

All notable changes to weaver-spec are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The spec and contracts follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.7.0] - 2026-06-06

### Added

- **Ecosystem front door — "What Is the Weaver Stack?" explainer + launch-post
  draft (#5, #6, #79, #81).** Documentation only; no contract shape changed, so
  no version bump (consistent with this release window's additive-docs practice).
  - New [`docs/WEAVER_STACK.md`](docs/WEAVER_STACK.md): the ecosystem-level
    explainer (#81) — the problem, the layered architecture, and a
    request-path-plus-closed-learning-loop Mermaid diagram **derived** from
    `docs/BOUNDARIES.md`/`docs/ARCHITECTURE.md` (canonical). It is also the
    single source for the reusable **front-door** copy: the org/landing profile
    README block, the per-repo "Part of the Weaver Stack" block (#6), and the
    shared topic set, plus a rollout checklist for the out-of-repo steps
    (org creation #79, sibling-repo edits #6, landing page #5).
  - New [`docs/WEAVER_STACK_LAUNCH.md`](docs/WEAVER_STACK_LAUNCH.md): a drafted
    ecosystem-level launch post (#81), honest about maturity, with the
    cross-repo golden path as the centerpiece proof.
  - Added the "Part of the Weaver Stack" block + explainer links to
    `README.md`, and cross-links from `docs/ECOSYSTEM.md`, `docs/VISION.md`, and
    the `AGENTS.md` documentation map.
- **Closed-loop interchange, firewall seam, and cross-repo golden path (#82, #83,
  #84).** Documentation + examples + conformance fixtures that finalize the
  cross-repo story. No contract shape changed, so no version bump (consistent
  with this release window's additive-docs/tooling practice).
  - **Canonical finding/failure interchange (#83):** `FailureCaseArtifact` (+ the
    `TraceBundle` it references) is documented in `docs/ARTIFACT_CONTRACTS.md` as
    the one shape every producer maps into. Added one sample payload per producer
    — agent-kernel `ActionTrace`, ChainWeaver flow-failure, vibeguard finding,
    AgentFence audit decision — each a positive conformance fixture and
    round-tripped in `test_extended.py`. Producer-specific detail rides on
    namespaced `x_*` `metadata` keys, so no schema change was needed.
  - **Context-firewall / `Frame` seam (#84), ADR 002:** new boundary section in
    `docs/BOUNDARIES.md` naming the canonical `Frame` seam and resolving the "two
    firewalls" overlap; I-05 clarified (canonical Frame path is the default,
    raw-output ingestion is non-canonical) without weakening any constraint. A
    seam negative fixture (`conformance/negative/trace_bundle/i05_seam_*`) asserts
    the statically-checkable half via the existing I-01 check; the behavioral half
    stays a sibling-harness check.
  - **Cross-repo golden path (#82):** new `docs/GOLDEN_PATH.md` documents the
    canonical end-to-end sequence, per-step contract dependencies, and a
    counterpart-status checklist; linked from `ECOSYSTEM.md` and
    `SEQUENCE_DIAGRAMS.md`.
- **Conformance, productized — reference implementation, self-cert badge, and
  public scoreboard (#76, #77, #51).** Three adoption-facing pieces built on the
  now-merged conformance runner (#43/#74). No contract changed, so no version
  bump (consistent with the conformance-suite release window); all of it is
  build-time/CI tooling + docs + an example, never imported by
  `weaver_contracts` and never published.
  - **Runnable reference implementation (#76):**
    `examples/reference_impl/reference_impl.py` constructs every Core artifact
    with `weaver_contracts`, gathers them into a `TraceBundle`, mints a **real**
    ed25519 signature over the RFC 8785 (JCS) canonical form using an *ephemeral*
    keypair, verifies it, validates all six payloads against `contracts/json/`,
    and asserts I-01/I-02 — failing CI if any Core schema drifts. Wired into
    `ci.yml` as the `reference-impl` job, with a "Become Weaver-compatible in 30
    minutes" guide. Placed under `examples/` (example tier) per the repo scope
    rule; it reuses the conformance dev deps and is never published.
  - **`--bundle` / `--emit-result` / `--emit-badge` on `conformance/run.py`:**
    the runner can now conformance-check a single external `TraceBundle` and emit
    a machine-readable result + a shields.io endpoint badge from the same run, so
    a badge can never disagree with the verdict that produced it.
  - **Self-certification badge (#77):** `docs/SELF_CERTIFICATION.md` plus this
    repo's own badge at `docs/badges/weaver-spec.json`, regenerated and
    staleness-checked by CI.
  - **Public scoreboard (#51):** `conformance/scoreboard.py` +
    `conformance/siblings.yaml` registry + `.github/workflows/scoreboard.yml`
    (scheduled). It fetches each registered sibling's published `TraceBundle`,
    runs the conformance pack against it, and renders `docs/scoreboard.md` +
    per-repo badge endpoints. Siblings with no reachable bundle are reported as
    `not-submitted` (never a failure), so the workflow stays green before any
    sibling publishes; participation is opt-in (`docs/SCOREBOARD.md`). Wiring the
    rendered page to GitHub Pages is left as an opt-in repo-admin step.
- **Conformance suite (`conformance/`).** A build-time / CI runner that defines
  what "spec-compliant" means as a runnable check, resolving #43 and #74. No
  contract changed, so no version bump (consistent with this release window's
  additive-tooling practice); this is CI tooling, never imported by
  `weaver_contracts` and never published.
  - `conformance/run.py` validates a **positive corpus** (sample payloads must
    validate), asserts a **negative corpus** is rejected (≥3 fixtures each for
    Frame, RoutingDecision, CapabilityToken, PolicyDecision, TraceEvent — by
    JSON Schema, or by invariant for schema-valid-but-invalid payloads), and
    evaluates `conformance/invariants.yaml` — executable assertions for **I-01,
    I-02, I-04, I-06** (I-03/I-05/I-07 remain layer-behaviour invariants checked
    by sibling harnesses).
  - **TraceBundle integrity verification (#74):** for every `TraceBundle` the
    runner recomputes the RFC 8785 (JCS) canonical form excluding `signature`,
    validates the detached-signature envelope against the
    `CapabilityTokenSignature` schema and algorithm registry, then
    **cryptographically verifies** the signature
    when the `kid` resolves in the keyring. Ships a real ed25519-signed fixture
    (`conformance/fixtures/trace_bundle_signed_valid.json`) with its public key
    in `conformance/keyring/`; unknown-key signatures are reported as *skipped*,
    never as verified.
  - Reusable workflow `.github/workflows/conformance.yml` (siblings adopt with
    one `uses:` line) plus a `conformance` job in `ci.yml`; package test
    `test_conformance.py`; and `docs/CONFORMANCE.md`. The original conformance
    issue #4 was already closed (not planned) and is superseded by this work.
- **Audit-chain and replayable-failure Extended contracts.** Two new
  implementation-neutral Extended contracts, folded into the unreleased `0.6.0`
  set (additive, no Core change, no version bump — consistent with the prior
  Extended-contract additions in this release window).
  - **`TraceBundle`** — a tamper-evident audit-chain envelope that *inlines* one
    request's Core artifacts (`routing_decision`, `policy_decisions`, `frames`,
    `handles`, `trace_events`) so the chain can be canonicalized (RFC 8785 JCS)
    and optionally signed. The full chain is required (a bundle describes a
    complete request); each member is validated against its Core schema via
    `$ref`. The optional `signature` reuses the `CapabilityTokenSignature`
    shape applied to the canonicalized bundle rather than inventing a second
    signature type; an absent signature means unsigned. Redefines no invariant
    (Frames stay free of raw output, I-01; each PolicyDecision is still expected
    to have a matching TraceEvent, I-02). Signed + unsigned sample payloads and
    the normative `docs/TRACE_BUNDLE.md`. Part of #50 — the contract, schema,
    payloads, and an interim I-01/I-02 sample test land here; conformance-runner
    verification of bundle integrity + invariants is tracked in #74 (depends on
    the conformance runner, #43).
  - **`FailureCaseArtifact`** — a small record of a replayable failure
    discovered by fuzzing / property testing / replay, capturing the failed
    `property_name`, reproduction inputs (`seed`, `generator_config`,
    `trace_ref`), `minimized` provenance, and a lifecycle `status`
    (`candidate` / `regression` / `ignored` / `fixed`). It *references* large
    artifacts rather than inlining them and is explicitly reproducible evidence,
    not proof of a bug. Documented in `docs/ARTIFACT_CONTRACTS.md` alongside the
    rest of the cross-project artifact family. Closes #72.
  - JSON Schemas under `contracts/json/extended/`, Python dataclasses in
    `extended.py` (with `__post_init__` enum/non-empty validation mirroring the
    schemas), sample payloads, roundtrip tests in `test_extended.py`,
    schema-alignment + negative tests in `test_extended_schema_alignment.py`.
    `contracts/COVERAGE.md` and `well-known/contracts.json` regenerated.
    Cross-repo impact: Extended/opt-in only — contextweaver, agent-kernel, and
    ChainWeaver may emit these but are not required to; no migration needed.
- **Selection ↔ execution boundary Extended contracts.** Four new
  implementation-neutral Extended contracts describing the boundary between
  selecting a unit of work and executing it, so static routers, the
  `contextweaver` ChoiceCard layer, and feedback-aware external routers can all
  describe a selection the same way instead of each integration inventing its
  own router-to-executor payload.
  - **`ExecutionCandidate`** — something selectable for execution; `candidate_type`
    is a fixed enum (`tool` / `flow` / `capability` / `agent` / `workflow`). A
    `compiled_flow` detail is only valid when `candidate_type` is `flow`
    (enforced in both the JSON Schema and the Python dataclass).
  - **`CompiledFlow`** — a compiled flow (e.g. a ChainWeaver flow) exposed as a
    routable, executable item. References (does not inline) its input/output
    schemas, lists internal `tool_dependencies`, and carries derived
    `sensitivity` / `side_effects`. `requires_authorization` defaults to `true`:
    a pre-compiled flow does not bypass the kernel authorization path
    (invariant I-07). It attaches to an `ExecutionCandidate` (when
    `candidate_type` is `flow`) via `$ref`.
  - **`ExecutionRoutingDecision`** — a router's **advisory** recommendation of an
    `ExecutionCandidate`. Named distinctly from the Core `RoutingDecision` (the
    `contextweaver` ChoiceCard wrapper, kept separate per AGENTS.md "Design
    decisions not to reopen"). It does not grant execution rights; the
    execution/policy layer still records a `PolicyDecision` and emits a
    `TraceEvent` (invariant I-02). `confidence` is standardized to `[0.0, 1.0]`.
  - **`ExecutionFeedback`** — the observed outcome of executing a candidate,
    correlated by `decision_id` / `candidate_id` and preserving the execution
    runtime's `trace_ref`. `quality_score` is standardized to `[0.0, 1.0]`.
    Consuming feedback is optional, keeping deterministic routers deterministic.
  - JSON Schemas under `contracts/json/extended/`, Python dataclasses in
    `extended.py` (with `__post_init__` range/enum validation mirroring the
    schemas), four sample payloads (including a `contextweaver` → ChainWeaver
    routing example and an external-router → ChainWeaver → feedback example),
    roundtrip tests in `test_extended.py`, schema-alignment + negative tests in
    `test_extended_schema_alignment.py`, and the normative
    `docs/EXECUTION_BOUNDARY.md`. `contracts/COVERAGE.md` and
    `well-known/contracts.json` regenerated. These are additive Extended
    contracts (no Core change), folded into the unreleased `0.6.0` set.
    Closes #61. Closes #66.
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
    `TestOtelTraceMapping` (11 + 12 cases each, including JCS/algorithm
    registry enforcement, the 86-char base64url length constraint on
    `sig`, W3C-lowercase enforcement on `trace_id` / `span_id` /
    `parent_span_id`, and all five OTel span kinds).
    `test_extended_schema_alignment.py` adds the nine new schemas to its
    parametrized list plus eleven new negative cases (unknown signing
    algorithm, unknown canonicalization, signed CapabilityToken
    validation, invalid OTel span kind, malformed `trace_id`, uppercase
    `trace_id`, wrong-length `sig`, `confidence_score` above/below
    `[0.0, 1.0]`, negative `estimated_duration_ms`, missing fingerprint
    required fields).
  - `ExtendedFrameMetadata` and `ExtendedSelectableItemMetadata` gain
    `__post_init__` range validation so the Python dataclass enforces
    the same numeric bounds the JSON Schemas document: `confidence_score`
    must be in `[0.0, 1.0]` (the schema gains explicit `minimum`/`maximum`
    too) and `estimated_duration_ms` must be `>= 0` (schema's existing
    `minimum: 0` is now mirrored in Python).
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
