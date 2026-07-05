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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

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

# Cap on an external bundle accepted by --bundle / the scoreboard. The external
# path ingests semi-trusted input (a sibling's published bundle, fetched on a
# schedule), so an oversized or malformed file must fail with a clear message
# rather than exhaust memory or surface a raw traceback (#158). scoreboard.py
# reuses this so the file path and the network fetch path share one limit.
MAX_BUNDLE_BYTES = 5 * 1024 * 1024  # 5 MiB


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


# Compiled validators are cached so a corpus run (or an adopter validating many
# payloads) compiles each schema once and reuses it, rather than recompiling per
# payload. See docs/CONFORMANCE.md "Validating at scale".
_VALIDATOR_CACHE: dict[str, "Draft202012Validator"] = {}


def _validator_for(schema: dict, registry: Registry) -> Draft202012Validator:
    """Return a compiled validator for ``schema``, compiling once and reusing.

    Keyed by the schema's ``$id`` — stable and immutable per docs/SCHEMA_HOSTING.md,
    so the same ``$id`` always maps to the same schema content and thus a
    behaviour-identical validator (unlike ``id(schema)``, which a fresh
    ``load_schemas()`` would change and which an object could later reuse). A
    schema without an ``$id`` is compiled fresh each call rather than cached. All
    validators in this repo resolve ``$ref`` against the single registry built by
    :func:`load_schemas`, so the registry is not part of the cache key.
    """
    schema_id = schema.get("$id")
    if schema_id is not None and schema_id in _VALIDATOR_CACHE:
        return _VALIDATOR_CACHE[schema_id]
    validator = Draft202012Validator(
        schema, registry=registry, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    if schema_id is not None:
        _VALIDATOR_CACHE[schema_id] = validator
    return validator


def schema_errors(payload: dict, schema: dict, registry: Registry) -> list[str]:
    """Return a sorted list of validation error messages (empty == valid)."""
    validator = _validator_for(schema, registry)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    out = []
    for err in errors:
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out


def schema_error_details(
    payload: dict, schema: dict, registry: Registry
) -> list[tuple[str, str, str]]:
    """Return (keyword, location, message) per validation error (empty == valid).

    Unlike :func:`schema_errors`, this preserves the failing JSON Schema keyword
    (``required``, ``minLength``, ``enum``, …) so a negative fixture can be
    checked against the *reason* it is supposed to fail, not merely that it
    fails somehow.
    """
    validator = _validator_for(schema, registry)
    details = []
    for err in validator.iter_errors(payload):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        details.append((str(err.validator), loc, err.message))
    return details


def negative_schema_reason_met(violates: str, details: list[tuple[str, str, str]]) -> bool:
    """True if some validation error matches the declared ``violates`` reason.

    ``violates`` is ``"<keyword>:<target>"`` (e.g. ``"required:summary"``,
    ``"minLength:frame_id"``). The keyword must match a failing keyword; the
    target must appear in that error's location or message — except for keywords
    like ``anyOf`` whose target is a human label rather than a field path.
    """
    keyword, _, target = violates.partition(":")
    label_only = {"anyOf", "oneOf", "allOf", "not"}
    for kw, loc, msg in details:
        if kw != keyword:
            continue
        if not target or keyword in label_only:
            return True
        if target in loc or target in msg:
            return True
    return False


class _Failures:
    """Collects failures as both human strings and structured records (#145).

    ``messages`` preserves the exact stderr/human output the runner has always
    produced (so existing consumers and tests are unaffected); ``records`` is the
    additive machine-readable view an agent can map to the offending
    fixture/field — ``kind`` plus, where known, ``payload`` / ``schema`` /
    ``keyword`` / ``path`` / ``invariant_id``. The two stay 1:1 and carry the
    same ``message``.
    """

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.records: list[dict] = []

    def add(self, kind: str, message: str, **fields: Optional[str]) -> None:
        self.messages.append(message)
        record = {"kind": kind, "message": message}
        record.update({k: v for k, v in fields.items() if v is not None})
        self.records.append(record)


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
        # `required` is an unordered set in JSON Schema, so compare as sets:
        # reordering fields in a schema file is a semantic no-op.
        actual = sorted(schema.get("required", []))
        if actual != sorted(expected):
            violations.append(
                f"{stem}: required surface drifted — expected {sorted(expected)}, found {actual}"
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
    sig_schema = schemas_by_stem.get("capability_token_signature")
    if sig_schema is None:
        errors.append(
            "Extended schema 'capability_token_signature' not found; "
            "cannot validate the signature envelope"
        )
        return errors, notes
    sig_errs = schema_errors(signature, sig_schema, registry)
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
    if key_entry.get("alg") != signature["alg"]:
        errors.append(
            f"keyring entry for kid {kid!r} is alg {key_entry.get('alg')!r}, "
            f"but the signature declares alg {signature['alg']!r}"
        )
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

def run(keyring_path: Optional[Path]) -> tuple[int, list[str], list[dict]]:
    """Run the full corpus + invariants + bundle checks.

    Returns ``(checks_run, failures, failure_records)``. ``failures`` is the
    human-readable list (unchanged); ``failure_records`` is the structured view
    (#145). Reporting and exit-code handling are the caller's responsibility
    (see :func:`main`), so the result can also be serialized via
    ``--emit-result`` / ``--emit-badge``.
    """
    schemas_by_stem, registry = load_schemas()
    corpus = yaml.safe_load((CONF_DIR / "corpus.yaml").read_text(encoding="utf-8"))
    invariants_doc = yaml.safe_load((CONF_DIR / "invariants.yaml").read_text(encoding="utf-8"))
    keyring = load_keyring(keyring_path)

    fail = _Failures()
    checks = 0

    def load(rel: str) -> dict:
        return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))

    # 1. Positive corpus must validate.
    for entry in corpus["positive"]:
        checks += 1
        errs = schema_errors(load(entry["payload"]), schemas_by_stem[entry["schema"]], registry)
        if errs:
            fail.add(
                "positive",
                f"POSITIVE {entry['payload']} should validate but did not: {errs}",
                payload=entry["payload"], schema=entry["schema"],
            )

    # 2. Negative corpus must be rejected.
    for entry in corpus["negative"]:
        checks += 1
        payload = load(entry["payload"])
        schema = schemas_by_stem[entry["schema"]]
        if entry["by"] == "schema":
            details = schema_error_details(payload, schema, registry)
            if not details:
                fail.add(
                    "negative",
                    f"NEGATIVE {entry['payload']} should fail schema ({entry['violates']}) but validated",
                    payload=entry["payload"], schema=entry["schema"], keyword=entry["violates"],
                )
            elif not negative_schema_reason_met(entry["violates"], details):
                observed = sorted({kw for kw, _, _ in details})
                fail.add(
                    "negative",
                    f"NEGATIVE {entry['payload']} should fail by {entry['violates']!r} "
                    f"but failed by {observed} instead",
                    payload=entry["payload"], schema=entry["schema"], keyword=entry["violates"],
                )
        elif entry["by"] == "invariant":
            # Must be schema-valid first, then rejected by the named invariant.
            if schema_errors(payload, schema, registry):
                fail.add(
                    "negative",
                    f"NEGATIVE {entry['payload']} expected schema-valid but failed schema",
                    payload=entry["payload"], schema=entry["schema"],
                )
                continue
            check = BUNDLE_INVARIANTS.get(_assertion_for(invariants_doc, entry["violates"]))
            if check is None or not check(payload):
                fail.add(
                    "negative",
                    f"NEGATIVE {entry['payload']} should violate {entry['violates']} but passed",
                    payload=entry["payload"], invariant_id=entry["violates"],
                )
        else:  # pragma: no cover - guarded by corpus authoring
            fail.add(
                "negative",
                f"NEGATIVE {entry['payload']} has unknown `by`: {entry['by']!r}",
                payload=entry["payload"],
            )

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
                fail.add("invariant", f"INVARIANT {inv['id']} failed: {v}", invariant_id=inv["id"])
        elif applies_to == ["capability_token"]:
            for token in positive_by_schema.get("capability_token", []):
                checks += 1
                v = capability_token_scoped(token)
                if v:
                    fail.add(
                        "invariant",
                        f"INVARIANT {inv['id']} failed on a capability_token: {v}",
                        schema="capability_token", invariant_id=inv["id"],
                    )
        elif applies_to == ["trace_bundle"]:
            check = BUNDLE_INVARIANTS[assertion]
            for bundle in positive_by_schema.get("trace_bundle", []):
                checks += 1
                v = check(bundle)
                if v:
                    fail.add(
                        "invariant",
                        f"INVARIANT {inv['id']} failed on {bundle.get('bundle_id')!r}: {v}",
                        payload=bundle.get("bundle_id"), invariant_id=inv["id"],
                    )
        else:
            # Extend via data, not silent no-ops (#137): an invariant whose
            # applies_to matches no branch here would otherwise be skipped
            # without a trace, quietly weakening the suite. Fail loudly so a new
            # target must register a real code path.
            raise ValueError(
                f"invariant {inv['id']!r} has unsupported applies_to {applies_to!r}; "
                "register a handling branch in run.py before adding it to invariants.yaml"
            )

    # 4. TraceBundle integrity + signature (#74) over every positive bundle.
    for bundle in positive_by_schema.get("trace_bundle", []):
        checks += 1
        errs, notes = check_trace_bundle(bundle, schemas_by_stem, registry, keyring)
        for note in notes:
            print(f"  bundle {bundle.get('bundle_id')!r}: {note}")
        if errs:
            fail.add(
                "tracebundle",
                f"TRACEBUNDLE {bundle.get('bundle_id')!r}: {errs}",
                payload=bundle.get("bundle_id"),
            )

    return checks, fail.messages, fail.records


# ---------------------------------------------------------------------------
# External-bundle mode (#51 scoreboard reuses this)
# ---------------------------------------------------------------------------

def load_external_bundle(path: Path) -> tuple[Optional[dict], Optional[str]]:
    """Read and parse an external bundle file defensively (#158).

    Returns ``(bundle, None)`` on success, or ``(None, reason)`` when the file is
    oversized, unreadable, not JSON, or not a JSON object. Because the
    external-bundle path ingests semi-trusted input, every failure mode is a
    clear message rather than a raw traceback. At most :data:`MAX_BUNDLE_BYTES`
    (+1 sentinel) is read before parsing, so a giant file cannot exhaust memory —
    the same idiom the scoreboard uses for network fetches.
    """
    try:
        with path.open("rb") as fh:
            raw = fh.read(MAX_BUNDLE_BYTES + 1)
    except OSError as exc:
        return None, f"cannot read bundle file: {exc}"
    if len(raw) > MAX_BUNDLE_BYTES:
        return None, f"bundle file exceeds the {MAX_BUNDLE_BYTES}-byte limit"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"bundle is not valid JSON: {exc}"
    if not isinstance(parsed, dict):
        return None, f"bundle must be a JSON object, got {type(parsed).__name__}"
    return parsed, None


def verify_external_bundle(
    bundle: dict,
    schemas_by_stem: dict[str, dict],
    registry: Registry,
    keyring: dict[str, dict],
) -> tuple[int, list[str], list[dict], list[str]]:
    """Conformance-check a single externally supplied TraceBundle.

    Validates it against the ``trace_bundle`` schema, runs the TraceBundle
    integrity + signature checks (#74), and asserts I-01/I-02. Returns
    ``(checks_run, failures, failure_records, notes)`` — ``failures`` is the
    human-readable list (unchanged) and ``failure_records`` the structured view
    (#145). This is what the scoreboard (#51) runs against each sibling's
    published bundle.
    """
    checks = 0
    fail = _Failures()
    notes: list[str] = []

    schema = schemas_by_stem.get("trace_bundle")
    if schema is None:  # pragma: no cover - extended schema is always present
        fail.add("schema", "Extended schema 'trace_bundle' not found", schema="trace_bundle")
        return 0, fail.messages, fail.records, notes

    checks += 1
    errs = schema_errors(bundle, schema, registry)
    if errs:
        for e in errs:
            fail.add("schema", f"schema: {e}", schema="trace_bundle", path=e.split(":", 1)[0])
        # A schema-invalid bundle can't be meaningfully invariant-checked.
        return checks, fail.messages, fail.records, notes

    checks += 1
    integrity_errs, integrity_notes = check_trace_bundle(bundle, schemas_by_stem, registry, keyring)
    for e in integrity_errs:
        fail.add("tracebundle", e, payload=bundle.get("bundle_id"))
    notes.extend(integrity_notes)

    for name, check in BUNDLE_INVARIANTS.items():
        checks += 1
        for v in check(bundle):
            fail.add("invariant", f"{name}: {v}", payload=bundle.get("bundle_id"), invariant_id=name)

    return checks, fail.messages, fail.records, notes


# ---------------------------------------------------------------------------
# Machine-readable result + badge (#77 / #51)
# ---------------------------------------------------------------------------

def _now_z() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def contract_version() -> str:
    """Read CONTRACT_VERSION without importing the package (the conformance
    workflow installs only the runner's deps, not ``weaver_contracts``)."""
    version_py = REPO_ROOT / "contracts" / "python" / "src" / "weaver_contracts" / "version.py"
    try:
        text = version_py.read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = re.search(r'CONTRACT_VERSION\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else "unknown"


# A published conformance result is trustworthy only while it is recent and
# targets the current contract MAJOR. The scoreboard re-verifies each sibling's
# live bundle on every run, so it never relies on a stale result; this policy
# governs a *self-published* result JSON that a third party might display. See
# docs/SELF_CERTIFICATION.md "Freshness and validity" (#150).
RESULT_MAX_AGE_DAYS = 90


def is_result_fresh(
    result: dict,
    *,
    now: Optional[datetime] = None,
    max_age_days: int = RESULT_MAX_AGE_DAYS,
) -> tuple[bool, list[str]]:
    """Return ``(fresh, reasons)`` for a published conformance result (#150).

    A result is fresh only when its ``generated_at`` is within ``max_age_days``
    and its ``contract_version`` shares the current contract MAJOR. ``reasons``
    lists why it is not fresh (empty when fresh). Uses only fields already in the
    result — no new contract surface.
    """
    reasons: list[str] = []
    now = now or datetime.now(timezone.utc)

    current_major = contract_version().split(".")[0]
    stated = str(result.get("contract_version", ""))
    stated_major = stated.split(".")[0] if stated else ""
    if stated_major != current_major:
        reasons.append(
            f"contract_version {stated!r} is not the current MAJOR {current_major!r}"
        )

    raw = result.get("generated_at")
    generated_at = None
    if isinstance(raw, str):
        try:
            generated_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            generated_at = None
    if generated_at is None:
        reasons.append("generated_at is missing or unparseable")
    else:
        if generated_at.tzinfo is None:  # treat a naive timestamp as UTC
            generated_at = generated_at.replace(tzinfo=timezone.utc)
        age_days = (now - generated_at).days
        if age_days > max_age_days:
            reasons.append(f"result is {age_days} days old (limit {max_age_days})")

    return (not reasons, reasons)


def build_result(
    status: str,
    checks: int,
    failures: list[str],
    *,
    mode: str = "corpus",
    target: Optional[str] = None,
    failure_records: Optional[list[dict]] = None,
) -> dict:
    """Build the machine-readable conformance result consumed by the badge (#77)
    and the scoreboard (#51). This is CI tooling output, not a Weaver runtime
    contract, but it is a stable inter-repo interchange shape validated against
    ``contracts/json/extended/conformance_result.schema.json`` (#116).

    ``failure_detail`` stays the flat human-readable list; ``failure_records`` is
    the structured per-failure view (#145) — empty when omitted so existing
    callers need no change."""
    return {
        "result_version": "1",
        "contract_version": contract_version(),
        "mode": mode,
        "target": target,
        "status": status,
        "checks_run": checks,
        "failures": len(failures),
        "failure_detail": failures,
        "failure_records": failure_records or [],
        "generated_at": _now_z(),
        "runner": "weaver-spec conformance/run.py",
    }


def build_shields_endpoint(result: dict) -> dict:
    """Render a shields.io endpoint badge (https://shields.io/endpoint) from a
    conformance result so the badge and the scoreboard can never disagree."""
    passed = result["status"] == "pass"
    return {
        "schemaVersion": 1,
        "label": "weaver-compatible",
        "message": f"v{result['contract_version']}" if passed else "failing",
        "color": "brightgreen" if passed else "red",
        "isError": not passed,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assertion_for(invariants_doc: dict, invariant_id: str) -> str:
    for inv in invariants_doc["invariants"]:
        if inv["id"] == invariant_id:
            return str(inv["assertion"])
    raise KeyError(f"no invariant block for {invariant_id!r}")


def _report(checks: int, failures: list[str], header: str) -> int:
    print(f"\n{header}: ran {checks} checks.")
    if failures:
        print(f"FAILED ({len(failures)}):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("All conformance checks passed.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Weaver conformance suite.")
    parser.add_argument(
        "--keyring",
        type=Path,
        default=DEFAULT_KEYRING,
        help="JSON keyring (kid -> public key) for signature verification.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="Conformance-check a single external TraceBundle JSON file instead "
        "of the built-in corpus (used by the scoreboard, #51).",
    )
    parser.add_argument(
        "--emit-result",
        type=Path,
        default=None,
        help="Write the machine-readable conformance result JSON to this path (#77).",
    )
    parser.add_argument(
        "--emit-badge",
        type=Path,
        default=None,
        help="Write a shields.io endpoint badge JSON to this path (#77).",
    )
    args = parser.parse_args(argv)

    keyring = load_keyring(args.keyring)

    if args.bundle is not None:
        schemas_by_stem, registry = load_schemas()
        bundle, load_error = load_external_bundle(args.bundle)
        if load_error is not None:
            # Oversized / malformed / non-object input: fail cleanly (#158), not
            # with a traceback, and never reach schema validation.
            checks, failures, records, notes = (
                0, [f"input: {load_error}"], [{"kind": "input", "message": load_error}], [],
            )
        else:
            assert bundle is not None  # load_error is None => bundle is set
            checks, failures, records, notes = verify_external_bundle(
                bundle, schemas_by_stem, registry, keyring
            )
        for note in notes:
            print(f"  bundle: {note}")
        exit_code = _report(checks, failures, f"Bundle conformance ({args.bundle})")
        mode, target = "bundle", str(args.bundle)
    else:
        checks, failures, records = run(args.keyring)
        exit_code = _report(checks, failures, "Conformance")
        mode, target = "corpus", None

    if args.emit_result is not None or args.emit_badge is not None:
        result = build_result(
            "pass" if not failures else "fail", checks, failures,
            mode=mode, target=target, failure_records=records,
        )
        if args.emit_result is not None:
            _write_json(args.emit_result, result)
            print(f"Wrote conformance result to {args.emit_result}")
        if args.emit_badge is not None:
            _write_json(args.emit_badge, build_shields_endpoint(result))
            print(f"Wrote badge endpoint to {args.emit_badge}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
