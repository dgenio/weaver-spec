# Conformance

> [!NOTE]
> This document describes the **build-time conformance suite** under
> [`conformance/`](../conformance). The suite is CI tooling, not part of the
> `weaver_contracts` package: it is never imported by the package and never
> published. It defines what "spec-compliant" means as a runnable check.

The conformance runner answers one question: *does a payload (or a sibling
repo's emitted artifact) honour the Weaver contracts and invariants?* It goes
beyond JSON Schema validation by also asserting the cross-field invariants that
Schema cannot express.

## What it checks

| Layer | Source | Meaning |
| ----- | ------ | ------- |
| Positive corpus | [`conformance/corpus.yaml`](../conformance/corpus.yaml) `positive` | Each payload **must** validate against its schema. |
| Negative corpus | `conformance/corpus.yaml` `negative` | Each payload **must** be rejected — by JSON Schema (`by: schema`) or, for schema-valid payloads, by an invariant (`by: invariant`). |
| Invariants | [`conformance/invariants.yaml`](../conformance/invariants.yaml) | Executable assertions for **I-01, I-02, I-04, I-06** (see [INVARIANTS.md](INVARIANTS.md)). |
| TraceBundle integrity | runner (`#74`) | Recomputes the RFC 8785 (JCS) canonical form excluding `signature`; validates the detached-signature envelope; cryptographically verifies the signature when the signing key is in the supplied keyring. Adversarial envelopes — a missing `kid`, a non-registry `canonicalization`, or a nested artifact tampered after signing — are rejected (`#133`). |

`invariants.yaml` is intentionally a **named-check registry**, not an embedded
expression language: each block binds an invariant `id` to a real Python check
in [`conformance/run.py`](../conformance/run.py), so a sibling repo running the
manifest gets the same verdict this repo does. The invariant descriptions point
to [INVARIANTS.md](INVARIANTS.md) and do not restate the normative text.

### Invariant coverage

I-01, I-02, I-04, and I-06 are statically checkable and are enforced here.
**I-03, I-05, and I-07 are layer-behaviour invariants** (routing, ingestion, and
orchestration runtime); they cannot be asserted against a static artifact and
are checked by the sibling-repo conformance harnesses instead.

## Running locally

```bash
python conformance/run.py
```

The runner exits non-zero on any positive failure, negative acceptance,
invariant violation, or signature failure. By default it loads the test keyring
at `conformance/keyring/test_keyring.json`; pass `--keyring <path>` to verify
bundles signed with your own keys.

Dependencies (`jsonschema`, `referencing`, `PyYAML`, `jcs`, `cryptography`) are
declared as the `dev` extra of the Python package:

```bash
pip install -e "contracts/python[dev]"
```

## Signature verification (`#74`)

For every `TraceBundle` the runner recomputes the JCS canonical form and, when a
`signature` is present, validates it against the
`CapabilityTokenSignature` schema and the algorithm registry, then verifies it
cryptographically **if** the `kid` resolves in the keyring. The procedure mirrors
[SIGNING.md](SIGNING.md). When the key is unknown the result is honestly
reported as *skipped* — never as verified.

The fixture [`conformance/fixtures/trace_bundle_signed_valid.json`](../conformance/fixtures/trace_bundle_signed_valid.json)
carries a **real** ed25519 signature (its public key is in
`conformance/keyring/test_keyring.json`; the private key was discarded after
generation), so the verification path is exercised end-to-end. The illustrative
sample in `examples/sample_payloads/trace_bundle_signed.json` keeps its
documented placeholder signature and is reported as *skipped*.

## Adopting it in a sibling repo

The suite ships as a reusable workflow. Add one job to your CI, pinned to a
released tag:

```yaml
jobs:
  weaver-conformance:
    uses: dgenio/weaver-spec/.github/workflows/conformance.yml@v0.6.0
```

This runs the spec repo's own corpus against the published schemas. To assert
conformance of *your* emitted artifacts, point the runner at your payloads via a
local `corpus.yaml` (same shape) and your own keyring.

## Checking a single external bundle

To conformance-check one externally produced `TraceBundle` (schema validation +
TraceBundle integrity/signature + I-01/I-02) instead of the built-in corpus:

```bash
python conformance/run.py --bundle path/to/bundle.json
```

This is the engine the [scoreboard](SCOREBOARD.md) runs against each sibling's
published bundle. Because that input is semi-trusted (it comes from another
repo), the external path is hardened (#158): a bundle larger than **5 MiB** or
that is not a JSON object is rejected with a clear `input:` failure rather than
a traceback, and at most that many bytes are read before parsing. The scoreboard
enforces the same limit on the bundles it fetches over the network.

## Machine-readable result and badge

The runner can emit a machine-readable conformance result and a shields.io
endpoint badge from the same run, so a published badge cannot disagree with the
verdict that produced it:

```bash
python conformance/run.py \
  --emit-result conformance-result.json \
  --emit-badge weaver-compatible.json
```

The result is CI tooling output, not a Weaver runtime contract, but it is a
stable interchange shape: it validates against
[`contracts/json/extended/conformance_result.schema.json`](../contracts/json/extended/conformance_result.schema.json)
(`#116`), so the badge, the scoreboard, and any sibling reading it share one
schema and cannot drift. Alongside the flat `failure_detail` strings the result
carries `failure_records` — a structured per-failure view (`kind`, `message`,
and, where known, `payload` / `schema` / `keyword` / `path` / `invariant_id`)
that an agent can map straight to the offending fixture or field (`#145`). See
[SELF_CERTIFICATION.md](SELF_CERTIFICATION.md) for the badge flow and
[SCOREBOARD.md](SCOREBOARD.md) for the public per-repo scoreboard.

## Validating at scale

Compiling a JSON Schema validator is far more expensive than running one.
Adopters that validate many payloads — a kernel firewalling every tool call, a
batch validating a corpus — should **compile once and reuse**, not build a
validator per payload. The runner does this internally: `load_schemas()` builds
the schema registry once, and `_validator_for()` caches one compiled
`Draft202012Validator` per schema `$id`, so validating N payloads against the
same schema compiles it once, not N times. Mirror that pattern in your own
integration rather than constructing a validator inside a per-payload loop.

## Extending the conformance suite

The runner is deliberately a single, data-driven file. Extend it through
**data, not new code paths**:

- **A new positive or negative payload** is a new entry in
  [`corpus.yaml`](../conformance/corpus.yaml) plus a fixture file — no runner
  change. A schema-level negative declares `by: schema` and the `violates`
  keyword/target; an invariant-level negative declares `by: invariant` and the
  invariant `id`.
- **A new invariant** registers a named check in `BUNDLE_INVARIANTS` (or the
  relevant dispatch in `run()`) and adds a block to
  [`invariants.yaml`](../conformance/invariants.yaml) binding the `id` to that
  named check. Avoid bespoke per-fixture branches.

A consistency test (`test_conformance.py`) enforces this: every `corpus.yaml`
schema name must resolve to a loaded schema, and every `trace_bundle`-scoped
invariant assertion must resolve to a registered check — so a typo or an
orphaned entry fails CI rather than silently skipping a check.

## Related

- [INVARIANTS.md](INVARIANTS.md) — the normative I-01..I-07 definitions.
- [SIGNING.md](SIGNING.md) — canonicalization + signature algorithm registry.
- [TRACE_BUNDLE.md](TRACE_BUNDLE.md) — the audit-chain envelope.
- [SELF_CERTIFICATION.md](SELF_CERTIFICATION.md) — the "Weaver-compatible" badge.
- [SCOREBOARD.md](SCOREBOARD.md) — the public conformance scoreboard.
- [examples/reference_impl/](../examples/reference_impl/) — runnable reference.
- [AGENTS.md](../AGENTS.md) — repo scope rule covering `conformance/`.
