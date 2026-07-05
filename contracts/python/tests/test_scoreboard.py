"""Tests for the conformance scoreboard builder (conformance/scoreboard.py, #51).

Like the runner, the scoreboard lives outside the ``weaver_contracts`` package
(it is build-time CI tooling, not shipped code), so it is loaded by path rather
than imported. Network access is faked — these tests never hit a real URL.
"""

import importlib.util
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOREBOARD_PY = REPO_ROOT / "conformance" / "scoreboard.py"


def _load_scoreboard():
    spec = importlib.util.spec_from_file_location("conformance_scoreboard", SCOREBOARD_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass (Row) can resolve the module via
    # sys.modules[cls.__module__] — module_from_spec does not do this for us.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sb = _load_scoreboard()


class _FakeResp:
    """Minimal stand-in for an http.client.HTTPResponse context manager."""

    def __init__(self, data: bytes, status: int = 200):
        self._data = data
        self.status = status

    def read(self, n: int = -1) -> bytes:
        return self._data if n < 0 else self._data[:n]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeOpener:
    def __init__(self, resp: _FakeResp):
        self._resp = resp

    def open(self, url, timeout=None):  # noqa: A003 - mirrors urllib opener API
        return self._resp


# ---------------------------------------------------------------------------
# fetch_json — scheme enforcement, redirect refusal, byte cap, parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", ["http://example.dev/b.json", "ftp://x/y", "file:///etc/passwd"])
def test_fetch_json_refuses_non_https(url):
    payload, note = sb.fetch_json(url, timeout=1.0)
    assert payload is None
    assert note == "refused: non-https URL"


def test_fetch_json_parses_valid_json(monkeypatch):
    monkeypatch.setattr(sb, "_OPENER", _FakeOpener(_FakeResp(b'{"a": 1}')))
    payload, note = sb.fetch_json("https://x.dev/b.json", timeout=1.0)
    assert payload == {"a": 1}
    assert note == "fetched"


def test_fetch_json_rejects_oversize(monkeypatch):
    monkeypatch.setattr(sb, "MAX_BUNDLE_BYTES", 10)
    monkeypatch.setattr(sb, "_OPENER", _FakeOpener(_FakeResp(b"x" * 20)))
    payload, note = sb.fetch_json("https://x.dev/b.json", timeout=1.0)
    assert payload is None
    assert "exceeds" in note


def test_fetch_json_refuses_redirect_status(monkeypatch):
    monkeypatch.setattr(sb, "_OPENER", _FakeOpener(_FakeResp(b"", status=302)))
    payload, note = sb.fetch_json("https://x.dev/b.json", timeout=1.0)
    assert payload is None
    assert "redirect" in note


def test_fetch_json_non_json_is_reported(monkeypatch):
    monkeypatch.setattr(sb, "_OPENER", _FakeOpener(_FakeResp(b"not json at all")))
    payload, note = sb.fetch_json("https://x.dev/b.json", timeout=1.0)
    assert payload is None
    assert note.startswith("not JSON")


# ---------------------------------------------------------------------------
# _signature_status — condense verify notes into a scoreboard label
# ---------------------------------------------------------------------------

def test_signature_status_verified():
    assert sb._signature_status(["signature cryptographically verified (kid 'k')"]) == "signature verified"


def test_signature_status_unsigned():
    assert sb._signature_status(["unsigned bundle (canonical form recomputed)"]) == "unsigned"


def test_signature_status_skipped():
    note = "signature envelope valid; crypto verify skipped (kid 'k' not in keyring)"
    assert sb._signature_status([note]) == "signature unverified (signing key not in scoreboard keyring)"


def test_signature_status_unchecked_when_empty():
    assert sb._signature_status([]) == "signature unchecked"


# ---------------------------------------------------------------------------
# sibling_row — status + detail, surfacing signature provenance
# ---------------------------------------------------------------------------

def test_sibling_row_not_submitted_on_unreachable(monkeypatch):
    monkeypatch.setattr(sb, "fetch_json", lambda url, timeout: (None, "unreachable: boom"))
    row = sb.sibling_row({"repo": "x", "url": "https://x.dev/b.json"}, None, None, None, 1.0)
    assert row.status == "not-submitted"
    assert row.checks == 0
    assert row.detail == "unreachable: boom"


def test_sibling_row_pass_surfaces_signature_status(monkeypatch):
    monkeypatch.setattr(sb, "fetch_json", lambda url, timeout: ({"bundle_id": "b"}, "fetched"))
    monkeypatch.setattr(
        sb.run,
        "verify_external_bundle",
        lambda *a: (3, [], [], ["signature cryptographically verified (kid 'k')"]),
    )
    row = sb.sibling_row({"repo": "x", "url": "https://x.dev/b.json"}, {}, None, {}, 1.0)
    assert row.status == "pass"
    assert row.checks == 3
    assert row.detail == "bundle verified; signature verified"


def test_sibling_row_fail_reports_first_failure(monkeypatch):
    monkeypatch.setattr(sb, "fetch_json", lambda url, timeout: ({"bundle_id": "b"}, "fetched"))
    monkeypatch.setattr(sb.run, "verify_external_bundle", lambda *a: (2, ["boom", "second"], [], []))
    row = sb.sibling_row({"repo": "x", "url": "https://x.dev/b.json"}, {}, None, {}, 1.0)
    assert row.status == "fail"
    assert row.detail == "2 failure(s): boom"


# ---------------------------------------------------------------------------
# render_markdown — stable, audience-facing artifact
# ---------------------------------------------------------------------------

def test_render_markdown_shape_and_stability():
    rows = [
        sb.Row(repo="weaver-spec", status="pass", checks=5,
               detail="bundle verified; signature verified", url="https://github.com/dgenio/weaver-spec"),
        sb.Row(repo="contextweaver", status="not-submitted", checks=0,
               detail="unreachable: name resolution", url="https://contextweaver.dev"),
    ]
    md = sb.render_markdown(rows, generated_at="2026-06-03T12:00:00Z", version="0.6.0")
    assert "# Weaver Conformance Scoreboard" in md
    assert "`v0.6.0`" in md
    assert "✅ pass" in md
    assert "signature verified" in md
    # not-submitted rows render a stable phrase, never the raw fetch error.
    assert "no bundle published this run" in md
    assert "name resolution" not in md
