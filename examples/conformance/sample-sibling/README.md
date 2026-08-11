# Sample downstream conformance consumer

This directory is a **test fixture/template**, not an implementation or adopter.
It proves that the public reusable workflow validates a caller-owned bundle rather
than merely re-running the `weaver-spec` repository's own corpus.

## Repository layout

A downstream repository publishes its conformance artifact at the well-known
path:

```text
.well-known/
  conformance.json
```

The sample fixture in this directory mirrors that layout.

## Copy-paste GitHub Actions job

With the well-known path above, the caller needs only the reusable-workflow job:

```yaml
jobs:
  weaver-conformance:
    uses: dgenio/weaver-spec/.github/workflows/conformance.yml@<immutable-ref>
```

Replace `<immutable-ref>` with a reviewed Weaver Spec release tag or exact commit
SHA. Do not use a mutable branch for a gating compatibility claim.

The called workflow:

1. checks out the **caller** repository;
2. separately checks out the immutable `weaver-spec` source used for validation;
3. reads the caller's `.well-known/conformance.json`;
4. runs the external-bundle conformance path against that exact artifact.

If a repository uses a different path, pass it explicitly:

```yaml
jobs:
  weaver-conformance:
    uses: dgenio/weaver-spec/.github/workflows/conformance.yml@<immutable-ref>
    with:
      bundle-path: path/to/conformance.json
      spec-ref: <immutable-weaver-spec-ref>
```

`spec-ref` defaults to the immutable 0.8.0 source commit while the release/tag
integrity gap is tracked in issue #202. Once a matching immutable release is
available, prefer the release tag.

## What a pass means

A pass means only that the submitted artifact satisfies the schemas/invariants
checked by the selected conformance version. It is **not** security
certification, production-readiness certification, or evidence of independent
adoption.
