# ADR 003: Wire representation and conformance check for the `raw_passthrough` override

**Status:** proposed <!-- proposed | accepted | rejected | superseded by ADR NNN (NNN-short-title.md) -->

---

## Context

[I-01](../INVARIANTS.md#i-01-llm-never-sees-raw-tool-output-by-default) and
[I-05](../INVARIANTS.md#i-05-contextweaver-receives-frames-not-raw-output) forbid
raw tool output reaching the LLM *by default*, with one carve-out: an explicit,
auditable `raw_passthrough` mode "declared in the `CapabilityToken` and recorded
in the audit log." This carve-out is the single highest-risk path in the spec.

Today it exists only in prose. The conformance suite models the **forbidden**
case — `conformance/run.py:frames_have_no_raw_output` rejects any `Frame`
carrying a raw-output key (`raw_output`, `raw`, `raw_result`, `tool_output`) —
but there is **no structural marker** for a *sanctioned* passthrough and **no
positive fixture** exercising it. As a result:

- Implementers have no defined wire shape for declaring an authorized
  passthrough, so each would invent its own.
- The conformance suite cannot distinguish "raw output leaked (violation)" from
  "raw output passed through under an audited, explicit override (allowed)."

Issue [#117](https://github.com/dgenio/weaver-spec/issues/117) asks for positive
and negative conformance fixtures for the override. The negative case is already
covered (`conformance/negative/trace_bundle/i01_frame_carries_raw_output.json`).
The positive case cannot be added without first deciding a wire representation
**and** teaching the I-01 conformance check to exempt a correctly-declared
passthrough — which changes how the spec's most security-critical invariant is
enforced. Per [CONTRIBUTING.md](../../CONTRIBUTING.md#adr-process-for-breaking-contract-changes),
a change that broadens what a contract/check accepts requires an ADR. This ADR
records the proposal so it can be reviewed before any enforcement change lands.

## Decision

> [!NOTE]
> This ADR is **proposed**, not accepted. No enforcement change has been made;
> the conformance check still flags every raw-output-bearing `Frame`. The
> proposal below is what a follow-up implementation PR would land if accepted.

Proposed wire representation — additive and namespaced, mirroring the existing
`x_weaver_signature` convention (ADR 001):

1. **Declaration on the `Frame`.** A sanctioned passthrough `Frame` carries a
   namespaced object `x_weaver_raw_passthrough` alongside the raw-output key,
   e.g.:

   ```json
   {
     "frame_id": "frame-...",
     "capability_id": "org.myapp.trusted_pipe",
     "summary": "...",
     "created_at": "...",
     "raw_output": "...",
     "x_weaver_raw_passthrough": {
       "authorized_by": "tok-...",
       "decision_id": "pd-..."
     }
   }
   ```

2. **Authorization on the `CapabilityToken`.** The authorizing token declares
   the mode via a namespaced marker (`metadata.x_weaver_raw_passthrough: true`
   or a reserved scope entry), so the declaration is rooted in the credential
   I-01/I-05 name — not self-asserted by the Frame alone.

3. **Audit record.** A `TraceEvent` records the passthrough (referencing the
   same `frame_id` / `decision_id`), satisfying "recorded in the audit log."

Proposed conformance change — **additive, does not weaken `FORBIDDEN_FRAME_KEYS`**:

- Keep `frames_have_no_raw_output` as the default I-01 check unchanged.
- Add a new named check that treats a raw-output-bearing `Frame` as compliant
  **only when** all three of the above are present and internally consistent
  (Frame declaration ↔ token authorization ↔ audit TraceEvent). Absent any of
  them, it remains a violation.
- Add a positive corpus fixture (declared + audited passthrough → allowed) and
  keep the existing unauthorized fixture (raw output, no declaration →
  violation).

## Consequences

- **Positive:** the spec's highest-risk conditional becomes conformance-checked
  and interoperable; implementers get one defined shape instead of ad-hoc ones;
  the exemption is gated on an explicit, audited, three-part declaration rather
  than on loosening what counts as raw output.
- **Negative / risk:** it broadens what the I-01 check accepts, so a bug in the
  exemption logic could mask a real leak. This is why it is gated behind this
  ADR and a dedicated review rather than bundled into unrelated work. The
  exemption must fail closed (any missing/ inconsistent part → violation).
- Extended/opt-in: contracts that never use passthrough are unaffected.

## Affected Contracts

No Core **schema** change is required (Core schemas already allow namespaced
`x_*` extension keys via `additionalProperties: true`); the change is to the
normative prose in `INVARIANTS.md` and to the conformance check.

| Contract | Change type | Description |
| ---------- | ------------- | ------------- |
| `frame.schema.json` | none (extension key) | `x_weaver_raw_passthrough` rides on the existing `additionalProperties: true`; no field added to `required` or `properties`. |
| `capability_token.schema.json` | none (extension key) | Authorization marker rides on `metadata` / namespaced extension; no schema change. |
| `trace_event.schema.json` | none | Existing event types/fields suffice to record the passthrough. |

## Migration Path

No migration for existing payloads: they contain no `x_weaver_raw_passthrough`
and remain valid and (for Frames) still subject to the unchanged default check.
Adopters that need passthrough opt in by emitting the three-part declaration
above once this ADR is accepted and the check ships.

## Cross-Repo Impact

| Repository | Impact | Coordination required? |
| ------------ | -------- | ------------------------ |
| contextweaver | Consumes Frames; would learn to recognize the passthrough marker as the sanctioned exception when ingesting. | yes (if accepted) |
| agent-kernel | Owns the firewall; would emit the token authorization + Frame declaration + audit TraceEvent when passthrough is configured. | yes (if accepted) |
| ChainWeaver | None directly; passthrough is a kernel/contextweaver concern. | no |
