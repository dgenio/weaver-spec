## Description

<!-- Briefly describe what this PR changes and why. -->

---

## Type of change

<!-- Check all that apply. -->

- [ ] Docs only (no contract changes)
- [ ] Experimental / research contract work (not a stable/Core commitment)
- [ ] Additive normative contract change (must pass the adoption-evidence gate)
- [ ] Breaking contract change (requires an ADR; adoption evidence applies to normative expansion)
- [ ] CI / tooling change

---

## Adoption evidence for normative expansion

<!--
Required for any PR that adds, graduates, or materially expands stable/Core semantics.
Mark N/A only for docs/tooling/experimental work that does not expand normative commitments.
See docs/ADOPTION_GUARDRAILS.md.
-->

- [ ] Two independently designed systems need substantially the same semantics — or N/A
- [ ] At least one external project/organization outside `dgenio` will consume or test the representation — or N/A
- [ ] The issue explains why MCP, A2A, OpenTelemetry, OAuth/OIDC/JOSE, OpenAPI, or another established standard does not already own the concern — or N/A
- [ ] The concrete information loss / integration cost removed by the contract is documented — or N/A
- [ ] Conformance examples/vectors cover independently observed cases — or N/A
- [ ] This work is consistent with the standards-ownership audit (#205) and Core freeze (#206) — or N/A

### Evidence / external implementation links

<!-- Link the issue, independent implementations, design-partner evidence, or upstream standards analysis. Do not count dgenio sibling repos as independent adoption. -->

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

## Deprecations

<!-- If this PR deprecates or removes a field, type, schema, or constraint, update the deprecation register. See docs/DEPRECATIONS.md for the policy (≥1 MAJOR retention rule, removal requires ADR). -->

- [ ] `docs/DEPRECATIONS.md` updated — or N/A (no deprecation in this PR)

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

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/ADOPTION_GUARDRAILS.md](docs/ADOPTION_GUARDRAILS.md) for the full contribution process, adoption-evidence gate, and ADR process for breaking changes.
