---
mode: agent
description: Add a new optional field to an existing Core contract (six-artifact rule).
---

# Add a field to an existing Core contract

You are working in the **weaver-spec** repository, which is **docs + contracts only**. You are about to add an **optional, additive field** to an existing Core contract. This is a non-breaking change — semver MINOR.

> [!IMPORTANT]
> Authority hierarchy: `docs/INVARIANTS.md` → `docs/BOUNDARIES.md` → `docs/ARCHITECTURE.md` → everything else.
> A field that contradicts an invariant or boundary must not be added — open an ADR instead (see `docs/adr/template.md`).

If the field is **required** (cannot default), or **removes/renames** an existing field, or **weakens** an existing constraint — STOP. That is a **breaking change** and needs the ADR process in `CONTRIBUTING.md`. Use the breaking-change ADR template instead of this prompt.

---

## Inputs you need before writing any code

Confirm the following with the requester before proceeding. If any is unclear, ask once and wait:

1. **Contract name** — e.g., `RoutingDecision`, `Frame`, `CapabilityToken`. One of the 9 Core types in `contracts/python/src/weaver_contracts/core.py`.
2. **Field name** — `snake_case`, descriptive. Must not start with `x_` (that prefix is reserved for un-namespaced extensions; see `docs/FAQ.md`).
3. **Field JSON type** — `string` / `integer` / `number` / `boolean` / `array` / `object`.
4. **Optional/default value** — additive fields must be optional. Pick a safe default (typically `None` in Python, omitted in JSON).
5. **Constraints** — `minLength`, `enum`, `format`, `pattern`, etc. Tighter is safer (constraints can be relaxed only via ADR).
6. **Rationale** — one sentence on why this field is universally needed by all three siblings (contextweaver, agent-kernel, ChainWeaver). If it is implementation-specific, propose an Extended contract instead (`extended.py`).

---

## Apply the six-artifact rule

> [!IMPORTANT]
> Every Core contract change updates **all six** of these in the same PR. Missing any one will fail review.

### 1. JSON Schema (`contracts/json/<contract>.schema.json`)

- Add the field to `properties` with `type`, `description`, and any constraints.
- Do **not** add it to `required`.
- Keep the description ≤1 short sentence; do not duplicate invariant prose.
- Schema `$id` must remain unchanged (immutable per `docs/SCHEMA_HOSTING.md`).

### 2. Python dataclass (`contracts/python/src/weaver_contracts/core.py`)

- Add the field with `Optional[<type>] = None` (or another safe default).
- Match the JSON Schema field name and type **exactly** — zero divergence allowed.
- If the schema declares an `enum`, validate it in `__post_init__` and raise `ValueError` on mismatch.
- Do **not** import any non-stdlib module.

### 3. Sample payload (`examples/sample_payloads/<contract>.json`)

- Update the canonical payload to include the new field in at least one example.
- The payload must validate against the updated schema (CI runs `validate-walkthroughs` and JSON validation).
- If the field is enum-constrained, use a valid enum value.

### 4. Roundtrip test (`contracts/python/tests/test_roundtrip_examples.py`)

- Extend the existing `test_<contract>_from_payload` (or matching pattern) to assert the new field is read back.
- Add at least one explicit assertion: `assert obj.new_field == "expected_value"`.
- If the field is enum-constrained, add a negative test asserting an invalid value raises `ValueError`.

### 5. CHANGELOG (`CHANGELOG.md`)

Add an entry under `[Unreleased] → Added`:

```markdown
- `<Contract>.<new_field>` — optional `<type>`. <One-sentence rationale>. Closes #<issue>.
```

### 6. Version bump

- `contracts/python/src/weaver_contracts/version.py` — bump MINOR (`0.X.0`).
- `contracts/python/pyproject.toml` — bump `version` to match.

---

## Validation gates (must all pass before opening PR)

Run from repo root:

```bash
# 1. Python tests + coverage threshold (≥80%)
cd contracts/python && pip install -e ".[dev]" && pytest --cov --cov-report=term-missing && cd ../..

# 2. mypy strict
cd contracts/python && mypy src/ && cd ../..

# 3. JSON schema validity + required fields
python scripts/check_schema_fields.py
python -c "import json,glob; [json.load(open(f)) for f in glob.glob('examples/sample_payloads/*.json')]"

# 4. Contracts index freshness
python scripts/generate_contracts_index.py     # regenerate
python scripts/generate_contracts_index.py --check

# 5. Markdown lint (see CONTRIBUTING.md for the canonical command)
markdownlint README.md CONTRIBUTING.md CHANGELOG.md CHARTER.md \
  'docs/**/*.md' 'contracts/**/*.md' 'examples/**/*.md' '.github/**/*.md'
```

Or, if pre-commit is installed: `pre-commit run --all-files`.

---

## Invariant verification

> [!IMPORTANT]
> Before opening the PR, walk through I-01 through I-07 in `docs/INVARIANTS.md` and confirm none is violated by the new field. Flag any uncertainty in the PR body.

Common pitfalls:

- A field that exposes raw tool output references violates **I-01 / I-05** — use a `Handle` instead.
- A field that introduces a "silent" execution path violates **I-02** — every authorized invocation needs a paired `TraceEvent`.
- A field that injects full tool schemas at routing time violates **I-03** — keep routing payloads bounded.
- A field that is only used by one adopter violates **I-04** — move it to an Extended contract.

---

## Cross-repo impact

Core contract changes affect **contextweaver**, **agent-kernel**, and **ChainWeaver**. Fill out the **Cross-repo impact** section of the PR body explicitly — never leave it as "no impact" for a Core change. If any sibling consumes or produces the contract, list whether a coordinated update is needed and when.

---

## PR title and body

- **Title:** `contracts: add <Contract>.<new_field> (closes #<issue>)`
- **Body:** use the template in `.github/pull_request_template.md`. Check the *Additive contract change* box, tick all six-artifact items, tick the invariants box, and fill out the cross-repo section.
