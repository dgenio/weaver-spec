# Deprecations Register

This document is the **authoritative register** of every field, type, schema, or constraint that has been deprecated in `weaver-spec`. Removals are governed by the policy below.

For the overall versioning policy, see [`docs/VERSIONING.md`](VERSIONING.md). For the contribution process that lands deprecations, see [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Policy

The repository enforces the following deprecation rules:

1. **Registration is required.** A deprecation does not exist until it has a row in the table below. A `description` note or a `# Deprecated` Python comment without a register row is not a deprecation; it is a comment.
2. **One-MAJOR retention rule.** A deprecated field, type, or constraint must remain in Core for **at least one full MAJOR version** before it may be removed. A field deprecated in `0.x` is therefore eligible for removal no earlier than `1.0.0`; a field deprecated in `1.x` is eligible no earlier than `2.0.0`.
3. **Removal requires an ADR.** Removing a deprecated item is a breaking Core contract change and must follow the ADR process documented in [CONTRIBUTING.md](../CONTRIBUTING.md#adr-process-for-breaking-contract-changes).
4. **The removal PR must update the register row.** Set `Removed in` to the actual removed-in version and move the row to the "Removed" section. PRs that remove a registered item without updating the register fail review.
5. **Adding a row also requires updates.** The same PR that deprecates an item must also update:
   - The relevant JSON Schema — mark the field with `"deprecated": true` and add a deprecation note in its `description`, per [`docs/VERSIONING.md`](VERSIONING.md#deprecation-policy).
   - The relevant Python type — add a `# Deprecated in X.Y.Z; remove in N.0.0` comment, per [`docs/VERSIONING.md`](VERSIONING.md#deprecation-policy).
   - `CHANGELOG.md` under the version that deprecates the item.

---

## Active deprecations

The register is currently empty. No fields, types, schemas, or constraints in Core or Extended contracts are currently deprecated.

| Item | Schema or module | Deprecated in | Eligible to remove | Migration step | Linked ADR |
| ------ | ------------------ | --------------- | -------------------- | ---------------- | ------------ |
| *(none yet)* | | | | | |

---

## Removed

Items that were deprecated and have since been removed. Kept here as an audit record; removals are not reversible without a new ADR.

| Item | Schema or module | Deprecated in | Removed in | Linked ADR |
| ------ | ------------------ | --------------- | ------------ | ------------ |
| *(none yet)* | | | | |

---

## How to add a row

1. Open an issue describing the deprecation, its motivation, and the migration path for adopters.
2. Open a PR that:
   - Adds the row to the **Active deprecations** table above.
   - Sets `Deprecated in` to the version that the PR will release.
   - Sets `Eligible to remove` to the next MAJOR boundary at minimum (e.g., a `0.x` deprecation gets `Eligible to remove: 1.0.0`).
   - Adds a one-sentence migration step.
   - Marks the JSON Schema field (where applicable) with `"deprecated": true` and a deprecation note in its `description`.
   - Marks the Python type (where applicable) with a `# Deprecated in X.Y.Z; remove in N.0.0` comment.
   - Adds a CHANGELOG entry.
   - Links the relevant issue or ADR.
3. PRs that remove a deprecated item must reference the row being removed and move it to the **Removed** section in the same PR.

---

## Worked example (illustrative — not a live deprecation)

This walks the full lifecycle of a **hypothetical** field, `Frame.legacy_summary`,
so contributors can see exactly what each step looks like. Nothing below is a
real deprecation; it is documentation only and is intentionally **not** in the
Active table above (so the register lint does not treat it as live).

1. **Deprecate in `0.9.0`.** The PR adds a row to Active deprecations:

   ```text
   | `Frame.legacy_summary` | frame.schema.json | 0.9.0 | 1.0.0 | Use `summary` instead. | — |
   ```

   In the same PR it marks the field `"deprecated": true` with a note in its
   `description`, adds a `# Deprecated in 0.9.0; remove in 1.0.0` comment on the
   Python field, and adds a CHANGELOG entry. Because `0.9.0` is a `0.x`
   deprecation, the earliest eligible removal is the next MAJOR boundary,
   `1.0.0` — `scripts/check_deprecations.py` fails the PR if the row claims an
   earlier `Eligible to remove`.

2. **Retain through `1.0.0`.** The field stays present and validating for at
   least one full MAJOR. Adopters migrate to `summary` during this window.

3. **Remove in `1.0.0` via ADR.** A breaking-change ADR (see
   [CONTRIBUTING.md](../CONTRIBUTING.md#adr-process-for-breaking-contract-changes))
   authorizes removal. The removal PR deletes the field, sets `Removed in` to
   `1.0.0`, and moves the row from Active to the Removed table.

## Why this register exists

`docs/VERSIONING.md` defines the deprecation policy in prose ("remains in the Core for at least one full major version"). Without a register, adopters cannot audit which fields are headed for removal and reviewers cannot enforce the retention rule mechanically. This document is the machine-auditable companion to that policy.
