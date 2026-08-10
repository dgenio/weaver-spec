# Conformance Scoreboard — Participation

The [checked-in scoreboard](scoreboard.md) is a timestamped snapshot of a
successful Scoreboard workflow run. For the **latest** sibling
reachability/conformance result, use the most recent `Scoreboard` GitHub Actions
run: the workflow writes the generated table to its job summary and uploads
`scoreboard.md` plus badge JSON as the `conformance-scoreboard` artifact.

Participation is **opt-in** and costs one file plus one published JSON document.

> [!NOTE]
> The scoreboard is a **report, not a gate**. A repo that publishes nothing is
> shown as `not-submitted`, never as failing. A passing row attests that a
> published artifact satisfies the conformance suite at a contract version — it
> does not attest to the correctness or security of the implementation.

## How it works

1. Each participating repo publishes a signed `TraceBundle` (the Extended
   audit-chain envelope — see [TRACE_BUNDLE.md](TRACE_BUNDLE.md)) at a stable,
   well-known URL.
2. The [`scoreboard.yml`](../.github/workflows/scoreboard.yml) workflow runs on a
   weekly schedule (and on demand). For each repo registered in
   [`conformance/siblings.yaml`](../conformance/siblings.yaml) it fetches the URL
   and runs the conformance pack against the bundle:

   ```bash
   python conformance/run.py --bundle <fetched-bundle.json>
   ```

3. [`conformance/scoreboard.py`](../conformance/scoreboard.py) renders a current
   `scoreboard.md` in the workflow workspace and a shields.io endpoint badge per
   repo under `docs/badges/`. The build is uploaded as an artifact and written to
   the job summary. The repository's committed [`scoreboard.md`](scoreboard.md)
   is intentionally labelled with its generation timestamp so it cannot be
   mistaken for a live status endpoint.

## Participate

1. **Publish a bundle.** Serve a conformant `TraceBundle` at a stable URL. The
   convention is `.well-known/conformance.json` on your project domain, e.g.
   `https://your-project.dev/.well-known/conformance.json`. Sign it (see
   [SIGNING.md](SIGNING.md)) so verifiers who hold your signing key can confirm
   provenance. Note: the public scoreboard always validates the signature
   *envelope*, but only cryptographically verifies it when your signing key
   (`kid`) is in its keyring. The default scheduled run carries only this repo's
   test keyring, so a sibling's row currently attests schema + invariant
   conformance — the row detail states whether the signature was actually
   verified, left unverified, or the bundle was unsigned.
2. **Register.** Add an entry to
   [`conformance/siblings.yaml`](../conformance/siblings.yaml):

   ```yaml
   siblings:
     - repo: your-project
       url: https://your-project.dev/.well-known/conformance.json
   ```

3. **Verify locally** before opening a PR:

   ```bash
   python conformance/run.py --bundle path/to/your/bundle.json
   ```

## Hosting the rendered scoreboard (optional)

The workflow uploads generated `scoreboard.md` + `docs/badges/` as an artifact
and writes the table to the run's job summary, so it works with no extra setup.
To serve a continuously refreshed web page, add an explicit deployment step or
site pipeline; simply enabling Pages over the repository's committed `docs/`
directory serves the timestamped committed snapshot, not each scheduled workflow
artifact automatically.

## Related

- [CONFORMANCE.md](CONFORMANCE.md) — what the conformance suite checks.
- [SELF_CERTIFICATION.md](SELF_CERTIFICATION.md) — the per-repo badge + flow.
- [scoreboard.md](scoreboard.md) — timestamped committed snapshot.
