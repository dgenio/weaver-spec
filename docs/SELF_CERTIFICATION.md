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

   The result is CI tooling output (not a Weaver runtime contract), but it is a
   stable interchange shape validated against
   [`contracts/json/extended/conformance_result.schema.json`](../contracts/json/extended/conformance_result.schema.json)
   (#116). Its shape:

   ```json
   {
     "result_version": "1",
     "contract_version": "0.8.0",
     "mode": "corpus",
     "target": null,
     "status": "pass",
     "checks_run": 47,
     "failures": 0,
     "failure_detail": [],
     "failure_records": [],
     "generated_at": "2026-07-05T12:00:00Z",
     "runner": "weaver-spec conformance/run.py"
   }
   ```

   `failures` is the failure *count*; `failure_detail` is the list of failure
   messages (empty when `status` is `pass`). `failure_records` is the structured
   per-failure view (#145): each entry carries a `kind`
   (`positive`/`negative`/`invariant`/`schema`/`tracebundle`/`input`) and the
   same `message`, plus — where known — `payload`, `schema`, `keyword`, `path`,
   and `invariant_id`, so an agent can map a failure to the offending
   fixture/field without parsing the human strings. `target` is `null` in
   `corpus` mode and the bundle URL/path in `bundle` mode.

3. **Display the badge.** Host the emitted endpoint JSON and reference it via the
   [shields.io endpoint](https://shields.io/badges/endpoint-badge):

   ```markdown
   ![Weaver-compatible](https://img.shields.io/endpoint?url=https://your-project.dev/weaver-compatible.json)
   ```

   This repo's own badge lives at [`docs/badges/weaver-spec.json`](badges/weaver-spec.json)
   and is regenerated (and checked for staleness) by the `reference-impl` CI job.

## Freshness and validity

A conformance result is a point-in-time attestation, so a published result is
trustworthy only while it stays current (#150):

> [!IMPORTANT]
> A published result is **valid** only when both hold:
>
> - its `generated_at` is within **90 days** of now, and
> - its `contract_version` shares the **current contract MAJOR**.
>
> A result that is older than the window, or that attests against a superseded
> MAJOR, MUST NOT be displayed as current — regenerate it. Display a badge only
> for a result that still satisfies both conditions.

The reference checker is `conformance/run.py:is_result_fresh(result)`, which
returns `(fresh, reasons)` using only the result's existing `generated_at` and
`contract_version` fields — no extra contract surface. The 90-day window is a
deliberately generous default (roughly a release cadence); tighten it in your
own pipeline if you publish more often.

The public [scoreboard](scoreboard.md) is unaffected by staleness because it
**re-verifies each sibling's live bundle on every run** rather than trusting a
previously published result — so a stale result can never reach it. The policy
above governs a result JSON that a third party hosts and displays directly.

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
- [SIGNING.md](SIGNING.md#trust-model) — what a verified signature does and does not attest.
- [examples/reference_impl/](../examples/reference_impl/) — zero-to-passing example.
