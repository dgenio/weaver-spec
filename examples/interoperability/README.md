# Minimal Interoperability Examples

Two tiny, self-contained walkthroughs that link the Core contracts together
end-to-end. Their purpose is to give adopters a single place to see exactly
what payloads cross each boundary on the simplest possible request.

- [`happy_path.md`](happy_path.md) — a single-turn happy path:
  `RoutingDecision → PolicyDecision → Frame + Handle → TraceEvent`.
- [`denied_path.md`](denied_path.md) — the same setup, but the policy engine
  denies the call: `RoutingDecision → PolicyDecision(deny) → TraceEvent`.
  No `Frame`, no `Handle`.

These walkthroughs deliberately use **only the Core contracts** that exist
in `contracts/json/`. They do not depend on the Extended types or on
unreleased features.

## Producer / consumer at each step

| Contract | Produced by | Consumed by | First appears in |
| --- | --- | --- | --- |
| `RoutingDecision` | contextweaver | agent-kernel | happy + denied paths |
| `CapabilityToken` | agent-kernel (issuance) | agent-kernel (validation) | happy + denied paths |
| `PolicyDecision` | agent-kernel (policy engine) | caller, audit log | happy + denied paths |
| `Frame` | agent-kernel (firewall) | contextweaver, caller | happy path only |
| `Handle` | agent-kernel (firewall) | HandleStore; caller via authorized resolution | happy path only |
| `TraceEvent` | agent-kernel | audit log | happy + denied paths |

See [`docs/INTEGRATION_MAP.md`](../../docs/INTEGRATION_MAP.md) for the same
mapping plus invariants at each boundary, and
[`docs/LIFECYCLE.md`](../../docs/LIFECYCLE.md) for the phase model.

## Conventions

- Every JSON block is preceded by a `<!-- schema: <name> -->` marker. CI
  extracts these blocks and validates them against
  `contracts/json/<name>.schema.json`.
- IDs use slug-style prefixes (`rd-`, `tok-`, `pd-`, `frame-`, `handle-`,
  `te-`) matching the sample-payload convention.

## How to use these examples

1. Read [`happy_path.md`](happy_path.md) end-to-end to see the canonical
   single-turn flow.
2. Compare it with [`denied_path.md`](denied_path.md) to see what changes on
   denial (and what does **not** change — the same `RoutingDecision` and
   `CapabilityToken` are presented to agent-kernel; only the policy verdict
   differs).
3. For richer scenarios (partial failure, multi-step, routing miss), see
   the dedicated walkthroughs in [`examples/`](..).
