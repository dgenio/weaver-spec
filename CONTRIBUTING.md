# Contributing to weaver-spec

Thank you for helping improve the Weaver specification. This repo is **documentation + contracts**, so contributions have a direct impact on all downstream implementations.

---

## Pull Request Template

All PRs in this repository use a shared template (`.github/pull_request_template.md`) that includes:

- **Type of change** checkboxes (docs only, additive contract, breaking contract, CI/tooling)
- **Six-artifact checklist** — required for every Core contract change
- **Invariant verification** checkbox (I-01 through I-07)
- **Cross-repo impact** section (contextweaver, agent-kernel, ChainWeaver)

The template is pre-filled automatically when you open a PR on GitHub.

---

## Types of Changes

| Change type | Process |
| ------------- | --------- |
| Typo / clarification in docs | PR with description |
| New doc section or additive contract field | PR with description + update CHANGELOG |
| **Breaking contract change** | ADR process (see below) + major version bump |
| New JSON Schema or Python type (non-breaking) | PR + minor version bump + sample payload |

---

## ADR Process for Breaking Contract Changes

A "breaking contract change" is any modification that would cause existing valid payloads to become invalid, or that removes or renames a required field.

Use the ADR template at [`docs/adr/template.md`](docs/adr/template.md) when documenting a breaking change. See [`docs/adr/README.md`](docs/adr/README.md) for the naming convention.

**Steps:**

1. **Open an issue** describing:
   - What you want to change and why.
   - Which contracts are affected.
   - Migration path for adopters.

2. **Discussion period** — at least 3 business days for feedback from the community.

3. **Open a PR** that includes:
   - An ADR file in `docs/adr/` (copied from `docs/adr/template.md`).
   - The contract change (JSON Schema and/or Python types).
   - Updated sample payloads that validate against the new schema.
   - A `CHANGELOG.md` entry under the new version.
   - A version bump in `contracts/python/src/weaver_contracts/version.py`.
   - Updated `docs/VERSIONING.md` compatibility matrix if needed.

4. **PR merges** after maintainer approval. The issue is closed and linked from the CHANGELOG entry.

---

## Style Guidelines

- **Docs**: concise, technical, unambiguous. No marketing language. Prefer tables and explicit definitions.
- **JSON Schemas**: include `$id`, `title`, `description`, and `required` fields. Keep them small.
- **Python types**: use stdlib only (`dataclasses`, `typing`). No runtime dependencies in `core.py`.
- **Tests**: every new schema must have a sample payload; every new Python type must have a roundtrip test.

---

## Local Development

All commands below assume dev dependencies are installed (`pip install -e ".[dev]"` in `contracts/python/`).

### Python Package Tests

```bash
cd contracts/python
pip install -e ".[dev]"
pytest --cov --cov-report=term-missing
```

### Type Checking

```bash
cd contracts/python
mypy src/
```

### Validate JSON Schemas

```bash
python -c "import json; [json.load(open(f)) for f in __import__('glob').glob('contracts/json/*.schema.json')]"
echo "All schemas are valid JSON"
```

### Markdown Lint

Run from the repository root (not from `contracts/python/`):

```bash
npm install -g markdownlint-cli
markdownlint \
  README.md CONTRIBUTING.md CHANGELOG.md \
  'docs/**/*.md' 'contracts/**/*.md' 'examples/*.md'
```

Rules are configured in `.markdownlint.json` at the repo root.

---

## Commit Messages

Use conventional commit style:

- `docs: ...` — documentation changes
- `contracts: ...` — schema or Python type changes
- `ci: ...` — workflow changes
- `fix: ...` — bug fixes in tests or scripts

---

## Code of Conduct

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
