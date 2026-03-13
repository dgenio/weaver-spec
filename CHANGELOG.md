# Changelog

All notable changes to weaver-spec are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The spec and contracts follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

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

[0.1.0]: https://github.com/dgenio/weaver-spec/releases/tag/v0.1.0
