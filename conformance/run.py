#!/usr/bin/env python3
"""Weaver conformance runner.

This is build-time / CI conformance tooling, not runtime code. It is NOT part of
the ``weaver_contracts`` package, is never imported by it, and is never
published. Sibling repos invoke it through the reusable workflow
``.github/workflows/conformance.yml`` to declare conformance in one CI line; see
docs/CONFORMANCE.md.

What it checks (issues #43 and #74):

* Positive corpus  — every payload in ``conformance/corpus.yaml`` ``positive``
  validates against its JSON Schema.
* Negative corpus  — every ``negative`` payload is rejected, either by JSON
  Schema (``by: schema``) or, for schema-valid payloads, by the invariant named
  in ``violates`` (``by: invariant``).
* Invariants       — the executable assertions declared in
  ``conformance/invariants.yaml`` (I-01, I-02, I-04, I-06) hold for the relevant
  positive payloads / schemas. I-03/I-05/I-07 are layer-behaviour invariants
  checked by sibling harnesses (see docs/CONFORMANCE.md).
* TraceBundle integrity (#74) — for every TraceBundle the runner recomputes the
  RFC 8785 (JCS) canonical form excluding ``signature``; when a signature is
  present it validates the detached-signature envelope and, if the signing key
  is in the supplied keyring, cryptographically verifies it.

Exit code is non-zero on any positive failure, negative acceptance, invariant
violation, or signature failure.

Usage::

    python conformance/run.py
    python conformance/run.py --keyring conformance/keyring/test_keyring.json
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import jcs
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
EXTENDED_SCHEMA_DIR = CORE_SCHEMA_DIR / "extended"
CONF_DIR = REPO_ROOT / "conformance"
DEFAULT_KEYRING = CONF_DIR / "keyring" / "test_keyring.json"

# Frames must never carry raw tool output (I-01). These keys are treated as raw
# passthrough and are forbidden on any Frame inside a bundle.
FORBIDDEN_FRAME_KEYS = frozenset({"raw_output", "raw", "raw_result", "tool_output"})

SIGNATURE_ALG_REGISTRY = frozenset({"ed25519", "es256"})


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

def load_schemas() -> tuple[dict[str, dict], Registry]:
    """Return (schemas_by_stem, registry) for all Core + Extended schemas."""
    schemas_by_stem: dict[str, dict] = {}
    registry = Registry()
    for path in sorted(CORE_SCHEMA_DIR.glob("*.schema.json")) + sorted(
        EXTENDED_SCHEMA_DIR.glob("*.schema.json")
    ):
        schema = json.loads(path.read_text(encoding="utf-8"))
        stem = path.name.removesuffix(".schema.json")
        schemas_by_stem[stem] = schema
        if "$id" in schema:
            registry = registry.with_resource(
                uri=schema["$id"],
                resource=Resource(contents=schema, specification=DRAFT202012),
            )
    return schemas_by_stem, registry


def schema_errors(payload: dict, schema: dict, registry: Registry) -> list[str]:
    """Return a sorted list of validation error messages (empty == valid)."""
    validator = Draft202012Validator(
        schema, registry=registry, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    out = []
    for err in errors:
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out


# ---------------------------------------------------------------------------
# Invariant checks (the named-check registry referenced by invariants.yaml)
# ---------------------------------------------------------------------------

def frames_have_no_raw_output(bundle: dict) -> list[str]:
    """I-01: no Frame in the bundle carries raw tool output."""
    violations = []
    for i, frame in enumerate(bundle.get("frames", [])):
        present = sorted(FORBIDDEN_FRAME_KEYS & set(frame))
        if present:
            fid = frame.get("frame_id", f"index {i}")
            violations.append(f"Frame {fid!r} carries forbidden raw-output key(s): {present}")
    return violations


def policy_decisions_are_traced(bundle: dict) -> list[str]:
    """I-02: every PolicyDecision has a matching TraceEvent (decision_id linkage)."""
    traced = {
        te.get("decision_id")
        for te in bundle.get("trace_events", [])
        if te.get("decision_id") is not None
    }
    violations = []
    for pd in bundle.get("policy_decisions", []):
        did = pd.get("decision_id")
        if did not in traced:
            violations.append(f"PolicyDecision {did!r} has no matching TraceEvent")
    return violations


def capability_token_scoped(token: dict) -> list[str]:
    """I-06: a CapabilityToken is scoped and either single-use or expiring."""
    violations = []
    scope = token.get("scope")
    if not isinstance(scope, list) or not scope:
        violations.append("scope is empty or missing; unbounded scope is not permitted")
    if not (token.get("single_use") is True or token.get("expires_at")):
        violations.append("token is neither single_use nor has expires_at")
    return violations


def core_required_surface_stable(baseline: dict, schemas_by_stem: dict[str, dict]) -> list[str]:
    """I-04: the Core required-field surface matches the pinned baseline."""
    violations = []
    for stem, expected in baseline.items():
        schema = schemas_by_stem.get(stem)
        if schema is None:
            violations.append(f"Core schema {stem!r} not found")
            continue
        actual = list(schema.get("required", []))
        if actual != list(expected):
            violations.append(
                f"{stem}: required surface drifted — expected {expected}, found {actual}"
            )
    return violations


BUNDLE_INVARIANTS: dict[str, Callable[[dict], list[str]]] = {
    "frames_have_no_raw_output": frames_have_no_raw_output,
    "policy_decisions_are_traced": policy_decisions_are_traced,
}


# ---------------------------------------------------------------------------
# TraceBundle signature verification (#74)
# ---------------------------------------------------------------------------

def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def load_keyring(path: Optional[Path]) -> dict[str, dict]:
    """Return kid -> key entry from a keyring JSON file (empty if none)."""
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k["kid"]: k for k in data.get("keys", [])}


def _crypto_verify(alg: str, key_entry: dict, message: bytes, sig: bytes) -> bool:
    """Cryptographically verify a signature. Raises if the crypto lib is absent."""
    pub_bytes = _b64url_decode(key_entry["public_key_b64url"])
    if alg == "ed25519":
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(sig, message)
        return True
    if alg == "es256":
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec, utils

        pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), pub_bytes)
        r = int.from_bytes(sig[:32], "big")
        s = int.from_bytes(sig[32:], "big")
        pub.verify(utils.encode_dss_signature(r, s), message, ec.ECDSA(hashes.SHA256()))
        return True
    raise ValueError(f"unsupported alg {alg!r}")


def check_trace_bundle(
    bundle: dict,
    schemas_by_stem: dict[str, dict],
    registry: Registry,
    keyring: dict[str, dict],
) -> tuple[list[str], list[str]]:
    """Return (errors, notes) for a TraceBundle's integrity + signature (#74)."""
    errors: list[str] = []
    notes: list[str] = []

    # Recompute the JCS canonical form excluding `signature` (always).
    unsigned = {k: v for k, v in bundle.items() if k != "signature"}
    try:
        canonical = jcs.canonicalize(unsigned)
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"JCS canonicalization failed: {exc}")
        return errors, notes

    signature = bundle.get("signature")
    if signature is None:
        notes.append("unsigned bundle (canonical form recomputed)")
        return errors, notes

    # Validate the detached-signature envelope against its Extended schema.
    sig_errs = schema_errors(signature, schemas_by_stem["capability_token_signature"], registry)
    if sig_errs:
        errors.extend(f"signature envelope invalid: {e}" for e in sig_errs)
    if signature.get("alg") not in SIGNATURE_ALG_REGISTRY:
        errors.append(f"signature alg {signature.get('alg')!r} not in registry")
    if signature.get("canonicalization", "JCS") != "JCS":
        errors.append("signature canonicalization must be JCS")
    if errors:
        return errors, notes

    kid = signature["kid"]
    key_entry = keyring.get(kid)
    if key_entry is None:
        notes.append(f"signature envelope valid; crypto verify skipped (kid {kid!r} not in keyring)")
        return errors, notes
    try:
        _crypto_verify(signature["alg"], key_entry, canonical, _b64url_decode(signature["sig"]))
        notes.append(f"signature cryptographically verified (kid {kid!r})")
    except ImportError:  # pragma: no cover - cryptography is a declared dep
        notes.append("crypto verify skipped (cryptography not installed)")
    except Exception as exc:
        errors.append(f"signature verification FAILED for kid {kid!r}: {exc}")
    return errors, notes


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(keyring_path: Optional[Path]) -> int:
    schemas_by_stem, registry = load_schemas()
    corpus = yaml.safe_load((CONF_DIR / "corpus.yaml").read_text(encoding="utf-8"))
    invariants_doc = yaml.safe_load((CONF_DIR / "invariants.yaml").read_text(encoding="utf-8"))
    keyring = load_keyring(keyring_path)

    failures: list[str] = []
    checks = 0

    def load(rel: str) -> dict:
        return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))

    # 1. Positive corpus must validate.
    for entry in corpus["positive"]:
        checks += 1
        errs = schema_errors(load(entry["payload"]), schemas_by_stem[entry["schema"]], registry)
        if errs:
            failures.append(f"POSITIVE {entry['payload']} should validate but did not: {errs}")

    # 2. Negative corpus must be rejected.
    for entry in corpus["negative"]:
        checks += 1
        payload = load(entry["payload"])
        schema = schemas_by_stem[entry["schema"]]
        if entry["by"] == "schema":
            if not schema_errors(payload, schema, registry):
                failures.append(
                    f"NEGATIVE {entry['payload']} should fail schema ({entry['violates']}) but validated"
                )
        elif entry["by"] == "invariant":
            # Must be schema-valid first, then rejected by the named invariant.
            if schema_errors(payload, schema, registry):
                failures.append(f"NEGATIVE {entry['payload']} expected schema-valid but failed schema")
                continue
            check = BUNDLE_INVARIANTS.get(_assertion_for(invariants_doc, entry["violates"]))
            if check is None or not check(payload):
                failures.append(
                    f"NEGATIVE {entry['payload']} should violate {entry['violates']} but passed"
                )
        else:  # pragma: no cover - guarded by corpus authoring
            failures.append(f"NEGATIVE {entry['payload']} has unknown `by`: {entry['by']!r}")

    # 3. Invariant assertions over positive targets / schemas.
    positive_by_schema: dict[str, list[dict]] = {}
    for entry in corpus["positive"]:
        positive_by_schema.setdefault(entry["schema"], []).append(load(entry["payload"]))

    for inv in invariants_doc["invariants"]:
        applies_to = inv["applies_to"]
        assertion = inv["assertion"]
        if applies_to == ["core_schemas"]:
            checks += 1
            v = core_required_surface_stable(inv["baseline"], schemas_by_stem)
            if v:
                failures.append(f"INVARIANT {inv['id']} failed: {v}")
        elif applies_to == ["capability_token"]:
            for token in positive_by_schema.get("capability_token", []):
                checks += 1
                v = capability_token_scoped(token)
                if v:
                    failures.append(f"INVARIANT {inv['id']} failed on a capability_token: {v}")
        elif applies_to == ["trace_bundle"]:
            check = BUNDLE_INVARIANTS[assertion]
            for bundle in positive_by_schema.get("trace_bundle", []):
                checks += 1
                v = check(bundle)
                if v:
                    failures.append(f"INVARIANT {inv['id']} failed on {bundle.get('bundle_id')!r}: {v}")

    # 4. TraceBundle integrity + signature (#74) over every positive bundle.
    for bundle in positive_by_schema.get("trace_bundle", []):
        checks += 1
        errs, notes = check_trace_bundle(bundle, schemas_by_stem, registry, keyring)
        for note in notes:
            print(f"  bundle {bundle.get('bundle_id')!r}: {note}")
        if errs:
            failures.append(f"TRACEBUNDLE {bundle.get('bundle_id')!r}: {errs}")

    # Report.
    print(f"\nConformance: ran {checks} checks.")
    if failures:
        print(f"FAILED ({len(failures)}):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("All conformance checks passed.")
    return 0


def _assertion_for(invariants_doc: dict, invariant_id: str) -> str:
    for inv in invariants_doc["invariants"]:
        if inv["id"] == invariant_id:
            return str(inv["assertion"])
    raise KeyError(f"no invariant block for {invariant_id!r}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Weaver conformance suite.")
    parser.add_argument(
        "--keyring",
        type=Path,
        default=DEFAULT_KEYRING,
        help="JSON keyring (kid -> public key) for signature verification.",
    )
    args = parser.parse_args(argv)
    return run(args.keyring)


if __name__ == "__main__":
    raise SystemExit(main())
