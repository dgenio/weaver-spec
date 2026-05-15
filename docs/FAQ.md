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

A separate ADR document file in `docs/adr/` is required for breaking Core contract changes. Copy the template from [`docs/adr/template.md`](adr/template.md) and follow the naming convention in [`docs/adr/README.md`](adr/README.md). The issue + PR history provides additional context, but the ADR file is the durable decision record.

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

---

## How do I add a new capability to my agent?

A `Capability` is a registry entry, not a class to instantiate at runtime. The minimum steps:

1. Pick a stable, namespaced `id` (e.g., `org.myapp.search_docs`). Capability IDs are immutable once published — treat them like API endpoints.
2. Construct a `Capability` with `id`, `name`, `version`, and `description`. Optionally declare `input_schema_ref` and `output_schema_ref` URIs pointing to your service's own JSON Schemas (these are not enforced by weaver-spec).
3. Register the `Capability` in your agent-kernel's capability registry so that contextweaver can include it as a `SelectableItem` candidate.
4. Surface the capability to contextweaver — the routing layer must be able to discover it so it can produce `ChoiceCard` entries pointing at it.

See `Capability` in [CONTRACT_REFERENCE.md](CONTRACT_REFERENCE.md) for the full field table, and the contextweaver integration snippet in [QUICKSTART.md](QUICKSTART.md) for how a `SelectableItem` references a `capability_id`.

---

## How do I extend Frame metadata without modifying Core?

Use `ExtendedFrameMetadata` (or your own namespaced fields) and attach it via `Frame.metadata`. Core schemas declare `additionalProperties: true`, so adopter-specific keys never break validation. Concretely:

```python
from weaver_contracts import Frame
from weaver_contracts.extended import (
    ExtendedFrameMetadata,
    RedactionPolicy,
    TelemetryHint,
)
from dataclasses import asdict
from datetime import datetime, timezone

extended = ExtendedFrameMetadata(
    redaction_policy=RedactionPolicy(policy_id="policy-2026Q1"),
    telemetry=TelemetryHint(trace_id="trace-001"),
)
frame = Frame(
    frame_id="f-001",
    capability_id="org.myapp.search_docs",
    summary="Found 3 documents.",
    created_at=datetime.now(timezone.utc),
    metadata={"extended": asdict(extended)},
)
```

Do not propose adding `redaction_policy`, `telemetry`, etc. as direct Core fields — that violates invariant I-04 (Core contracts minimal and stable).

---

## How do I validate payloads against schemas in my language?

Use any JSON Schema Draft 2020-12 validator. The pattern is identical across languages:

- **Python:** `jsonschema` (`Draft202012Validator`, with `format_checker` enabled).
- **JavaScript/TypeScript:** `ajv` (`ajv/dist/2020`) plus `ajv-formats` for `date-time` and similar formats.
- **Java/Kotlin:** `networknt/json-schema-validator` (set `SpecVersionDetector` to Draft 2020-12).
- **Go:** `santhosh-tekuri/jsonschema/v5`.
- **Rust:** `jsonschema` crate (`Draft202012`).

Critical detail: always enable the format-keyword checker. Without it, `date-time` and similar formats are not enforced, and you will accept payloads the rest of the ecosystem rejects. Copy-paste examples for Python and JS/TS live in [QUICKSTART.md](QUICKSTART.md) and [`contracts/json/README.md`](../contracts/json/README.md).

---

## How do I handle contract version mismatches between services?

Two versions are compatible when they share the same MAJOR version. The Python package exposes a helper:

```python
from weaver_contracts.version import CONTRACT_VERSION, is_compatible

assert is_compatible(peer_version)   # raises if MAJOR differs
```

In languages other than Python, do the same MAJOR-version comparison yourself. The compatibility table in [VERSIONING.md](VERSIONING.md) tracks which sibling-repo versions are known to interoperate with which contract versions. If you publish your service, declare your supported contract MAJOR(s) explicitly so consumers know which payloads to send.

A breaking Core contract change always increments MAJOR and goes through the ADR process described in [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## How do I add telemetry to my contract flows?

Use the Extended `TelemetryHint` type for trace IDs and baggage, and emit a `TraceEvent` for each significant lifecycle step (authorization, execution, firewall application, handle creation, etc.). The `TraceEvent.event_type` enum lists the canonical event types (`capability_authorized`, `capability_executed`, `firewall_applied`, …) — see [CONTRACT_REFERENCE.md](CONTRACT_REFERENCE.md) for the complete list. Attach `TelemetryHint` either inside a `Frame.metadata` or in a parallel `ExtendedFrameMetadata.telemetry` field. Invariant I-02 already requires every execution to be audited, so `TraceEvent` is the canonical observability hook; telemetry hints are additive.

---

## How do I propose a new field for a Core contract?

Most "new field" proposals belong in Extended, not Core. Before opening an issue, ask:

1. Would every adopter — contextweaver-only, agent-kernel-only, and ChainWeaver — need this field? If not, it belongs in Extended (see invariant I-04).
2. Does it weaken any existing constraint? Loosening an `enum`, dropping a `required` entry, removing a `minLength` — these are breaking changes regardless of whether existing payloads remain valid.

If the field genuinely belongs in Core, open an ADR-proposal issue using the `.github/ISSUE_TEMPLATE/adr_proposal.yml` form. Follow the ADR process in [CONTRIBUTING.md](../CONTRIBUTING.md): issue → minimum 3 business days of discussion → PR that lands all six artifacts (schema, dataclass, sample payload, roundtrip test, CHANGELOG, version bump) plus an ADR file in [`docs/adr/`](adr/). Cross-repo impact must be flagged in the PR description.

---

## What's the difference between Frame and Handle?

A `Frame` is the LLM-safe view; a `Handle` is an opaque reference to the raw artifact.

- A `Frame` is what contextweaver and the LLM see. Its `summary` is human-readable and firewall-filtered. It never contains raw output (invariants I-01, I-05).
- A `Handle` is an access-controlled pointer to the full artifact, which lives in the HandleStore. The `Handle` itself carries no payload; resolving it back to raw bytes requires authorization through agent-kernel.

A `Frame` may reference one or more handles via `handle_refs`. Adopters that need the raw artifact (for archival, replay, or downstream processing) resolve a handle through the kernel; adopters that only need to feed the LLM consume the `Frame` and never touch the handle. This separation exists because raw output may contain secrets, PII, large binaries, or injection vectors — see [BOUNDARIES.md](BOUNDARIES.md) for the artifact-ownership table.

---

## How do I test my implementation against the spec?

Validate your payloads against the JSON Schemas in [`contracts/json/`](../contracts/json/) at every layer boundary. A practical conformance pattern:

1. **Schema validation in unit tests.** For every contract your service produces or consumes, write a test that loads the schema (Draft 2020-12, format-checker enabled) and validates a representative payload. The sample payloads in [`examples/sample_payloads/`](../examples/sample_payloads/) are a good source of starter fixtures.
2. **Invariant assertions.** Add tests that exercise the constraints in [INVARIANTS.md](INVARIANTS.md) that apply to your layer — for example, "every `Frame` we emit has a non-empty `summary` and never contains raw payload text" or "every `CapabilityToken` we accept has `expires_at` or `single_use=true`".
3. **Walkthrough fixtures.** Use the failure scenarios and orchestration walkthroughs in [`examples/`](../examples/) as integration fixtures.

A canonical, repo-managed conformance suite is tracked separately (issue #4).
