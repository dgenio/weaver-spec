---
applyTo: "docs/**"
---

# Documentation Instructions

## Verification rules

- When editing docs that describe layer responsibilities or data flow, verify claims against the artifact ownership table in `docs/BOUNDARIES.md` and invariants in `docs/INVARIANTS.md`.
- Never modify a Mermaid diagram without checking it against the `BOUNDARIES.md` artifact ownership table. The table is canonical; diagrams are derived.

## Authority

When docs conflict, the authority hierarchy applies: `INVARIANTS.md` → `BOUNDARIES.md` → `ARCHITECTURE.md` → everything else. See `AGENTS.md` for details.
