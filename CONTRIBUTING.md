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

A "breaking contract change" is any modification that would cause existing valid payloads to become invalid, that removes or renames a required field, or that weakens an existing schema constraint (for example, loosening an `enum` or removing a `minLength`) even if existing payloads remain valid.

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

### Deprecating or removing a field

Deprecations and removals are governed by [`docs/DEPRECATIONS.md`](docs/DEPRECATIONS.md):

- A deprecated field, type, or constraint must remain in Core for **at least one full MAJOR version** before it may be removed.
- A PR that deprecates an item must add a row to the register in the same PR.
- A PR that removes a deprecated item must reference the existing register row and move it to the **Removed** section in the same PR. Removals are otherwise blocked.

---

## Style Guidelines

- **Docs**: concise, technical, unambiguous. No marketing language. Prefer tables and explicit definitions. Mark binding requirements with `> [!IMPORTANT]` callouts and explanatory notes with `> [!NOTE]` callouts — see [docs/DOCS_CONVENTIONS.md](docs/DOCS_CONVENTIONS.md) for the full markup convention.
- **JSON Schemas**: include `$id`, `title`, `description`, and `required` fields. Keep them small.
- **Python types**: use stdlib only (`dataclasses`, `typing`). No runtime dependencies in `core.py`.
- **Tests**: every new schema must have a sample payload; every new Python type must have a roundtrip test.

---

## Library dependency constraints

`weaver_contracts` is a **library**, so it must not over-constrain the adopters that depend on it. The package is stdlib-only today; keep it that way, and if a runtime dependency is ever genuinely required, follow these rules:

- **Lower bounds only.** Declare `dependency>=X.Y` (the minimum version you actually rely on). Never pin an exact version (`==`) and never add a speculative upper-bound cap (`<N`). Caps cause resolver conflicts in adopter environments and are only justified by a *known* incompatibility, documented inline.
- **Supported Python is a lower bound too.** `requires-python = ">=3.10"` (no upper cap). The trove `classifiers` in `pyproject.toml` and the CI matrix must list every supported minor (currently **3.10–3.14**); keep all three in sync (the `test_packaging_metadata.py` check enforces classifier ⟷ `requires-python` alignment).
- **When the first runtime dependency is added**, add in the same PR: (1) a floor job that installs the lowest declared versions (e.g. `uv pip install --resolution lowest-direct`, or a `constraints-min.txt`) so the lower bounds are actually tested, and (2) a scheduled latest/pre-release job (`pip install --pre -U`, allow-failure) to catch upstream breakage early. Until then these jobs are moot — the stdlib-only smoke step in CI is the floor.

The `weaver-stack` umbrella meta-package (`packaging/weaver-stack/`) is the **deliberate exception**: a meta-package's job is to pin a known-compatible set, so it may use tight pins. That tightness lives only there — never in `weaver_contracts` itself. See its README for the "convenience, not coupling" stance.

---

## Local Development

All commands below assume dev dependencies are installed (`pip install -e ".[dev]"` in `contracts/python/`).

### Pre-commit Hooks (recommended)

Install [pre-commit](https://pre-commit.com/) once to run the local validation gates automatically on `git commit` (and the full pytest suite on `git push`):

```bash
pip install pre-commit
pre-commit install                # install commit-stage hooks
pre-commit install --hook-type pre-push   # install push-stage hooks
```

Run all hooks against the full repo on demand:

```bash
pre-commit run --all-files
pre-commit run --all-files --hook-stage pre-push
```

The hooks mirror the CI gates: JSON schema field validation, contracts-index freshness, `markdownlint-cli2`, `yamllint`, and (on push) the `weaver_contracts` pytest suite. See `.pre-commit-config.yaml` for the full hook list.

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

### Contracts Index Freshness

The content-addressed index in `well-known/contracts.json` is regenerated by a stdlib-only script. Run from repo root after any change to `contracts/json/`:

```bash
python scripts/generate_contracts_index.py          # regenerate in place
python scripts/generate_contracts_index.py --check  # CI uses this to fail on stale index
```

### Markdown Lint

Run from the repository root (not from `contracts/python/`):

```bash
npm install -g markdownlint-cli2@0.14.0
markdownlint-cli2 \
  README.md CONTRIBUTING.md CHANGELOG.md CHARTER.md \
  'docs/**/*.md' 'contracts/**/*.md' 'examples/**/*.md' 'packaging/**/*.md' '.github/**/*.md'
```

Rules are configured in `.markdownlint.json` at the repo root. CI, the
`markdownlint-cli2` pre-commit hook, and this command all use the same engine
(`markdownlint-cli2`) and the same config (#140).

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
