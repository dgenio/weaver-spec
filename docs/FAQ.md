# FAQ

## Why not a single repository?

A single repository would couple routing, execution, and orchestration into one release cycle. A team that only needs bounded tool routing would still depend on the execution and orchestration code. A team that only needs safe execution would be forced to adopt contextweaver's routing model.

Separate repositories allow:
- Independent versioning and release cadence.
- Genuine partial adoption (each repo is usable alone).
- Clean dependency graphs: contextweaver can depend on weaver-spec contracts without depending on agent-kernel's runtime.

`weaver-spec` (this repository) plays the role of a shared interface layer that keeps the separate repos interoperable.

---

## What overlaps are intentionally prevented?

Three overlaps are explicitly prohibited by the boundary decisions in [BOUNDARIES.md](BOUNDARIES.md):

1. **contextweaver must not implement a firewall.** Firewalling raw tool output is agent-kernel's responsibility. If contextweaver were to filter output, every contextweaver implementation would re-implement security logic, leading to inconsistency.

2. **contextweaver must not execute tools.** Routing produces a decision; execution is always mediated by agent-kernel (or a compatible layer). This ensures authorization is always enforced.

3. **ChainWeaver must not issue or validate CapabilityTokens.** Authorization is always agent-kernel's responsibility, even within a ChainWeaver flow.

---

## How strict are the contracts?

**Core contracts are strict.** Every required field is required; types are precise; IDs must be non-empty strings (`minLength: 1`).

**Extended contracts are lenient.** Optional fields may be absent. New fields may be added in a minor version. Extended contracts are not required for spec compliance.

**The Python package enforces Core contracts at construction time** (dataclass field types and post-init validation). The JSON Schemas enforce them at validation time.

---

## Can I add my own fields to a contract?

Yes, via extension. You should not modify Core contract schemas directly. Instead:

- Add a custom field with a namespaced prefix (e.g., `x_myorg_field`) in your JSON payload. JSON Schema `additionalProperties` is not set to `false` in Core schemas precisely to allow this.
- In Python, subclass the Core dataclass and add your fields.
- Document your extensions in your own repository.

Do not submit custom organizational fields to weaver-spec unless they are universally applicable.

---

## How do I propose a change to the spec?

See [CONTRIBUTING.md](../CONTRIBUTING.md). The short version:

- For typos and clarifications: open a PR.
- For new optional fields or new contract types: open a PR with a CHANGELOG entry.
- For breaking changes to Core contracts: open an issue first, allow discussion, then open a PR following the ADR process.

---

## What is an ADR in this context?

An Architecture Decision Record. In weaver-spec, we use a lightweight form:

1. An issue that describes the problem, proposed change, and migration path.
2. A discussion period (minimum 3 business days).
3. A PR that implements the change and includes a CHANGELOG entry and version bump.

We do not require a separate ADR document file. The issue + PR history serves as the decision record.

---

## How do I know if my implementation is spec-compliant?

Your implementation is spec-compliant if:

1. All Core contract fields are present and correctly typed in your payloads.
2. The invariants in [INVARIANTS.md](INVARIANTS.md) are satisfied.
3. The boundary decisions in [BOUNDARIES.md](BOUNDARIES.md) are respected.
4. Your payloads validate against the JSON Schemas in `contracts/json/`.

You can use the Python package's validators or run the JSON Schema validation directly with any `jsonschema`-compatible library.

---

## Do I need to use the Python package?

No. The Python package (`weaver_contracts`) is a convenience layer for Python implementations. The JSON Schemas are the language-agnostic source of truth. You can implement the contracts in any language using the JSON Schema definitions.

---

## What Python versions are supported?

The `weaver_contracts` package requires Python 3.9+. It uses only the standard library at runtime (no third-party dependencies). `jsonschema` is a development/test dependency only.
