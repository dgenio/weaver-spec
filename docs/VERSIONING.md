# Versioning

## Scope

This document defines the versioning rules for:

1. The **spec documents** (this repository's Markdown files).
2. The **JSON Schemas** (`contracts/json/`).
3. The **Python package** `weaver_contracts` (`contracts/python/`).

---

## Semantic Versioning

All versioned artifacts follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

| Increment | When |
|-----------|------|
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

Extended contracts provide optional metadata (telemetry, UI hints, risk levels, schema fingerprints, redaction notes). They are declared in `extended.py` and are not required by any Core contract.

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

The Python package version is defined in `contracts/python/src/weaver_contracts/version.py` and must match the contract version:

```python
CONTRACT_VERSION = "0.1.0"
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

This table tracks which versions of the sibling repositories are known-compatible with each contract version.

| Contract Version | contextweaver | agent-kernel | ChainWeaver |
|-----------------|--------------|-------------|-------------|
| 0.1.0 | — (TBD) | — (TBD) | — (TBD) |

*Entries marked "—" indicate that the sibling repository has not yet declared compatibility. Maintainers should update this table when a sibling repository publishes a compatibility declaration.*

---

## Deprecation Policy

When a contract field or type is deprecated:

1. It is marked `deprecated: true` in the JSON Schema and with a `# Deprecated` comment in Python.
2. It remains in the Core for at least one full major version.
3. The deprecation is documented in `CHANGELOG.md` with the version it was deprecated and the version it will be removed.
