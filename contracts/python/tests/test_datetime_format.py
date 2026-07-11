"""date-time format enforcement tests (issue #155).

jsonschema only *validates* the ``date-time`` format when ``rfc3339-validator``
is installed; otherwise the format keyword is silently ignored. These tests fail
loudly if that companion is missing from the dev extras — which is the point:
the RFC 3339 convention documented in CONTRACT_REFERENCE.md must be enforced,
not decorative. They also confirm a real Core schema rejects a malformed
timestamp.
"""

import json
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")

from jsonschema import Draft202012Validator  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]

_DATETIME_SCHEMA = {"type": "string", "format": "date-time"}


def _validator(schema):
    return Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )


def test_date_time_format_is_actually_enforced():
    # If rfc3339-validator were missing, this malformed value would pass.
    v = _validator(_DATETIME_SCHEMA)
    assert list(v.iter_errors("not-a-timestamp")), (
        "date-time format is not being enforced — is rfc3339-validator installed?"
    )


@pytest.mark.parametrize(
    "value",
    ["2026-07-10T12:00:00Z", "2026-07-10T12:00:00+00:00", "2026-07-10T12:00:00.5Z"],
)
def test_valid_rfc3339_timestamps_pass(value):
    assert not list(_validator(_DATETIME_SCHEMA).iter_errors(value))


@pytest.mark.parametrize(
    "value",
    ["2026-07-10", "10/07/2026", "2026-13-01T00:00:00Z", "yesterday", ""],
)
def test_malformed_timestamps_fail(value):
    assert list(_validator(_DATETIME_SCHEMA).iter_errors(value))


def test_core_schema_rejects_bad_created_at():
    # Frame.created_at is a required date-time field.
    schema = json.loads((REPO_ROOT / "contracts/json/frame.schema.json").read_text())
    payload = {
        "frame_id": "f1",
        "capability_id": "c1",
        "summary": "ok",
        "created_at": "not-a-date",
    }
    errors = list(_validator(schema).iter_errors(payload))
    assert any("created_at" in "/".join(str(p) for p in e.absolute_path) or
               "date-time" in e.message for e in errors)
