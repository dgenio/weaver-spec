# Versioning

## Scope

This document defines the versioning rules for:

1. The **spec documents** (this repository's Markdown files).
2. The **JSON Schemas** (`contracts/json/`).
3. The **Python package** `weaver_contracts` (`contracts/python/`).

---

## Semantic Versioning

All versioned artifacts follow [Semantic Versioning 2.0.0](https://semver.org/):

```text
MAJOR.MINOR.PATCH
```

| Increment | When |
| ----------- | ------ |
| **MAJOR** | Breaking change: required field removed, field renamed, type changed, invariant altered. |
| **MINOR** | Backward-compatible addition: new optional field, new contract type, new doc section. |
| **PATCH** | Backward-compatible fix: typo, clarification, example update, non-schema doc change. |

---

## Contract Tiers and Stability

### Core Contracts

Core contracts are the minimal, stable interface required by all adopters:

- `SelectableItem`, `ChoiceCard`, `RoutingDecision`
- `Capability`, `CapabilityToken`, `PolicyDecision`
- `Frame`, `Handle`, `TraceEvent`

**Stability promise:** Core contracts will not have breaking changes within a major version. A breaking change to any Core contract triggers a MAJOR version bump of the entire contract set.

### Extended Contracts

Extended contracts provide optional metadata (telemetry, UI hints, risk levels, schema fingerprints, redaction notes) plus the cross-project artifact and execution-boundary types. Each has a JSON Schema in `contracts/json/extended/` mirrored by a dataclass in `extended.py`, and none is required by any Core contract.

**Authority:** Extended contracts are **schema-led, the same as Core** — the JSON Schema is the source of truth and the dataclass mirrors it (enforced by `test_schema_parity.py`). The difference is the stability promise below, not where the contract is defined.

**Stability promise:** Extended contracts may have breaking changes in a MINOR version, provided the change is backward-compatible from a Core perspective. Extended contracts are explicitly versioned separately when they change independently.

---

## JSON Schema Versioning

Each JSON Schema file carries a version in its `$id` field:

```json
"$id": "https://weaver-spec.dev/contracts/v0/selectable_item.schema.json"
```

The `v0`, `v1`, etc. prefix tracks the MAJOR version of the contract. When a MAJOR bump occurs, old schema files are preserved for migration purposes under the previous version path.

---

## Python Package Versioning

The Python package version is defined in
`contracts/python/src/weaver_contracts/version.py` and must match the contract
version. Do not copy a literal example version into documentation; read the
canonical value instead:

```python
from weaver_contracts.version import CONTRACT_VERSION

print(CONTRACT_VERSION)
```

The `pyproject.toml` version must be updated to match. Package versions follow the same MAJOR.MINOR.PATCH rules.

---

## Spec Document Versioning

Spec documents (the Markdown files in `docs/`) do not carry individual version numbers. The repository itself is tagged with a version (e.g., `v0.1.0`) that corresponds to the contract version. A PATCH change to docs alone does not require a contract version bump.

---

## How to Propose a Version Bump

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full process. In summary:

- **PATCH**: PR is sufficient.
- **MINOR**: PR + CHANGELOG entry.
- **MAJOR**: ADR process (issue + discussion + PR + CHANGELOG + compatibility matrix update).

---

## Compatibility Matrix

This table tracks which versions of the sibling repositories are known-compatible with each contract version. The machine-readable source of truth is [`compatibility.yaml`](../compatibility.yaml) at the repository root; this table is the human-readable view of it.

### Status vocabulary

| Status | Meaning |
| ------ | ------- |
| `verified` | The sibling repo has declared support **and** backed it with passing tests/conformance against this contract version. |
| `provisional` | The sibling repo claims support, but it is not yet test-verified. |
| `unverified` | No compatibility declaration has been published yet (default). |
| `incompatible` | Known not to work against this contract version. |

> [!IMPORTANT]
> A cell may be `verified` or `provisional` only when backed by a real declaration recorded in `compatibility.yaml` (the `declaration` field). Unknown compatibility MUST be recorded as `unverified` — never assume or invent a version claim.

### Current matrix (contract version 0.8.0)

| Contract Version | contextweaver | agent-kernel | ChainWeaver |
| ----------------- | -------------- | ------------- | ------------- |
| 0.8.0 (current) | `unverified` | `unverified` | `unverified` |

All `0.x` contract versions share MAJOR version `0` and are mutually compatible (see [Semantic Versioning](#semantic-versioning) and `weaver_contracts.version.is_compatible`). No sibling repository has published a compatibility declaration yet, so every cell is `unverified`.

The single source of truth for the contract version string is `weaver_contracts.version.CONTRACT_VERSION`. Every other file that states the version (this document, `README.md`, `pyproject.toml`, `well-known/contracts.json`, `CHANGELOG.md`, `compatibility.yaml`, and the committed conformance-scoreboard snapshot) must match it; `scripts/check_version_consistency.py` (the `validate-version-consistency` CI job) enforces this and fails on drift.

### How a sibling repository declares compatibility

1. Test the sibling repo against a specific weaver-spec contract version (ideally via the contract round-trip tests or a conformance check).
2. Add or update the repo's entry in [`compatibility.yaml`](../compatibility.yaml): set `supported_spec_versions`, `tested_version`, `status`, `declaration` (a URL or commit ref backing the claim), and any `known_limitations`.
3. Update the matching cell in the matrix above so the human-readable view stays in sync with the manifest.
4. Open a PR. The `validate-compatibility` CI job (`.github/workflows/ci.yml`) checks the manifest structure and that every repository in the manifest is referenced in this document.

---

## Deprecation Policy

When a contract field or type is deprecated:

1. It is marked `deprecated: true` in the JSON Schema and with a `# Deprecated` comment in Python.
2. It remains in the Core for at least one full major version.
3. The deprecation is documented in `CHANGELOG.md` with the version it was deprecated and the version it will be removed.
