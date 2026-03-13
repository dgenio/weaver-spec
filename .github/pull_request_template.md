## Description

<!-- Briefly describe what this PR changes and why. -->

---

## Type of change

<!-- Check all that apply. -->

- [ ] Docs only (no contract changes)
- [ ] Additive contract change (new optional field or new type — non-breaking)
- [ ] Breaking contract change (requires ADR — see [CONTRIBUTING.md](CONTRIBUTING.md))
- [ ] CI / tooling change

---

## Six-artifact checklist

<!-- Required for every Core contract change. Mark N/A if this PR does not touch Core contracts. -->

- [ ] JSON Schema updated (`contracts/json/`) — or N/A
- [ ] Python dataclass updated (`contracts/python/src/weaver_contracts/core.py`) — or N/A
- [ ] Sample payload updated (`examples/sample_payloads/`) — or N/A
- [ ] Roundtrip test updated (`contracts/python/tests/test_roundtrip_examples.py`) — or N/A
- [ ] CHANGELOG entry added (`CHANGELOG.md`) — or N/A
- [ ] Version bumped (`version.py` + `pyproject.toml`) — or N/A

---

## Invariants

- [ ] I have verified that invariants I-01 through I-07 in `docs/INVARIANTS.md` are not violated by this change.

---

## Cross-repo impact

<!-- Core contract changes affect sibling repositories. Check each repo that needs a coordinated update. -->

- [ ] **contextweaver** — needs coordinated update
- [ ] **agent-kernel** — needs coordinated update
- [ ] **ChainWeaver** — needs coordinated update
- [ ] No cross-repo impact

---

## Process

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution process, including the ADR process for breaking changes.
