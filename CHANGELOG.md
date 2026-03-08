# Changelog

All notable changes to weaver-spec are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The spec and contracts follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

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
