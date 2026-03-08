---
applyTo: "contracts/json/**"
---

# JSON Schema Instructions

## Conventions

- Use JSON Schema Draft 2020-12.
- Every schema must include `$id`, `title`, `description`, and set `additionalProperties: true`.
- `$id` URIs follow the pattern `https://weaver-spec.dev/contracts/v{MAJOR}/name.schema.json` — this is a namespace, not a live URL.
- Cross-schema references (`$ref`) use full `$id` URIs, not relative paths.
- `contracts/json/README.md` is the authoritative source for schema design conventions.

## Review cautions

- **Description must not contradict structural constraints.** Do not say a field is "required" in a `description` if it is not in the `required` array. Do not claim extensibility ("additional values may be used") for a field with an `enum` constraint.
- **Never weaken a constraint** (remove `minLength`, loosen an `enum`, drop a `required` entry) without an ADR. Constraint loosening affects consumers even when existing payloads remain valid.
- Every new schema must have a corresponding sample payload in `examples/sample_payloads/`.

## Change scope

A schema change is never standalone. The same PR must also update the Python dataclass, sample payload, roundtrip test, CHANGELOG, and version. See `AGENTS.md` for the full six-artifact rule.
