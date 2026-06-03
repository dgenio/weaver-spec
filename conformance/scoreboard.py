#!/usr/bin/env python3
"""Weaver public conformance scoreboard builder (issue #51).

Build-time / CI tooling, like the rest of ``conformance/``: never imported by
``weaver_contracts`` and never published. It reuses the conformance runner
(:mod:`run`) so the scoreboard and the badges can never disagree with what
``conformance/run.py`` would verdict.

What it does:

* Verifies *this* repo against its own corpus (the ``weaver-spec`` row).
* For each sibling in ``conformance/siblings.yaml``, fetches the TraceBundle the
  sibling publishes at its well-known URL and conformance-checks it with
  ``run.verify_external_bundle``.
* A sibling whose URL is unreachable, missing, or non-JSON is recorded as
  ``not-submitted`` — never as a failure (the scoreboard is a report, not a
  gate). The workflow therefore stays green even before any sibling publishes.
* Renders ``docs/scoreboard.md`` and a shields.io endpoint badge per repo under
  ``docs/badges/``.

Usage::

    python conformance/scoreboard.py                 # write docs/scoreboard.md + badges
    python conformance/scoreboard.py --strict         # exit non-zero if any repo FAILS
    python conformance/scoreboard.py --timeout 5
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
sys.path.insert(0, str(THIS_DIR))

import run  # noqa: E402  (sibling module in conformance/)

DEFAULT_REGISTRY = THIS_DIR / "siblings.yaml"
SCOREBOARD_MD = REPO_ROOT / "docs" / "scoreboard.md"
BADGE_DIR = REPO_ROOT / "docs" / "badges"
SELF_REPO = "weaver-spec"

STATUS_ICON = {"pass": "✅ pass", "fail": "❌ fail", "not-submitted": "⚪ not-submitted"}

# Cap on a fetched sibling bundle. The scoreboard fetches whatever a registered
# sibling publishes, on a schedule in CI; an oversized response must not be able
# to exhaust memory before we even attempt to parse it.
MAX_BUNDLE_BYTES = 5 * 1024 * 1024  # 5 MiB


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse to follow redirects. Enforcing ``https://`` on the registry URL is
    not enough on its own: ``urllib`` would otherwise follow a 30x to ``http://``
    or an internal host, re-opening the SSRF/plaintext hole. With this handler a
    redirect surfaces as an error (caught below) and the sibling is recorded as
    not-submitted rather than dereferenced."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


_OPENER = urllib.request.build_opener(_NoRedirectHandler)


@dataclass
class Row:
    repo: str
    status: str  # "pass" | "fail" | "not-submitted"
    checks: int
    detail: str
    url: Optional[str] = None


def fetch_json(url: str, timeout: float) -> tuple[Optional[dict], str]:
    """Fetch and parse JSON from ``url``. Returns ``(payload, note)``; payload is
    ``None`` when the URL is refused / unreachable / oversized / non-JSON (note
    explains).

    Only ``https://`` URLs are dereferenced — a registry entry pointing at
    ``http://`` or any other scheme is refused rather than fetched, so a bad
    entry can't make the scheduled CI job reach an internal/plaintext endpoint.
    At most ``MAX_BUNDLE_BYTES`` are read before parsing, so a hostile or
    accidental giant response can't exhaust memory."""
    if not url.lower().startswith("https://"):
        return None, "refused: non-https URL"
    try:
        # _OPENER refuses redirects (SSRF guard); https is enforced just above.
        with _OPENER.open(url, timeout=timeout) as resp:  # noqa: S310
            if getattr(resp, "status", 200) >= 300:
                return None, f"refused: redirect not followed (status {resp.status})"
            raw = resp.read(MAX_BUNDLE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return None, f"unreachable: {exc}"
    if len(raw) > MAX_BUNDLE_BYTES:
        return None, f"refused: response exceeds {MAX_BUNDLE_BYTES} bytes"
    try:
        return json.loads(raw), "fetched"
    except json.JSONDecodeError as exc:
        return None, f"not JSON: {exc}"


def self_row() -> Row:
    """Conformance-check this repo against its own corpus."""
    checks, failures = run.run(run.DEFAULT_KEYRING)
    status = "pass" if not failures else "fail"
    detail = "reference corpus" if not failures else f"{len(failures)} failure(s)"
    return Row(repo=SELF_REPO, status=status, checks=checks, detail=detail,
               url="https://github.com/dgenio/weaver-spec")


def _signature_status(notes: list[str]) -> str:
    """Condense ``check_trace_bundle`` notes into a short signature status for the
    scoreboard, so a passing row never implies provenance was verified when the
    crypto check was actually skipped (unknown ``kid``) or the bundle is unsigned."""
    for note in notes:
        if "cryptographically verified" in note:
            return "signature verified"
        if "unsigned bundle" in note:
            return "unsigned"
        if "crypto verify skipped" in note:
            return "signature unverified (signing key not in scoreboard keyring)"
    return "signature unchecked"


def sibling_row(entry: dict, schemas, registry, keyring, timeout: float) -> Row:
    repo = entry["repo"]
    url = entry["url"]
    payload, note = fetch_json(url, timeout)
    if payload is None:
        return Row(repo=repo, status="not-submitted", checks=0, detail=note, url=url)
    checks, failures, notes = run.verify_external_bundle(payload, schemas, registry, keyring)
    status = "pass" if not failures else "fail"
    if failures:
        detail = f"{len(failures)} failure(s): {failures[0]}"
    else:
        detail = f"bundle verified; {_signature_status(notes)}"
    return Row(repo=repo, status=status, checks=checks, detail=detail, url=url)


def render_markdown(rows: list[Row], generated_at: str, version: str) -> str:
    lines = [
        "# Weaver Conformance Scoreboard",
        "",
        "<!-- Generated by conformance/scoreboard.py — do not edit by hand. -->",
        "",
        "Public, automatically-generated conformance status for the Weaver Stack.",
        "Each sibling repo opts in by publishing a signed `TraceBundle` at a",
        "well-known URL; the scoreboard fetches it and runs the conformance pack",
        "(`conformance/run.py`) against it. See [SCOREBOARD.md](SCOREBOARD.md) to",
        "participate.",
        "",
        f"- **Spec contract version:** `v{version}`",
        f"- **Last updated:** {generated_at}",
        "",
        "| Repository | Status | Checks | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        name = f"[{row.repo}]({row.url})" if row.url else row.repo
        checks = str(row.checks) if row.checks else "—"
        # Keep the rendered detail stable across runs: the precise fetch error
        # (DNS vs 403 vs timeout) is console-only, not baked into the artifact.
        detail = "no bundle published this run" if row.status == "not-submitted" else row.detail
        lines.append(f"| {name} | {STATUS_ICON[row.status]} | {checks} | {detail} |")
    lines += [
        "",
        "Status meanings: **pass** — the published bundle satisfies the schemas,",
        "invariants, and signature checks; **fail** — it was reachable but did not;",
        "**not-submitted** — no bundle was reachable at the registered URL this run.",
        "",
        "> [!NOTE]",
        "> A passing row attests that a published artifact satisfies the conformance",
        "> suite at the listed contract version. It does not attest to the",
        "> correctness or security of the implementation behind it.",
        "",
    ]
    return "\n".join(lines)


def build(registry_path: Path, timeout: float) -> list[Row]:
    schemas_by_stem, registry = run.load_schemas()
    keyring = run.load_keyring(run.DEFAULT_KEYRING)
    manifest = yaml.safe_load(registry_path.read_text(encoding="utf-8"))

    rows = [self_row()]
    for entry in manifest.get("siblings", []):
        rows.append(sibling_row(entry, schemas_by_stem, registry, keyring, timeout))
    return rows


def write_outputs(rows: list[Row]) -> None:
    version = run.contract_version()
    generated_at = run._now_z()
    SCOREBOARD_MD.write_text(render_markdown(rows, generated_at, version), encoding="utf-8")
    print(f"Wrote {SCOREBOARD_MD.relative_to(REPO_ROOT)}")
    for row in rows:
        # Each repo gets a shields.io endpoint badge derived from its status.
        result = run.build_result(
            "pass" if row.status == "pass" else "fail",
            row.checks,
            [] if row.status == "pass" else [row.detail],
            mode="bundle" if row.repo != SELF_REPO else "corpus",
            target=row.url,
        )
        endpoint = run.build_shields_endpoint(result)
        if row.status == "not-submitted":
            endpoint.update({"message": "not submitted", "color": "lightgrey", "isError": False})
        run._write_json(BADGE_DIR / f"{row.repo}.json", endpoint)
    print(f"Wrote {len(rows)} badge endpoint(s) to {BADGE_DIR.relative_to(REPO_ROOT)}/")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Weaver conformance scoreboard (#51).")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-URL fetch timeout (s).")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any registered repo FAILS (not-submitted never fails).",
    )
    args = parser.parse_args(argv)

    rows = build(args.registry, args.timeout)
    write_outputs(rows)

    print("\nScoreboard:")
    for row in rows:
        print(f"  {row.repo:16} {STATUS_ICON[row.status]:18} {row.detail}")

    if args.strict and any(r.status == "fail" for r in rows):
        print("\nstrict: at least one repo FAILED.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
