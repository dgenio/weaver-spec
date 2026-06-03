# Conformance Scoreboard — Participation

The [public scoreboard](scoreboard.md) shows, for each Weaver Stack repo,
whether its published artifacts pass the conformance suite. Participation is
**opt-in** and costs one file plus one published JSON document.

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

3. [`conformance/scoreboard.py`](../conformance/scoreboard.py) renders
   [`scoreboard.md`](scoreboard.md) and a shields.io endpoint badge per repo
   under [`docs/badges/`](badges). The build is published as a workflow artifact
   and written to the job summary.

## Participate

1. **Publish a bundle.** Serve a conformant `TraceBundle` at a stable URL. The
   convention is `.well-known/conformance.json` on your project domain, e.g.
   `https://your-project.dev/.well-known/conformance.json`. Sign it (see
   [SIGNING.md](SIGNING.md)) so verifiers can confirm provenance.
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

The workflow uploads `scoreboard.md` + `docs/badges/` as an artifact and writes
the table to the run's job summary, so it works with no extra setup. To serve it
as a web page, enable **GitHub Pages** for this repo (Settings → Pages) and point
it at `docs/`; the badge endpoints are then consumable via
`https://img.shields.io/endpoint?url=<raw badge URL>`. Enabling Pages is a
repository-admin action and is intentionally left out of the workflow.

## Related

- [CONFORMANCE.md](CONFORMANCE.md) — what the conformance suite checks.
- [SELF_CERTIFICATION.md](SELF_CERTIFICATION.md) — the per-repo badge + flow.
- [scoreboard.md](scoreboard.md) — the generated scoreboard (do not edit by hand).
