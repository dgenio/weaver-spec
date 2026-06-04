# ADR 002: The context-firewall vs Frame-firewall seam

**Status:** accepted

---

## Context

The stack has historically used the phrase "context firewall" for two different
things, and the overlap is the most confusing boundary in the ecosystem:

1. **agent-kernel's output firewall** — the choke point that turns raw tool
   output into a `Frame` (+ `Handle`) before anything reaches contextweaver or
   the LLM. This is the firewall invariants
   [I-01](../INVARIANTS.md#i-01-llm-never-sees-raw-tool-output-by-default) and
   [I-05](../INVARIANTS.md#i-05-contextweaver-receives-frames-not-raw-output)
   describe, and the boundary [`BOUNDARIES.md`](../BOUNDARIES.md) calls "Kernel
   Owns the Firewall."
2. **contextweaver's stage-4 firewall** — a budgeted *selection/packing* stage
   that decides what already-safe context enters the prompt.

Calling both a "firewall" invites implementers to re-derive output-firewalling
inside contextweaver from raw output, which would collapse the safety boundary.
contextweaver#352 raises this on the implementation side; the spec must own the
resolution so both repos agree. weaver-spec issue
[#84](https://github.com/dgenio/weaver-spec/issues/84) tracks it.

I-05 already states that contextweaver ingests `Frame`s only, but it was written
as a bare restatement of I-01 and did not name the canonical seam or mark the
legacy raw-output ingestion path as non-canonical.

## Decision

Define a single canonical seam — the **`Frame` seam** — and use it consistently:

- **agent-kernel produces** a `Frame` at the output-firewall boundary. Raw tool
  output never crosses that boundary; it stays behind a `Handle`.
- **contextweaver consumes** `Frame`s and performs budgeted selection/packing.
  Its "stage-4 firewall" is **context budgeting over already-safe Frames**, not a
  second output-firewall. contextweaver must not re-derive firewalling from raw
  output on the canonical path.
- Reserve the unqualified word **"firewall"** for the agent-kernel output
  firewall. Refer to contextweaver's stage as **context budgeting / selection**.

This is recorded as a **clarification** of the existing boundary, not a change to
it: the artifact ownership table in `BOUNDARIES.md` is unchanged (agent-kernel
still owns raw output → `Frame`/`Handle`; contextweaver still ingests `Frame`
only). I-05 is tightened in wording — the canonical `Frame` path is the default
for first-class ingestion, and any raw-output ingestion *other than* the
explicit, auditable `raw_passthrough` override of I-01 is **non-canonical /
non-compliant** — without weakening any constraint.

## Consequences

- **Easier:** implementers stop conflating the two firewalls; the seam has one
  name and one owner; partial adopters (contextweaver without agent-kernel) know
  they must still produce `Frame`s upstream.
- **Harder / limits:** the *behavioral* half of I-05 (an ingestion interface
  that refuses raw output) cannot be asserted against a static artifact, so it
  remains a sibling-harness check (consistent with
  [`conformance/invariants.yaml`](../../conformance/invariants.yaml), which scopes
  I-03/I-05/I-07 to sibling harnesses). The spec asserts the *artifact* half — a
  `Frame` at the seam carries no raw output — via the existing I-01 check
  (`frames_have_no_raw_output`), now exercised by a seam-specific negative
  fixture.

## Affected Contracts

No Core contract schema changes. This ADR clarifies normative prose only.

| Contract | Change type | Description |
| -------- | ----------- | ----------- |
| (none) | clarification | `Frame` / `Handle` shapes unchanged; I-05 wording tightened; new boundary section in `BOUNDARIES.md`. |

## Migration Path

No payloads change. Implementers should:

1. Stop using "firewall" for contextweaver's selection stage; call it context
   budgeting.
2. Confirm contextweaver's ingestion accepts `Frame` only — any raw-output
   ingestion path is non-canonical and should be removed or gated behind the
   declared `raw_passthrough` audit path (I-01).

## Cross-Repo Impact

| Repository | Impact | Coordination required? |
| ---------- | ------ | ---------------------- |
| contextweaver | Adopt the seam wording; ensure ingestion is `Frame`-only (contextweaver#352). | yes |
| agent-kernel | Confirm it is the sole owner of the output firewall producing `Frame`/`Handle`. | yes |
| ChainWeaver | None — delegates execution; never touches raw output. | no |

> [!NOTE]
> ADR numbering: this is ADR 002. The hardening umbrella
> [#48](https://github.com/dgenio/weaver-spec/issues/48) sketched several
> sub-ADRs starting at 002; those should be renumbered from 003 when they land,
> since 002 is taken by this decision.
