# JavaScript conformance reference

This directory contains a **second-language reference implementation** of the
static Weaver conformance corpus.

It exists to test whether the specification's schemas, fixtures, invariants, and
signature vectors can be implemented independently of the Python runner. It is
CI tooling only: it is not published as a runtime package and it is not evidence
of independent ecosystem adoption because it is maintained in the same
repository by the same project.

## Inputs

The JavaScript runner reads the same repository-owned inputs as
`conformance/run.py`:

- `contracts/json/**/*.schema.json`
- `conformance/corpus.yaml`
- `conformance/invariants.yaml`
- `conformance/keyring/test_keyring.json`
- the same positive/negative/signed fixtures

It does not import or execute Python code.

## Checks

The current implementation covers:

- all positive JSON Schema corpus cases;
- all schema-negative cases, including the declared failure keyword/target;
- I-01 (`Frame` does not carry raw-output keys);
- I-02 (every `PolicyDecision` in a bundle is traced);
- I-04 (Core required-field baseline);
- I-06 (scoped + expiring/single-use capability tokens);
- TraceBundle signature-envelope checks;
- cryptographic verification of the shared Ed25519 signed fixture when the key
  is present in the common test keyring.

An unknown signing key is reported with the same conformance-report semantics as
the Python runner: it is not treated as verified, but its absence from the local
keyring does not by itself turn an otherwise valid conformance report into a
security gate.

## Run locally

```bash
cd conformance/javascript
npm ci --ignore-scripts --no-audit --no-fund
npm run conformance
```

The `Cross-language Conformance` GitHub Actions workflow requires both the Python
and JavaScript reference implementations to pass the same corpus.

## What this does not prove

Two implementations written under one project prove **feasibility and spec
clarity**, not independent adoption. The pre-v1 gate in issue #209 still requires
an independently maintained implementation/validator before language-neutral
conformance can be used as external standards evidence.

A future iteration should also make expected per-vector verdicts fully
machine-readable, so independent validators can compare detailed outcomes rather
than only sharing a corpus and agreeing on overall pass/fail.
