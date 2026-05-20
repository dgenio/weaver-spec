---
mode: agent
description: Create a brand-new Core JSON Schema + Python dataclass + sample payload + tests.
---

# Add a new Core contract (schema + dataclass + payload + tests)

You are working in the **weaver-spec** repository, which is **docs + contracts only**. You are about to add a **new Core contract type** — a brand-new JSON Schema plus its mirrored Python dataclass, a sample payload, roundtrip tests, and the supporting CHANGELOG/version updates.

> [!IMPORTANT]
> Authority hierarchy: `docs/INVARIANTS.md` → `docs/BOUNDARIES.md` → `docs/ARCHITECTURE.md` → everything else.
> A new Core type that crosses a boundary in `docs/BOUNDARIES.md` requires an ADR. If you are not certain the type belongs in Core, propose it as **Extended** first (see `contracts/python/src/weaver_contracts/extended.py` and the Extended contract workflow in `docs/agent-context/workflows.md`).

If this type is **only useful to one adopter** — STOP. That is an Extended contract or a local extension, not Core. Adding implementation-specific types to Core violates **I-04** (`docs/INVARIANTS.md`).

---

## Inputs you need before writing any code

1. **Type name** — `PascalCase` Python class name; `snake_case` schema file name. Must not collide with any existing type in `contracts/python/src/weaver_contracts/core.py` or `extended.py`.
2. **Purpose** — one paragraph describing what the type represents, which layer owns it (per `docs/BOUNDARIES.md`), and which sibling repo produces vs consumes it.
3. **Field list** — for each field: `snake_case` name, JSON type, required/optional, constraints (`enum`, `format`, `minLength`, `pattern`, etc.), one-sentence description.
4. **Identifier field** — every Core type carries a non-empty `id: string` (see `docs/FAQ.md` ID format guidance). Confirm the ID convention.
5. **Cross-references** — which existing Core types does this type reference? Use the same field names (`capability_id`, `frame_id`, etc.) as established by sibling types.

---

## Apply the six-artifact rule

> [!IMPORTANT]
> A new Core type touches **all six** artifacts in the same PR. Missing any one will fail review.

### 1. JSON Schema — `contracts/json/<type_name>.schema.json`

Template (replace `<type_name>` and field block):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://weaver-spec.dev/contracts/v0/<type_name>.schema.json",
  "title": "<TypeName>",
  "description": "<One-sentence purpose. Owned by: <layer>>.",
  "type": "object",
  "required": ["id"],
  "properties": {
    "id": {
      "type": "string",
      "minLength": 1,
      "description": "Stable identifier for this <TypeName>."
    }
  },
  "additionalProperties": true
}
```

- `$id` must follow the pattern in `docs/SCHEMA_HOSTING.md` and use the current MAJOR version (`/v0/...` until v1.0.0).
- Schema is Draft 2020-12. Validate locally with `jsonschema`.
- Conventions and required schema fields are documented in `contracts/json/README.md`.

### 2. Python dataclass — `contracts/python/src/weaver_contracts/core.py`

- Add the class with `@dataclass(frozen=False)` (the existing pattern; check the file for the canonical decorator style).
- Field names + types must mirror the JSON Schema **exactly** — zero divergence allowed.
- Implement `__post_init__` for any non-structural constraint the schema enforces (enum membership, non-empty string, range checks). Raise `ValueError` on violation.
- Do **not** import any non-stdlib module.
- Export the class from `contracts/python/src/weaver_contracts/__init__.py`.

### 3. Sample payload — `examples/sample_payloads/<type_name>.json`

- A minimal but complete example using slug-style IDs (`<prefix>-<date>-<NNN>` is the convention; see existing payloads).
- Must validate against the new schema. CI runs both `validate-schemas` and the inline-payload validator.

### 4. Roundtrip test — `contracts/python/tests/test_roundtrip_examples.py`

- Add a new `Test<TypeName>` class following the pattern of existing classes in the file.
- Include at least:
  - `test_from_payload` — loads the sample JSON and reconstructs the dataclass.
  - `test_required_fields` — asserts every required field is read back.
  - One negative test for each enum/range/length constraint declared in the schema.
- Add a JSON Schema alignment test in `contracts/python/tests/test_json_schema_alignment.py` (`TestPayload` class pattern).

### 5. CHANGELOG — `CHANGELOG.md`

Add under `[Unreleased] → Added`:

```markdown
- `<TypeName>` Core contract — schema `contracts/json/<type_name>.schema.json`, Python dataclass `core.<TypeName>`, sample payload `examples/sample_payloads/<type_name>.json`. <One-sentence purpose>. Closes #<issue>.
```

### 6. Version bump

- `contracts/python/src/weaver_contracts/version.py` — bump MINOR (`0.X.0`).
- `contracts/python/pyproject.toml` — bump `version` to match.
- Regenerate the contracts index: `python scripts/generate_contracts_index.py`. The index `contract_version` will pick up the new value automatically.

---

## Validation gates (must all pass before opening PR)

Run from repo root:

```bash
# 1. Python tests + coverage threshold (≥80%)
cd contracts/python && pip install -e ".[dev]" && pytest --cov --cov-report=term-missing && cd ../..

# 2. mypy strict
cd contracts/python && mypy src/ && cd ../..

# 3. JSON schema validity + required fields ($id, title, description)
python scripts/check_schema_fields.py
python -c "import json,glob; [json.load(open(f)) for f in glob.glob('examples/sample_payloads/*.json')]"

# 4. Contracts index freshness (must be regenerated after adding a new schema)
python scripts/generate_contracts_index.py
python scripts/generate_contracts_index.py --check

# 5. Markdown lint (see CONTRIBUTING.md for the canonical command)
markdownlint README.md CONTRIBUTING.md CHANGELOG.md CHARTER.md \
  'docs/**/*.md' 'contracts/**/*.md' 'examples/*.md'
```

Or, if pre-commit is installed: `pre-commit run --all-files`.

---

## Invariant verification

> [!IMPORTANT]
> Before opening the PR, walk through I-01 through I-07 in `docs/INVARIANTS.md`. A new type often raises one of these:
>
> - Does the type expose raw tool output without firewalling? — violates **I-01 / I-05**.
> - Does the type bypass authorization or audit? — violates **I-02**.
> - Does the type carry full tool schemas through the routing path? — violates **I-03**.
> - Is the type implementation-specific? — violates **I-04** (use Extended instead).

Document the invariant check in the PR body even when no violation is found — reviewers will look for explicit reasoning, not an implicit pass.

---

## Cross-repo impact

A new Core type **always** has cross-repo impact: every sibling that produces or consumes the type needs a coordinated update. Fill out the **Cross-repo impact** section of the PR body explicitly — list each sibling (contextweaver / agent-kernel / ChainWeaver) and whether it needs a coordinated update, with the matching upstream issue if known.

---

## PR title and body

- **Title:** `contracts: add <TypeName> Core contract (closes #<issue>)`
- **Body:** use the template in `.github/pull_request_template.md`. Check the *Additive contract change* box, tick all six-artifact items, tick the invariants box, and fill out the cross-repo section. Mention the regenerated `well-known/contracts.json` in the description.
