# Self-Certification & the "Weaver-compatible" Badge

Any implementer who passes the conformance suite can display a
**`weaver-compatible vX.Y`** badge. The badge is derived from a verifiable
conformance result, so it cannot disagree with what the suite actually checks.

> [!IMPORTANT]
> The badge attests that an implementation **passed the conformance suite at a
> stated contract version**. It does **not** attest to the correctness,
> security, or production-readiness of the implementation. Display it only for a
> version you actually pass.

## The flow

1. **Pass the suite.** Make your artifacts conform — start from the
   [reference implementation](../examples/reference_impl/) and
   [CONFORMANCE.md](CONFORMANCE.md).
2. **Emit a result.** The runner writes a machine-readable result and a
   shields.io endpoint badge from the *same* run, so the two can never drift:

   ```bash
   python conformance/run.py \
     --emit-result conformance-result.json \
     --emit-badge weaver-compatible.json
   ```

   The result is CI tooling output (not a Weaver contract). Its shape:

   ```json
   {
     "result_version": "1",
     "contract_version": "0.6.0",
     "mode": "corpus",
     "status": "pass",
     "checks_run": 40,
     "failures": 0,
     "generated_at": "2026-06-03T12:00:00Z",
     "runner": "weaver-spec conformance/run.py"
   }
   ```

3. **Display the badge.** Host the emitted endpoint JSON and reference it via the
   [shields.io endpoint](https://shields.io/badges/endpoint-badge):

   ```markdown
   ![Weaver-compatible](https://img.shields.io/endpoint?url=https://your-project.dev/weaver-compatible.json)
   ```

   This repo's own badge lives at [`docs/badges/weaver-spec.json`](badges/weaver-spec.json)
   and is regenerated (and checked for staleness) by the `reference-impl` CI job.

## Consistency with the scoreboard

The public [scoreboard](scoreboard.md) renders a badge per repo from the
identical `build_shields_endpoint` logic in
[`conformance/run.py`](../conformance/run.py). A repo that publishes a
`TraceBundle` (see [SCOREBOARD.md](SCOREBOARD.md)) gets a scoreboard badge backed
by the same verdict, so the self-served badge and the scoreboard badge agree by
construction.

## Related

- [CONFORMANCE.md](CONFORMANCE.md) — what the suite verifies.
- [SCOREBOARD.md](SCOREBOARD.md) — publishing a bundle for the public scoreboard.
- [examples/reference_impl/](../examples/reference_impl/) — zero-to-passing example.
