# Conformance test keyring

`test_keyring.json` holds **public** keys only, used by
[`../run.py`](../run.py) to cryptographically verify signed `TraceBundle`
fixtures (issue #74).

- `conformance-test-ed25519-2026-01` — ed25519 public key for
  [`../fixtures/trace_bundle_signed_valid.json`](../fixtures/trace_bundle_signed_valid.json).
  The matching **private key was generated once and discarded**; it exists only
  to produce that one fixture's signature. No secret material is committed.

Adopters verifying their own bundles supply their own keyring via
`python conformance/run.py --keyring <path>`. See
[../../docs/CONFORMANCE.md](../../docs/CONFORMANCE.md).
