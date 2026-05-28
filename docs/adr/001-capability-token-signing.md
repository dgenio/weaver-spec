# ADR 001: CapabilityToken canonical form (RFC 8785 JCS) and signing spec — Extended-first

**Status:** accepted

---

## Context

`docs/INVARIANTS.md` and the schema description for `CapabilityToken` describe
the token as "signed", but no field, no algorithm registry, and no verification
rule existed in the spec — the word was aspirational (see `AGENTS.md` →
"Forbidden behaviors" #5 and "Domain clarifications" → CapabilityToken).
Sibling-repo authorization teams cannot ship tamper-evident tokens without a
concrete spec covering:

1. A deterministic canonical form for the token payload.
2. A signature object with explicit algorithm, key identifier, and signature
   bytes.
3. Verification rules that downstream consumers (contextweaver, ChainWeaver,
   third-party auditors) follow identically.

Tracked in issue #44.

## Decision

Define token signing as an **Extended** contract first; promote to Core only in
v1.0.0 once all three siblings adopt it and interop tests are green
(see issue #48, sub-ADR 005).

1. **Canonicalization.** The payload to be signed is the CapabilityToken JSON
   object with the `x_weaver_signature` field removed, then canonicalized via
   [RFC 8785 JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785).
2. **Algorithm registry.** Initial algorithms: `ed25519` and `es256` (both
   produce 64-byte signatures). The registry lives in `docs/SIGNING.md`.
   Verifiers MUST reject unknown algorithms.
3. **Signature object.** A new Extended contract `CapabilityTokenSignature`
   carries `alg`, `kid`, `sig`, `canonicalization`, and an optional
   informational `signed_at`. Its JSON Schema is
   `contracts/json/extended/capability_token_signature.schema.json`.
4. **Attachment.** The signature is attached to a `CapabilityToken` under the
   namespaced extension key `x_weaver_signature`. Core schemas are unchanged.
   Tokens without `x_weaver_signature` remain valid in v0.x (signing is opt-in).
5. **Verification flow:** documented step-by-step with test vectors in
   `docs/SIGNING.md`. Verifiers strip `x_weaver_signature`, JCS-canonicalize the
   remaining object, then verify `sig` against `kid` using `alg`.

## Consequences

**Easier:**

- `agent-kernel` and downstream auditors can ship tamper-evident tokens and
  detect MITM tampering.
- The word "signed" in glossary/schema descriptions becomes accurate when
  `x_weaver_signature` is present.
- Sibling repos that only pass tokens through (contextweaver, ChainWeaver) do
  not need to verify — they preserve the extension unchanged.

**Harder:**

- Producers and verifiers must use a real JCS implementation; ad-hoc
  `json.dumps(sort_keys=True)` is **not** sufficient (it does not normalize
  numbers or string escapes per I-JSON).
- Key management (issuing `kid` values, rotating keys) is out of scope for the
  spec; each adopter manages it.

## Affected Contracts

| Contract | Change type | Description |
| ---------- | ------------- | ------------- |
| `extended/capability_token_signature.schema.json` | new schema | Detached-signature shape |
| `weaver_contracts.extended.CapabilityTokenSignature` | new dataclass | Mirrors the schema |
| `examples/sample_payloads/capability_token_signature.json` | new payload | Standalone signature sample |
| `examples/sample_payloads/capability_token_signed.json` | new payload | CapabilityToken with `x_weaver_signature` attached |
| `capability_token.schema.json` | unchanged | `additionalProperties: true` already accepts the `x_weaver_signature` extension |

## Migration Path

- **agent-kernel:** implement issuance + verification per `docs/SIGNING.md`.
  Begin issuing signed tokens once a `kid` registry is configured.
- **contextweaver / ChainWeaver:** pass `x_weaver_signature` through unchanged.
  No validation required.
- **Existing unsigned tokens:** remain valid for v0.x. v1.0.0 may promote
  signing to Core (deferred to issue #48 ADR 005).

## Cross-Repo Impact

| Repository | Impact | Coordination required? |
| ------------ | -------- | ------------------------ |
| contextweaver | Passthrough only; do not strip `x_weaver_signature`. | no |
| agent-kernel | Implement issuance + verification. | yes — issuance and key-management plan |
| ChainWeaver | Passthrough only. | no |

## Alternatives considered

- **JOSE/JWS.** Heavy; binary base64 wrapping breaks the JSON-native model and
  doubles payload size. Rejected.
- **COSE.** Designed for CBOR; mismatch for JSON-native contracts. Rejected.
- **`json.dumps(sort_keys=True)` ad-hoc.** Does not normalize numbers, does not
  restrict to I-JSON; spec would silently break across language runtimes.
  Rejected.
- **JCS (RFC 8785).** Explicit interop guarantees, reference implementation +
  test vectors at <https://github.com/cyberphone/json-canonicalization>.
  **Selected.**

## References

- RFC 8785 — JSON Canonicalization Scheme (JCS): <https://www.rfc-editor.org/rfc/rfc8785>
- JCS reference implementation + test vectors: <https://github.com/cyberphone/json-canonicalization>
- Issue #44 — original proposal.
- Issue #48 sub-ADR 005 — promotion to Core in v1.0.0.
