# weaver-spec

**Canonical specs and shared contracts for the Weaver Stack.**

[![Weaver-compatible](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/dgenio/weaver-spec/main/docs/badges/weaver-spec.json)](docs/SELF_CERTIFICATION.md)
[![Read the Weaver Stack overview on Towards AI](https://img.shields.io/badge/Read_the_overview-Towards_AI-black?logo=medium&logoColor=white)](https://pub.towardsai.net/the-weaver-stack-one-contract-layer-for-safe-llm-agents-7f733cad5eac)

> **Part of the [Weaver Stack](docs/WEAVER_STACK.md)**
>
> | Repo | Role |
> |------|------|
> | [weaver-spec](https://github.com/dgenio/weaver-spec) | Canonical specs + contracts |
> | [contextweaver](https://github.com/dgenio/contextweaver) | Context compilation + routing |
> | [agent-kernel](https://github.com/dgenio/agent-kernel) | Execution + firewalling + audit |
> | [ChainWeaver](https://github.com/dgenio/ChainWeaver) | Flow orchestration |
>
> New here? Start with [What Is the Weaver Stack?](docs/WEAVER_STACK.md).

This repository is the single source of truth for the vocabulary, invariants, responsibility boundaries, versioning rules, and language-agnostic contract schemas that keep the Weaver ecosystem composable and compatible.

---

## What This Repo Is For

`weaver-spec` is **documentation + contracts**, not a runtime library. It defines the interfaces that the Weaver repositories share. Each repo can be adopted independently; `weaver-spec` defines the contracts that make them interoperable when used together.

### Ecosystem map

| Repo | Role | Layer ([ARCHITECTURE.md](docs/ARCHITECTURE.md)) |
| ---- | ---- | ----------------------------------- |
| **[contextweaver](https://github.com/dgenio/contextweaver)** | Context compilation, tool routing, ChoiceCard generation. | Routing |
| **[agent-kernel](https://github.com/dgenio/agent-kernel)** | Capability authZ/authN, execution, firewalling, audit. | Execution |
| **[ChainWeaver](https://github.com/dgenio/ChainWeaver)** | Deterministic DAG / flow orchestration. | Orchestration |
| **AgentFence** | External policy firewall / proxy for tool calls. Optional; complements (does not replace) the agent-kernel firewall. | Adjacent — policy edge |
| **vibeguard** | Pre-merge checks for AI-generated code risks. Adjacent to the runtime stack; not on the request path. | Adjacent — dev workflow |

Only the first three repos are on the runtime request path. AgentFence and vibeguard are adjacent tools that share contracts and conventions but are not required for a working Weaver stack.

For the full boundary map (owns / consumes / emits per project, plus an end-to-end lifecycle), see [docs/ECOSYSTEM.md](docs/ECOSYSTEM.md).

### Adoption paths

Pick the path that matches what you are integrating today. None requires adopting the full stack.

| Goal | Adopt | Read first |
| ---- | ----- | ---------- |
| Smarter, bounded tool routing for an LLM you already host. | `contextweaver` alone. Provide your own execution layer that returns a `Frame`. | [docs/ADOPTION_GUIDE.md](docs/ADOPTION_GUIDE.md), [docs/LIFECYCLE.md](docs/LIFECYCLE.md) phase 1. |
| Add capability authorization, firewalling, and audit to an existing tool runner. | `agent-kernel` alone. Provide your own routing that returns a `RoutingDecision`. | [docs/BOUNDARIES.md](docs/BOUNDARIES.md), [docs/LIFECYCLE.md](docs/LIFECYCLE.md) phases 2–3. |
| Deterministic multi-step flows over any safe execution backend. | `ChainWeaver` alone, against any backend that honors the `CapabilityToken` + `RoutingDecision` contracts. | [docs/LIFECYCLE.md](docs/LIFECYCLE.md) phase 5, [examples/multi_agent_orchestration.md](examples/multi_agent_orchestration.md). |
| Read or pin the shared contracts without adopting any sibling repo. | Reference the JSON Schemas in `contracts/json/` directly, or `pip install weaver_contracts` for Python types. | [docs/QUICKSTART.md](docs/QUICKSTART.md), [contracts/json/](contracts/json/). |
| Propose a Core contract change. | Open an issue, then follow the ADR process. | [CONTRIBUTING.md](CONTRIBUTING.md), [docs/VERSIONING.md](docs/VERSIONING.md). |

This repo is the contract layer for all of the above. You do not need to adopt every sibling to benefit; you do need to honor the contracts at any boundary you cross.

---

## Quick Navigation

| What you need | Where to look |
| --------------- | --------------- |
| What is the Weaver Stack? (explainer) | [docs/WEAVER_STACK.md](docs/WEAVER_STACK.md) |
| Ecosystem overview | [docs/VISION.md](docs/VISION.md) |
| Ecosystem boundary map | [docs/ECOSYSTEM.md](docs/ECOSYSTEM.md) |
| Ecosystem launch post (draft) | [docs/WEAVER_STACK_LAUNCH.md](docs/WEAVER_STACK_LAUNCH.md) |
| Quick-start (Python + JS/TS) | [docs/QUICKSTART.md](docs/QUICKSTART.md) |
| Contract field reference | [docs/CONTRACT_REFERENCE.md](docs/CONTRACT_REFERENCE.md) |
| Layer architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Responsibility boundaries | [docs/BOUNDARIES.md](docs/BOUNDARIES.md) |
| Non-negotiable invariants | [docs/INVARIANTS.md](docs/INVARIANTS.md) |
| End-to-end lifecycle | [docs/LIFECYCLE.md](docs/LIFECYCLE.md) |
| Cross-repo integration map | [docs/INTEGRATION_MAP.md](docs/INTEGRATION_MAP.md) |
| Cross-project artifact contracts | [docs/ARTIFACT_CONTRACTS.md](docs/ARTIFACT_CONTRACTS.md) |
| Selection ↔ execution boundary | [docs/EXECUTION_BOUNDARY.md](docs/EXECUTION_BOUNDARY.md) |
| Term definitions | [docs/GLOSSARY.md](docs/GLOSSARY.md) |
| Sequence diagrams | [docs/SEQUENCE_DIAGRAMS.md](docs/SEQUENCE_DIAGRAMS.md) |
| Versioning rules | [docs/VERSIONING.md](docs/VERSIONING.md) |
| Adoption guide | [docs/ADOPTION_GUIDE.md](docs/ADOPTION_GUIDE.md) |
| FAQ | [docs/FAQ.md](docs/FAQ.md) |
| Contract artifact coverage | [contracts/COVERAGE.md](contracts/COVERAGE.md) |
| Governance and roles | [CHARTER.md](CHARTER.md) |
| Security framework alignment | [docs/SECURITY_MAPPING.md](docs/SECURITY_MAPPING.md) |
| Deprecation register | [docs/DEPRECATIONS.md](docs/DEPRECATIONS.md) |
| Schema hosting policy | [docs/SCHEMA_HOSTING.md](docs/SCHEMA_HOSTING.md) |
| Doc markup conventions | [docs/DOCS_CONVENTIONS.md](docs/DOCS_CONVENTIONS.md) |
| Content-addressed schema index | [well-known/contracts.json](well-known/contracts.json) |
| JSON Schemas | [contracts/json/](contracts/json/) |
| Python package | [contracts/python/](contracts/python/) |
| End-to-end examples | [examples/](examples/) |
| Minimal interoperability examples | [examples/interoperability/](examples/interoperability/) |
| Runnable reference implementation | [examples/reference_impl/](examples/reference_impl/) |
| Conformance suite | [docs/CONFORMANCE.md](docs/CONFORMANCE.md) |
| "Weaver-compatible" badge | [docs/SELF_CERTIFICATION.md](docs/SELF_CERTIFICATION.md) |
| Public conformance scoreboard | [docs/SCOREBOARD.md](docs/SCOREBOARD.md) |

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

> [!NOTE]
> Throughout the docs, `> [!IMPORTANT]` callouts mark **binding requirements**, `> [!NOTE]` callouts mark **informative guidance**, and fenced code blocks contain **illustrative examples**. See [docs/DOCS_CONVENTIONS.md](docs/DOCS_CONVENTIONS.md) for the full markup convention.

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

Current contract version: **0.8.0**

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
