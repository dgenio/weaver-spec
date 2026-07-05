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
    checks, failures, records = conf.run(conf.DEFAULT_KEYRING)
    assert failures == []
    assert records == []
    assert checks > 0


def test_main_corpus_exit_zero():
    assert conf.main([]) == 0


# ---------------------------------------------------------------------------
# External-bundle mode + machine-readable result + badge (#51 / #77)
# ---------------------------------------------------------------------------

def test_verify_external_bundle_passes_signed_fixture():
    bundle = _load("conformance/fixtures/trace_bundle_signed_valid.json")
    keyring = conf.load_keyring(conf.DEFAULT_KEYRING)
    checks, failures, records, _notes = conf.verify_external_bundle(bundle, SCHEMAS, REGISTRY, keyring)
    assert checks > 0
    assert failures == []
    assert records == []


def test_verify_external_bundle_flags_i01_violation():
    bundle = _load("conformance/negative/trace_bundle/i01_frame_carries_raw_output.json")
    checks, failures, records, _notes = conf.verify_external_bundle(bundle, SCHEMAS, REGISTRY, {})
    assert any("frames_have_no_raw_output" in f for f in failures)
    # #145: the same failure is available as a structured record an agent can map.
    assert any(
        r["kind"] == "invariant" and r.get("invariant_id") == "frames_have_no_raw_output"
        for r in records
    )


def test_verify_external_bundle_rejects_schema_invalid_bundle():
    # Missing the required trace_events array: rejected at the schema gate.
    bundle = {"bundle_id": "b", "routing_decision": {}, "policy_decisions": [],
              "frames": [], "handles": []}
    _checks, failures, records, _notes = conf.verify_external_bundle(bundle, SCHEMAS, REGISTRY, {})
    assert any(f.startswith("schema:") for f in failures)
    assert any(r["kind"] == "schema" for r in records)


def test_build_result_and_shields_endpoint_pass():
    result = conf.build_result("pass", 40, [])
    assert result["status"] == "pass"
    assert result["failures"] == 0
    endpoint = conf.build_shields_endpoint(result)
    assert endpoint["color"] == "brightgreen"
    assert endpoint["message"].startswith("v")
    assert endpoint["isError"] is False


def test_build_shields_endpoint_fail():
    endpoint = conf.build_shields_endpoint(conf.build_result("fail", 40, ["boom"]))
    assert endpoint["color"] == "red"
    assert endpoint["message"] == "failing"
    assert endpoint["isError"] is True


# ---------------------------------------------------------------------------
# Result freshness / expiry policy (#150)
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone  # noqa: E402


def test_result_freshness_accepts_recent_current_major():
    # Just-produced result: generated_at ~= real now and version == current, so
    # it is fresh. Uses the default `now` (real clock) rather than a pinned one
    # so the freshly-stamped generated_at is never treated as future.
    result = conf.build_result("pass", 47, [])
    fresh, reasons = conf.is_result_fresh(result)
    assert fresh, reasons


def test_result_freshness_flags_stale():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    result = conf.build_result("pass", 47, [])
    result["generated_at"] = "2026-01-01T00:00:00Z"  # > 90 days before `now`
    fresh, reasons = conf.is_result_fresh(result, now=now)
    assert not fresh
    assert any("days old" in r for r in reasons)


def test_result_freshness_flags_wrong_major():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    result = conf.build_result("pass", 47, [])
    result["contract_version"] = "1.0.0"  # different MAJOR than current 0.x
    fresh, reasons = conf.is_result_fresh(result, now=now)
    assert not fresh
    assert any("MAJOR" in r for r in reasons)


def test_result_freshness_flags_missing_generated_at():
    result = conf.build_result("pass", 47, [])
    del result["generated_at"]
    fresh, reasons = conf.is_result_fresh(result)
    assert not fresh
    assert any("generated_at" in r for r in reasons)


def test_result_freshness_flags_future_timestamp():
    # A future-dated result is clock-skewed/malformed, not fresh: a negative age
    # must not slip past the age ceiling.
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    result = conf.build_result("pass", 47, [])
    result["generated_at"] = "2026-08-01T00:00:00Z"  # after `now`
    fresh, reasons = conf.is_result_fresh(result, now=now)
    assert not fresh
    assert any("future" in r for r in reasons)


def test_main_emits_result_and_badge(tmp_path):
    result_path = tmp_path / "result.json"
    badge_path = tmp_path / "badge.json"
    code = conf.main(["--emit-result", str(result_path), "--emit-badge", str(badge_path)])
    assert code == 0
    result = json.loads(result_path.read_text())
    assert result["status"] == "pass"
    assert result["mode"] == "corpus"
    assert result["failure_records"] == []
    badge = json.loads(badge_path.read_text())
    assert badge["label"] == "weaver-compatible"
    assert badge["color"] == "brightgreen"


def test_emitted_result_validates_against_schema():
    # #116: the runner's own output must satisfy the ConformanceResult schema, so
    # the badge/scoreboard consumers have a validated contract.
    schema = SCHEMAS["conformance_result"]
    passing = conf.build_result("pass", 47, [], mode="corpus", target=None)
    assert conf.schema_errors(passing, schema, REGISTRY) == []


def test_emitted_result_with_structured_failures_validates():
    # #116 + #145: a failing result carrying structured failure_records also
    # validates against the schema.
    schema = SCHEMAS["conformance_result"]
    records = [
        {"kind": "schema", "message": "schema: <root>: boom", "schema": "frame", "path": "<root>"},
        {"kind": "invariant", "message": "INVARIANT I-01 failed", "invariant_id": "I-01"},
    ]
    failing = conf.build_result(
        "fail", 47, ["schema: <root>: boom", "INVARIANT I-01 failed"],
        mode="bundle", target="path/to/bundle.json", failure_records=records,
    )
    assert conf.schema_errors(failing, schema, REGISTRY) == []
    assert failing["failure_records"] == records


# ---------------------------------------------------------------------------
# External-bundle input hardening (#158)
# ---------------------------------------------------------------------------

def test_load_external_bundle_accepts_valid_object(tmp_path):
    path = tmp_path / "b.json"
    path.write_text(json.dumps({"bundle_id": "b"}))
    bundle, error = conf.load_external_bundle(path)
    assert error is None
    assert bundle == {"bundle_id": "b"}


def test_load_external_bundle_rejects_oversized(tmp_path):
    path = tmp_path / "big.json"
    # A valid-JSON string padded past the limit: rejected on size, before parsing.
    path.write_text('{"x": "' + "a" * (conf.MAX_BUNDLE_BYTES + 10) + '"}')
    bundle, error = conf.load_external_bundle(path)
    assert bundle is None
    assert error is not None and "limit" in error


def test_load_external_bundle_rejects_non_object(tmp_path):
    path = tmp_path / "arr.json"
    path.write_text("[1, 2, 3]")  # valid JSON, but not a bundle object
    bundle, error = conf.load_external_bundle(path)
    assert bundle is None
    assert error is not None and "JSON object" in error


def test_load_external_bundle_rejects_malformed_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    bundle, error = conf.load_external_bundle(path)
    assert bundle is None
    assert error is not None and "not valid JSON" in error


def test_main_bundle_mode_fails_gracefully_on_malformed_input(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("[1, 2, 3]")
    # Exit non-zero with a clear failure, not a traceback.
    assert conf.main(["--bundle", str(path)]) == 1


def test_main_bundle_mode_oversized_input_is_reported(tmp_path, capsys):
    path = tmp_path / "big.json"
    path.write_text('{"x": "' + "a" * (conf.MAX_BUNDLE_BYTES + 10) + '"}')
    assert conf.main(["--bundle", str(path)]) == 1
    err = capsys.readouterr().err
    assert "input:" in err and "limit" in err


def test_input_failure_message_is_1to1_in_result(tmp_path):
    # The structured record's message must equal the failure_detail entry (the
    # _Failures 1:1 invariant), including the "input:" prefix.
    path = tmp_path / "bad.json"
    path.write_text("[1, 2, 3]")  # valid JSON, not an object
    result_path = tmp_path / "result.json"
    assert conf.main(["--bundle", str(path), "--emit-result", str(result_path)]) == 1
    result = json.loads(result_path.read_text())
    assert result["failure_detail"] == [r["message"] for r in result["failure_records"]]
    assert result["failure_detail"][0].startswith("input:")


# ---------------------------------------------------------------------------
# Validator caching / performance regression guard (#130)
# ---------------------------------------------------------------------------

def test_validator_is_compiled_once_and_reused():
    # Same schema -> the very same compiled validator object, not a rebuild.
    v1 = conf._validator_for(SCHEMAS["frame"], REGISTRY)
    v2 = conf._validator_for(SCHEMAS["frame"], REGISTRY)
    assert v1 is v2


def test_full_run_compiles_far_fewer_validators_than_checks():
    # Regression guard: with caching, the number of distinct compiled validators
    # scales with the number of *schemas*, not the number of checks. If a future
    # change reintroduces per-payload construction this bound breaks loudly
    # (this is a structural guard, not a flaky wall-clock benchmark).
    conf._VALIDATOR_CACHE.clear()
    checks, failures, _records = conf.run(conf.DEFAULT_KEYRING)
    assert failures == []
    assert 0 < len(conf._VALIDATOR_CACHE) < checks


# ---------------------------------------------------------------------------
# Extend-via-data guard: corpus/invariants map to real schemas/checks (#137)
# ---------------------------------------------------------------------------

INVARIANTS_DOC = yaml.safe_load((REPO_ROOT / "conformance" / "invariants.yaml").read_text())
_KNOWN_APPLIES_TO = (["core_schemas"], ["capability_token"], ["trace_bundle"])


@pytest.mark.parametrize(
    "entry",
    CORPUS["positive"] + CORPUS["negative"],
    ids=lambda e: e["payload"],
)
def test_corpus_schema_names_resolve(entry):
    # Every corpus entry must name a schema the runner actually loaded — a typo
    # or a schema rename would otherwise KeyError deep in a run (or, worse for a
    # sibling manifest, skip silently).
    assert entry["schema"] in SCHEMAS, f"unknown schema {entry['schema']!r}"


def test_trace_bundle_invariant_assertions_are_registered():
    # Every trace_bundle-scoped invariant must bind to a real named check in
    # BUNDLE_INVARIANTS, so invariants.yaml can't reference a check that no
    # longer exists.
    for inv in INVARIANTS_DOC["invariants"]:
        if inv["applies_to"] == ["trace_bundle"]:
            assert inv["assertion"] in conf.BUNDLE_INVARIANTS, (
                f"invariant {inv['id']} names unregistered check {inv['assertion']!r}"
            )


def test_every_invariant_applies_to_a_known_branch():
    # Guards the run() dispatch: an applies_to with no branch now raises rather
    # than silently skipping (#137). This asserts the shipped manifest stays
    # within the supported set.
    for inv in INVARIANTS_DOC["invariants"]:
        assert inv["applies_to"] in _KNOWN_APPLIES_TO, (
            f"invariant {inv['id']} has unsupported applies_to {inv['applies_to']!r}"
        )


def test_run_raises_on_unsupported_applies_to(monkeypatch, tmp_path):
    # Directly exercise the fail-loud path: an invariant targeting an unknown
    # scope must raise, not no-op. Keep the real invariants (the negative corpus
    # resolves I-01/I-02 by id) and append one bogus entry.
    doc = yaml.safe_load((REPO_ROOT / "conformance" / "invariants.yaml").read_text())
    doc["invariants"].append(
        {"id": "I-XX", "applies_to": ["nonexistent"], "assertion": "whatever"}
    )
    (tmp_path / "invariants.yaml").write_text(yaml.safe_dump(doc))
    # Copy the real corpus alongside so run() gets past the corpus stage.
    (tmp_path / "corpus.yaml").write_text(
        (REPO_ROOT / "conformance" / "corpus.yaml").read_text()
    )
    monkeypatch.setattr(conf, "CONF_DIR", tmp_path)
    with pytest.raises(ValueError, match="unsupported applies_to"):
        conf.run(conf.DEFAULT_KEYRING)


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


def test_tampered_nested_frame_fails_verification():
    # #133: tampering a nested artifact (not just a top-level scalar) after
    # signing must still break the signature, since the whole bundle is in the
    # JCS canonical form. Guards the integrity check against nested mutation.
    bundle = _load("conformance/fixtures/trace_bundle_signed_valid.json")
    bundle["frames"][0]["summary"] = "Rewritten after the bundle was signed."
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
