# Signing CapabilityTokens

> [!IMPORTANT]
> This document is normative for the Extended contract
> `CapabilityTokenSignature`. The canonicalization rule and algorithm
> registry below are mandatory for any producer or verifier claiming
> compliance with weaver-spec token signing. See
> [ADR 001](adr/001-capability-token-signing.md) for the design decision.

CapabilityToken signing is **Extended** in v0.x: tokens without a signature
remain valid, and routing/orchestration layers must pass the signature
extension through unchanged. Promotion to Core is tracked under issue #48
sub-ADR 005.

---

## Canonicalization

The payload to be signed is the CapabilityToken JSON object with the
`x_weaver_signature` field **removed**, then canonicalized via
[RFC 8785 JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785).

JCS guarantees:

- UTF-8 output.
- Member keys sorted by code point.
- Numbers serialized per ES6 `Number.prototype.toString` (no trailing zeros,
  shortest unambiguous form).
- I-JSON restrictions applied.

Ad-hoc `json.dumps(sort_keys=True)` is **not** equivalent — it does not
normalize numbers, escape sequences, or insignificant whitespace consistently.
Use a real JCS implementation (Python: [jcs](https://pypi.org/project/jcs/);
JavaScript: [canonicalize](https://www.npmjs.com/package/canonicalize); reference
test vectors: <https://github.com/cyberphone/json-canonicalization>).

---

## Algorithm registry

The `alg` field of `CapabilityTokenSignature` MUST be one of the values below.
Verifiers MUST reject unknown algorithms.

| `alg` | Public-key algorithm | Signature encoding | Signature size |
| ----- | -------------------- | ------------------ | -------------- |
| `ed25519` | Ed25519 ([RFC 8032](https://www.rfc-editor.org/rfc/rfc8032)) | Raw 64-byte signature, base64url (no padding) | 64 bytes / 86 base64url chars |
| `es256` | ECDSA over NIST P-256 with SHA-256 | IEEE P1363 concatenated `r\|\|s`, 64 bytes, base64url (no padding) | 64 bytes / 86 base64url chars |

Adding a new algorithm to this registry is an additive change (MINOR bump);
removing one is breaking.

`canonicalization` MUST be `JCS`. Other canonicalization schemes are not in
the registry and must be rejected.

---

## Producing a signature

```text
input:  token (a CapabilityToken JSON object), alg, kid, private_key
output: token_with_signature

1. work = deep_copy(token)
2. delete work["x_weaver_signature"]      # signing input excludes the signature
3. canonical_bytes = jcs.canonicalize(work)
4. signature_bytes = sign(alg, private_key, canonical_bytes)
5. token["x_weaver_signature"] = {
     "alg": alg,
     "kid": kid,
     "sig": base64url_no_pad(signature_bytes),
     "canonicalization": "JCS",
     "signed_at": now_iso8601()       # optional, informational
   }
6. return token
```

---

## Verifying a signature

```text
input:  token, keyring (kid -> public_key)
output: bool

1. signature = token.get("x_weaver_signature")
2. if signature is None:                     return False  # unsigned
3. if signature["alg"]    not in REGISTRY:   return False  # unknown alg
4. if signature["canonicalization"] != "JCS": return False  # wrong canonical
5. public_key = keyring.get(signature["kid"])
6. if public_key is None:                    return False  # unknown key
7. work = deep_copy(token)
8. delete work["x_weaver_signature"]
9. canonical_bytes = jcs.canonicalize(work)
10. signature_bytes = base64url_decode_no_pad(signature["sig"])
11. return verify(signature["alg"], public_key, canonical_bytes, signature_bytes)
```

A verifier that returns `True` MAY then apply additional invariant checks
(I-06 scope non-empty, `expires_at` in the future, etc.) — these are
independent of signature verification.

---

## Test vectors

To produce repeatable interop test vectors, regenerate from the sample payload
`examples/sample_payloads/capability_token_signed.json` after stripping
`x_weaver_signature` and running the chosen JCS implementation. The JCS
reference repository (linked above) ships vectors that exercise every
canonicalization edge case (number formatting, surrogate pairs, etc.); sibling
repos should run those vectors as part of their interop suite.

The sample payload's `sig` value is illustrative only — it was not produced
from a real key pair. Replace it with a vector from your own keyring during
adoption.

---

## Trust model

> [!IMPORTANT]
> This section states what a verified signature does and does not guarantee. It
> is normative for adopters reasoning about the signing/conformance path (#156).

**What a valid signature attests.** A signature that verifies proves exactly
two things: (1) **integrity** — the JCS-canonical form of the payload (with
`x_weaver_signature` / `signature` removed) has not changed since signing; and
(2) **origin** — it was produced by the private key whose public key the
verifier holds under `kid`. Nothing more.

**What it does NOT attest.**

- **Correctness or safety.** A signed `TraceBundle` or `CapabilityToken` is
  authentic, not *correct*. Signing says who produced the bytes, not that the
  decision they encode was sound.
- **Freshness / replay.** A detached signature carries no nonce or expiry of its
  own. `signed_at` is informational and unverified. A captured signed payload
  stays verifiable forever; bound freshness at the payload layer (a
  `CapabilityToken`'s `expires_at` / `single_use`, invariant I-06) or with a
  transport nonce, not via the signature.
- **Confidentiality.** Signing is integrity + authentication, never encryption
  (see below).

**Trust is rooted in keyring distribution.** Verification is only as trustworthy
as the mapping from `kid` to public key. Distributing and rotating that keyring
is the adopter's responsibility (see *What is out of scope*); a signature
verified against an attacker-controlled keyring proves nothing.

**Unknown key means "not verified", not "trusted".** The strict verifier in
[Verifying a signature](#verifying-a-signature) returns `False` for a `kid` that
is absent from the keyring — an unknown key is a verification *failure* for a
verifier that must decide accept/reject. The conformance runner
(`conformance/run.py:check_trace_bundle`) instead reports an unknown `kid` as
**skipped** — it validates the signature *envelope* (shape, algorithm registry,
canonicalization) but records that cryptographic verification did not run,
because the runner is a **conformance report**, not an authorization gate: it
must not claim provenance it did not check, and it must not fail a bundle merely
because the report host lacks the signer's key. Both behaviours share the same
rule — **an unknown key is never treated as verified** — they differ only in
what an unverifiable signature means for the caller: reject (a gate) versus
report-as-unchecked (a scoreboard). See
[CONFORMANCE.md](CONFORMANCE.md#signature-verification-74) and
[SELF_CERTIFICATION.md](SELF_CERTIFICATION.md).

## What is out of scope

- **Key management.** Issuing `kid` values, rotating keys, distributing
  public keys to verifiers — each adopter manages these. Recommended: short
  rotation windows aligned with token expiry, public-key distribution via
  a JWKS-style endpoint.
- **Revocation.** Signed tokens remain valid until `expires_at`. Use
  `single_use: true` for one-shot tokens; rely on revocation lists or short
  expiries for the rest.
- **Encryption.** Signing is integrity + authentication, not confidentiality.
  Tokens MUST NOT contain secrets in cleartext.

---

## Related

- ADR 001: [adr/001-capability-token-signing.md](adr/001-capability-token-signing.md)
- Extended schema: `contracts/json/extended/capability_token_signature.schema.json`
- Extended dataclass: `weaver_contracts.extended.CapabilityTokenSignature`
- Issue #44 — original proposal.
- Issue #48 sub-ADR 005 — promotion to Core in v1.0.0.
