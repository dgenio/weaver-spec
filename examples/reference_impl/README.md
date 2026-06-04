# Become Weaver-compatible in 30 minutes

A single, runnable reference implementation that exercises **every Core
contract** end-to-end — produce a `RoutingDecision`, mint and verify a signed
`CapabilityToken`-style signature, return a `Frame`, reference a `Handle`, emit a
`TraceEvent`, and gather them into a signed `TraceBundle` — with **nothing from
the sibling repos required**.

> [!NOTE]
> This is an **example**, deliberately placed under `examples/` rather than in
> the `weaver_contracts` package. Per [`AGENTS.md`](../../AGENTS.md) the package
> stays docs + contracts + stdlib dataclasses; this runnable demonstration is
> CI-checked example tooling (it reuses the same `jcs` / `cryptography` /
> `jsonschema` dev dependencies the conformance suite uses) and is never
> published. Copy it into your own project as a starting point — do not import
> it from `weaver_contracts`.

## Run it

```bash
# From the repo root. Installs weaver_contracts + the example's dev deps
# (jcs, cryptography, jsonschema, referencing).
pip install -e "contracts/python[dev]"

python examples/reference_impl/reference_impl.py
```

Expected output:

```text
Weaver reference implementation — contract version 0.6.0

[1] Constructed RoutingDecision, CapabilityToken, PolicyDecision, Frame, Handle, TraceEvent and gathered them into a TraceBundle.
[2] Signed the bundle (alg=ed25519, kid='reference-impl-ephemeral').
[3] Signature verified against the ephemeral public key.
[4] Validated 6 payloads against contracts/json/ schemas.
[5] Invariants I-01 (no raw output in Frames) and I-02 (PolicyDecisions are traced) hold.

Reference implementation: all checks passed.
```

A non-zero exit code means a Core schema, invariant, or signature check failed —
which is exactly what `ci.yml`'s `reference-impl` job guards against, so this
example can never silently drift from the contracts.

## What each step demonstrates

| Step | Contract / rule | Where to read more |
| --- | --- | --- |
| Construct artifacts | The 6 Core types + their construction-time validation | [`contracts/json/`](../../contracts/json), [`core.py`](../../contracts/python/src/weaver_contracts/core.py) |
| Gather into a bundle | `TraceBundle` (Extended audit-chain envelope) | [`docs/TRACE_BUNDLE.md`](../../docs/TRACE_BUNDLE.md) |
| Sign + verify | `CapabilityTokenSignature` over the RFC 8785 (JCS) canonical form | [`docs/SIGNING.md`](../../docs/SIGNING.md) |
| Validate payloads | JSON Schemas are the language-agnostic source of truth | [`contracts/json/README.md`](../../contracts/json/README.md) |
| Assert invariants | I-01 (no raw output in Frames), I-02 (decisions are traced) | [`docs/INVARIANTS.md`](../../docs/INVARIANTS.md) |

## From here to a conformance badge

1. Make your own artifacts validate against the schemas in `contracts/json/`
   (this example shows the wire shape for each).
2. Run the conformance suite — see [`docs/CONFORMANCE.md`](../../docs/CONFORMANCE.md).
3. Emit a machine-readable result and a badge, and (optionally) publish a
   `TraceBundle` to appear on the public scoreboard — see
   [`docs/SELF_CERTIFICATION.md`](../../docs/SELF_CERTIFICATION.md) and
   [`docs/SCOREBOARD.md`](../../docs/SCOREBOARD.md).

## Related

- [`examples/interoperability/`](../interoperability) — the same Core flow as
  documentation-only walkthroughs (happy path + denied path).
- [`docs/INTEGRATION_MAP.md`](../../docs/INTEGRATION_MAP.md) — the inter-repo
  handoff points with payloads at each boundary.
