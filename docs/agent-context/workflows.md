# Workflows for Agents

> Consult this file for the authoritative command sequences and documentation governance rules.
> For the rules themselves, see [AGENTS.md](../../AGENTS.md).

---

## Core contract change workflow

When modifying a Core contract, complete all steps in a single PR:

1. **Update the JSON Schema** in `contracts/json/`. Follow the conventions in `contracts/json/README.md`.
2. **Update the Python dataclass** in `contracts/python/src/weaver_contracts/core.py`. Field names, types, and required/optional status must match the updated schema exactly.
3. **Update or create a sample payload** in `examples/sample_payloads/`. The payload must validate against the updated schema.
4. **Add or update a roundtrip test** in `contracts/python/tests/test_roundtrip_examples.py`.
5. **Add a CHANGELOG entry** under the appropriate version section.
6. **Bump the version** in both `contracts/python/src/weaver_contracts/version.py` and `contracts/python/pyproject.toml`.

After completing all six artifacts, run the local validation checks before submitting.

---

## Extended contract change workflow

Extended contracts define JSON Schemas under `contracts/json/extended/`.
Every Extended type ships the full eight-artifact set; the original metadata
types (`TelemetryHint`, `SchemaFingerprint`, `RedactionPolicy`, `UIHint`,
`RiskAssessment`, `ExtendedFrameMetadata`, `ExtendedSelectableItemMetadata`)
were retrofitted with schemas in v0.6.0 (#46).
When adding or modifying an Extended contract, complete all of the following in a single PR:

1. **Update the Python dataclass** in `contracts/python/src/weaver_contracts/extended.py`.
2. **Add or update the JSON Schema** under `contracts/json/extended/`.
3. **Update or create a sample payload** in `examples/sample_payloads/`.
4. **Add or update a roundtrip test** in `contracts/python/tests/test_extended.py`.
5. **Add or update a schema-alignment test** in `contracts/python/tests/test_extended_schema_alignment.py`.
6. **Add a CHANGELOG entry** under the appropriate version section.
7. **Bump the version** in both `contracts/python/src/weaver_contracts/version.py` and `contracts/python/pyproject.toml`.
8. **Regenerate** `contracts/COVERAGE.md` (`scripts/generate_coverage_table.py`) and `well-known/contracts.json` (`scripts/generate_contracts_index.py`); CI checks both with `--check`.

Breaking changes are allowed in MINOR versions for Extended contracts.

---

## Offline schema bundle workflow

The committed offline distribution artifact lives at
`contracts/bundles/weaver-contracts.bundle.json`. It is derived from the
content-addressed `well-known/contracts.json` index and must never be edited by
hand.

When a Core or Extended JSON Schema changes, regenerate the index first and the
bundle second, then commit both generated files in the same PR:

```bash
python scripts/generate_contracts_index.py
python scripts/generate_schema_bundle.py
python scripts/generate_schema_bundle.py --check
python tests/test_schema_bundle.py
```

The `Schema Bundle` workflow is read-only. It checks the committed bundle for
byte-for-byte freshness, validates the conformance corpus through the bundle,
and uploads the verified file as a workflow artifact. It never commits generated
output back to a contributor branch.

---

## Breaking change workflow (ADR process)

Breaking changes to Core contracts must not be submitted as direct PRs. Follow the ADR process defined in `CONTRIBUTING.md`:

1. Open an issue describing the change, affected contracts, and migration path.
2. Wait for a 3-day discussion period.
3. Open a PR that includes the contract change, updated payloads, CHANGELOG, version bump, and compatibility matrix update in `docs/VERSIONING.md`.
4. PR merges after maintainer approval; the issue is closed and linked from the CHANGELOG.

---

## Cross-repo impact flagging

For any Core contract change, add a section to the PR description:

```text
## Cross-repo impact
- contextweaver: [describe impact or "none"]
- agent-kernel: [describe impact or "none"]
- ChainWeaver: [describe impact or "none"]
```

If the change affects a contract that a sibling repo produces or consumes, coordination is required.

---

## Local validation commands

Run every applicable check before submitting a PR. CI enforces the same checks.

```bash
# 1. Python tests (with coverage)
cd contracts/python
pip install -e ".[dev]"
pytest --cov --cov-report=term-missing

# 2. Type checking
mypy src/

# 3. JSON schema validation
cd ../..
python -c "import json; [json.load(open(f)) for f in __import__('glob').glob('contracts/json/*.schema.json')]"

# 4. Contracts index freshness (regenerate first if you changed any schema)
python scripts/generate_contracts_index.py --check

# 4a. Offline schema bundle freshness
python scripts/generate_schema_bundle.py --check

# 4b. Contract version string consistency (single source: version.py)
python scripts/check_version_consistency.py

# 5. Markdown lint
# See CONTRIBUTING.md "Markdown Lint" section for the canonical command.

# 6. Conformance suite (corpus + executable invariants + TraceBundle signatures)
python conformance/run.py

# 7. Validate the conformance corpus through the offline bundle
python tests/test_schema_bundle.py
```

If step 4 or 4a fails, regenerate the index and bundle, then commit both results:

```bash
python scripts/generate_contracts_index.py
python scripts/generate_schema_bundle.py
```

---

## Commit conventions

| Prefix | When to use |
| -------- | ------------- |
| `docs:` | Documentation-only changes |
| `contracts:` | Schema or Python type changes |
| `ci:` | Workflow/CI changes |
| `fix:` | Bug fixes in tests, scripts, or docs |

**Mixed changes:** Use the prefix for the most impactful change. Mention the secondary scope in the commit body. Example: `contracts: add optional risk_level field to ChoiceCard` with body noting `Also updates docs/GLOSSARY.md`.

---

## Documentation governance

### When docs must be updated

| Trigger | Docs to update |
| --------- | --------------- |
| New or changed Core contract | CHANGELOG, potentially GLOSSARY if term meaning changes |
| New invariant or boundary change | INVARIANTS.md or BOUNDARIES.md (via ADR), then update AGENTS.md pointer |
| New workflow or validation command | This file (`workflows.md`) |
| New recurring mistake identified | `lessons-learned.md` (see failure-capture workflow there) |
| Review expectations change | `review-checklist.md` |
| New agent-facing guidance added | AGENTS.md documentation map |
| Shared rule, workflow, or invariant changed | Agent-facing docs (`AGENTS.md`, `docs/agent-context/*`) |

### How to avoid duplicate authority

- Each governance rule lives in one file.
- Other files may contain a one-sentence pointer (e.g., "See workflows.md for command details").
- If you find the same rule stated in two files without a clear canonical/pointer relationship, flag it for cleanup.

---

## Update triggers

Update this file when:

- A validation command changes
- The commit convention or PR process changes
- A new documentation governance rule is established
- The ADR process is modified in `CONTRIBUTING.md`
