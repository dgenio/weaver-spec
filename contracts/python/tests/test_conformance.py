"""Tests for the conformance runner (conformance/run.py, issues #43 + #74).

The runner lives outside the ``weaver_contracts`` package (it is build-time CI
tooling, not shipped code), so it is loaded by path rather than imported.
"""

import importlib.util
import json
import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
RUN_PY = REPO_ROOT / "conformance" / "run.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("conformance_run", RUN_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


conf = _load_runner()
CORPUS = yaml.safe_load((REPO_ROOT / "conformance" / "corpus.yaml").read_text())
SCHEMAS, REGISTRY = conf.load_schemas()


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------

def test_full_suite_passes():
    assert conf.run(conf.DEFAULT_KEYRING) == 0


# ---------------------------------------------------------------------------
# Positive / negative corpus
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entry", CORPUS["positive"], ids=lambda e: e["payload"])
def test_positive_validates(entry):
    errs = conf.schema_errors(_load(entry["payload"]), SCHEMAS[entry["schema"]], REGISTRY)
    assert errs == [], f"{entry['payload']} should validate: {errs}"


@pytest.mark.parametrize("entry", CORPUS["negative"], ids=lambda e: e["payload"])
def test_negative_is_rejected(entry):
    payload = _load(entry["payload"])
    schema = SCHEMAS[entry["schema"]]
    if entry["by"] == "schema":
        assert conf.schema_errors(payload, schema, REGISTRY), \
            f"{entry['payload']} should fail schema ({entry['violates']})"
    else:
        # Invariant negatives must be schema-valid first, then caught by the invariant.
        assert conf.schema_errors(payload, schema, REGISTRY) == []
        check = conf.BUNDLE_INVARIANTS[
            conf._assertion_for(
                yaml.safe_load((REPO_ROOT / "conformance" / "invariants.yaml").read_text()),
                entry["violates"],
            )
        ]
        assert check(payload), f"{entry['payload']} should violate {entry['violates']}"


@pytest.mark.parametrize(
    "entry",
    [e for e in CORPUS["negative"] if e["by"] == "schema"],
    ids=lambda e: e["payload"],
)
def test_negative_schema_fails_by_declared_reason(entry):
    # The fixture must fail for the *reason* named in `violates`, not just fail
    # somehow — this guards against fixtures rotting into the wrong failure.
    details = conf.schema_error_details(_load(entry["payload"]), SCHEMAS[entry["schema"]], REGISTRY)
    assert conf.negative_schema_reason_met(entry["violates"], details), (
        f"{entry['payload']} expected to fail by {entry['violates']!r}, "
        f"observed {sorted({kw for kw, _, _ in details})}"
    )


def test_negative_reason_mismatch_is_detected():
    # A fixture that fails by a different keyword than declared must NOT be
    # accepted as matching.
    details = conf.schema_error_details(
        _load("conformance/negative/frame/missing_summary.json"), SCHEMAS["frame"], REGISTRY
    )
    assert conf.negative_schema_reason_met("required:summary", details)
    assert not conf.negative_schema_reason_met("minLength:frame_id", details)


# ---------------------------------------------------------------------------
# Invariant checks (unit level)
# ---------------------------------------------------------------------------

def test_i01_flags_raw_output_and_passes_clean_bundle():
    dirty = _load("conformance/negative/trace_bundle/i01_frame_carries_raw_output.json")
    clean = _load("examples/sample_payloads/trace_bundle.json")
    assert conf.frames_have_no_raw_output(dirty)
    assert conf.frames_have_no_raw_output(clean) == []


def test_i02_flags_unlinked_policy_decision_and_passes_clean_bundle():
    dirty = _load("conformance/negative/trace_bundle/i02_policy_decision_without_trace_event.json")
    clean = _load("examples/sample_payloads/trace_bundle.json")
    assert conf.policy_decisions_are_traced(dirty)
    assert conf.policy_decisions_are_traced(clean) == []


def test_i04_baseline_matches_and_detects_drift():
    inv = yaml.safe_load((REPO_ROOT / "conformance" / "invariants.yaml").read_text())
    baseline = next(i["baseline"] for i in inv["invariants"] if i["id"] == "I-04")
    assert conf.core_required_surface_stable(baseline, SCHEMAS) == []
    drifted = {**baseline, "frame": baseline["frame"] + ["surprise_field"]}
    assert conf.core_required_surface_stable(drifted, SCHEMAS)


def test_i04_reordering_required_is_a_no_op():
    # `required` is an unordered set; a reordered baseline must still pass.
    inv = yaml.safe_load((REPO_ROOT / "conformance" / "invariants.yaml").read_text())
    baseline = next(i["baseline"] for i in inv["invariants"] if i["id"] == "I-04")
    reordered = {stem: list(reversed(fields)) for stem, fields in baseline.items()}
    assert conf.core_required_surface_stable(reordered, SCHEMAS) == []


def test_i06_flags_empty_scope_and_missing_expiry():
    assert conf.capability_token_scoped(_load("examples/sample_payloads/capability_token.json")) == []
    assert conf.capability_token_scoped(
        {"token_id": "t", "principal": "p", "scope": [], "single_use": True})
    assert conf.capability_token_scoped(
        {"token_id": "t", "principal": "p", "scope": ["c"], "issued_at": "2026-01-01T00:00:00Z"})


# ---------------------------------------------------------------------------
# TraceBundle signature verification (#74)
# ---------------------------------------------------------------------------

def test_signed_fixture_cryptographically_verifies():
    bundle = _load("conformance/fixtures/trace_bundle_signed_valid.json")
    keyring = conf.load_keyring(conf.DEFAULT_KEYRING)
    errs, notes = conf.check_trace_bundle(bundle, SCHEMAS, REGISTRY, keyring)
    assert errs == []
    assert any("cryptographically verified" in n for n in notes)


def test_tampered_bundle_fails_verification():
    bundle = _load("conformance/fixtures/trace_bundle_signed_valid.json")
    bundle["bundle_id"] = "tampered-after-signing"  # changes the canonical form
    keyring = conf.load_keyring(conf.DEFAULT_KEYRING)
    errs, _ = conf.check_trace_bundle(bundle, SCHEMAS, REGISTRY, keyring)
    assert any("verification FAILED" in e for e in errs)


def test_keyring_alg_mismatch_is_rejected():
    bundle = _load("conformance/fixtures/trace_bundle_signed_valid.json")
    kid = bundle["signature"]["kid"]
    mismatched = {kid: {"kid": kid, "alg": "es256", "public_key_b64url": "AAAA"}}
    errs, _ = conf.check_trace_bundle(bundle, SCHEMAS, REGISTRY, mismatched)
    assert any("alg" in e and kid in e for e in errs)


def test_unsigned_bundle_recomputes_canonical_form_without_error():
    bundle = _load("examples/sample_payloads/trace_bundle.json")
    errs, notes = conf.check_trace_bundle(bundle, SCHEMAS, REGISTRY, {})
    assert errs == []
    assert any("unsigned bundle" in n for n in notes)


def test_signature_with_unknown_kid_is_skipped_not_failed():
    # The illustrative sample sig uses a kid absent from the test keyring.
    bundle = _load("examples/sample_payloads/trace_bundle_signed.json")
    keyring = conf.load_keyring(conf.DEFAULT_KEYRING)
    errs, notes = conf.check_trace_bundle(bundle, SCHEMAS, REGISTRY, keyring)
    assert errs == []
    assert any("skipped" in n for n in notes)
