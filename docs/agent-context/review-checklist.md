# Review Checklist

> Use this checklist for self-review before proposing a change, or for maintainer review of incoming PRs.
> For the underlying rules, see [AGENTS.md](../../AGENTS.md).

---

## Review priority order

When reviewing Core contract changes, check in this order:

1. **Artifact completeness** — Are all required artifacts updated?
2. **Invariant compliance** — Do invariants I-01 through I-07 hold?
3. **Boundary compliance** — Does the change respect `docs/BOUNDARIES.md`?

---

## Artifact completeness

For Core contract changes, all six must be in the same PR:

- [ ] JSON Schema updated (`contracts/json/`)
- [ ] Python dataclass updated (`contracts/python/src/weaver_contracts/core.py`)
- [ ] Sample payload updated or created (`examples/sample_payloads/`)
- [ ] Roundtrip test updated or created (`contracts/python/tests/test_roundtrip_examples.py`)
- [ ] CHANGELOG entry added
- [ ] Version bumped in `version.py` and `pyproject.toml`

For Extended contract changes, the same pattern applies but with `extended.py` instead of `core.py`.

---

## Invariant compliance

- [ ] I-01 / I-05: Change does not expose raw tool output to contextweaver or the LLM
- [ ] I-02: Change does not create a path for unaudited execution
- [ ] I-03: Change does not require full tool schema injection for routing
- [ ] I-04: Any new Core field is universally needed (not implementation-specific)
- [ ] I-06: CapabilityToken constraints (scoped + expiry or single-use) are preserved
- [ ] I-07: ChainWeaver tool invocations still delegate to agent-kernel

---

## Schema-description consistency

- [ ] No `description` asserts "required" for a field not in the `required` array
- [ ] No `description` claims extensibility for a field with an `enum` constraint
- [ ] No `description` asserts a format (e.g., "UUID") not enforced by a `format` or `pattern` constraint
- [ ] Description text accurately reflects the structural constraints

---

## Cross-file consistency

- [ ] Python dataclass field names, types, and required/optional status match the JSON schema exactly
- [ ] Sample payload validates against the updated schema
- [ ] Roundtrip test covers the updated fields
- [ ] Mermaid diagrams (if modified) match the artifact ownership table in `docs/BOUNDARIES.md`

---

## Documentation and update checks

- [ ] CHANGELOG entry present for non-patch changes
- [ ] Version numbers consistent across `version.py` and `pyproject.toml`
- [ ] PR description includes cross-repo impact section (for Core contract changes)
- [ ] If a term definition changed, `docs/GLOSSARY.md` is updated
- [ ] If a boundary or invariant changed, `docs/BOUNDARIES.md` or `docs/INVARIANTS.md` is updated via ADR
- [ ] No new duplicate authority introduced — each rule has one canonical home
- [ ] Agent-facing docs (`AGENTS.md`, `docs/agent-context/*`) updated if any shared rule, workflow, or invariant changed

---

## Local validation

- [ ] `pytest` passes (`cd contracts/python && pip install -e ".[dev]" && pytest`)
- [ ] JSON schemas parse without error
- [ ] Markdownlint passes on all `.md` files

---

## Update triggers

Update this checklist when:
- A new artifact is added to the required-per-PR set
- A new invariant is added
- Review expectations or gates change
- A new cross-file consistency rule is discovered
