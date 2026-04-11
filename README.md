# weaver-spec

**Canonical specs and shared contracts for the Weaver Stack.**

This repository is the single source of truth for the vocabulary, invariants, responsibility boundaries, versioning rules, and language-agnostic contract schemas that keep the Weaver ecosystem composable and compatible.

---

## What This Repo Is For

`weaver-spec` is **documentation + contracts**, not a runtime library. It defines the interfaces that three sibling repositories share:

| Repo | Role |
| ------ | ------ |
| **contextweaver** | Context compilation, tool routing, ChoiceCard generation |
| **agent-kernel** | Capability authZ/authN, execution, firewalling, audit |
| **ChainWeaver** | Deterministic DAG/flow orchestration |

Each repo can be adopted independently. `weaver-spec` defines the contracts that make them interoperable when used together.

---

## Quick Navigation

| What you need | Where to look |
| --------------- | --------------- |
| Ecosystem overview | [docs/VISION.md](docs/VISION.md) |
| Layer architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Responsibility boundaries | [docs/BOUNDARIES.md](docs/BOUNDARIES.md) |
| Non-negotiable invariants | [docs/INVARIANTS.md](docs/INVARIANTS.md) |
| Term definitions | [docs/GLOSSARY.md](docs/GLOSSARY.md) |
| Sequence diagrams | [docs/SEQUENCE_DIAGRAMS.md](docs/SEQUENCE_DIAGRAMS.md) |
| Versioning rules | [docs/VERSIONING.md](docs/VERSIONING.md) |
| Adoption guide | [docs/ADOPTION_GUIDE.md](docs/ADOPTION_GUIDE.md) |
| FAQ | [docs/FAQ.md](docs/FAQ.md) |
| JSON Schemas | [contracts/json/](contracts/json/) |
| Python package | [contracts/python/](contracts/python/) |
| End-to-end examples | [examples/](examples/) |

---

## How Contracts Are Structured

Contracts are split into two tiers:

- **Core** — minimal, stable, required by all adopters. Changes require a major version bump and an ADR.
- **Extended** — optional metadata (telemetry, UI hints, risk levels). Evolves faster; backward-compatible within a minor series.

---

## How to Propose Spec Changes

1. Open an issue describing the problem and proposed change.
2. For **breaking contract changes**, follow the lightweight ADR process in [CONTRIBUTING.md](CONTRIBUTING.md): issue → PR → contract version bump.
3. For doc-only or additive changes, a PR with a clear description is sufficient.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## Where Contracts Live

```text
contracts/
  json/          JSON Schemas (language-agnostic)
  python/        weaver_contracts Python package (stdlib dataclasses)
examples/
  sample_payloads/   Example JSON payloads validated against schemas
```

---

## Contract Versioning

The spec and contracts follow semantic versioning. See [docs/VERSIONING.md](docs/VERSIONING.md) for the full compatibility promise.

Current contract version: **0.1.0**

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
