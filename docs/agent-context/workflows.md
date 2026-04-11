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

Extended contracts do **not** currently have JSON Schemas; the `contracts/json/` directory is Core-only.
When modifying an Extended contract, complete all of the following in a single PR:

1. **Update the Python dataclass** in `contracts/python/src/weaver_contracts/extended.py`.
2. **Update or create a sample payload** in `examples/sample_payloads/`.
3. **Add or update a roundtrip test** in `contracts/python/tests/test_roundtrip_examples.py`.
4. **Add a CHANGELOG entry** under the appropriate version section.
5. **Bump the version** in both `contracts/python/src/weaver_contracts/version.py` and `contracts/python/pyproject.toml`.

Breaking changes are allowed in MINOR versions for Extended contracts.

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

Run all four before submitting any PR. CI enforces all four.

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

# 4. Markdown lint
# See CONTRIBUTING.md "Markdown Lint" section for the canonical command.
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
