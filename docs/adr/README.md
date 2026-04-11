# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for breaking changes to Core contracts in weaver-spec.

## What is an ADR?

An ADR is a short document that captures a significant architectural decision: what was decided, why, and what the consequences are. In weaver-spec, ADRs are required for any breaking change to a Core contract — a change that would cause existing valid payloads to become invalid, or that removes or renames a required field.

## Why ADRs are required

Breaking Core contract changes affect all three sibling repositories (contextweaver, agent-kernel, ChainWeaver) and every downstream adopter. The ADR process ensures changes are deliberate, visible, and accompanied by a migration path before any code is merged.

See [CONTRIBUTING.md](../../CONTRIBUTING.md#adr-process-for-breaking-contract-changes) for the full step-by-step process (issue → 3-day discussion → PR).

## Naming convention

ADR files follow the pattern:

```text
NNN-short-title.md
```

Where `NNN` is a zero-padded three-digit sequence number (e.g., `001`, `002`) and `short-title` is a lowercase hyphenated description of the decision. Example: `001-remove-legacy-frame-field.md`.

## Using the template

Copy [`template.md`](template.md) to a new file using the naming convention above and fill in each section. Do not leave placeholder text in the final ADR.
