# Documentation Conventions

This page defines a lightweight convention for distinguishing **binding requirements** from **explanatory notes** and from **illustrative examples** in the weaver-spec docs.

> [!NOTE]
> This is a conventions doc, not a specification. The contracts and invariants themselves remain authoritative — see `docs/INVARIANTS.md`, `docs/BOUNDARIES.md`, and `docs/ARCHITECTURE.md`. The convention below is purely about how the **same content** is **marked up** so readers and sibling-repo implementers can tell at a glance which sentences are binding.

---

## The three content kinds

| Kind | Meaning | Marker |
| ----- | -------- | -------- |
| **Normative** | Binding requirement. A spec-compliant implementation MUST satisfy it. | `> [!IMPORTANT]` GitHub callout |
| **Informative** | Explanation, rationale, context, or guidance. Helpful, not enforced. | `> [!NOTE]` GitHub callout |
| **Example** | Illustrative payload, command, or scenario. Not a payload shape requirement beyond the schema. | Fenced code block, optionally headed by an `**Example:**` label |

GitHub renders `> [!IMPORTANT]` and `> [!NOTE]` as styled callouts in `.md` previews on github.com. They also degrade gracefully to plain blockquotes on other Markdown renderers.

---

## When to use each marker

### Normative — `> [!IMPORTANT]`

Use for statements that an implementation MUST, MUST NOT, or SHALL satisfy to be spec-compliant. Examples:

- Invariants I-01 through I-07.
- Six-artifact rule for Core contract PRs.
- The boundary that contextweaver ingests `Frame` only, never raw output.
- Schema constraints (`required`, `enum`, `minLength`) that the contracts enforce.

> [!IMPORTANT]
> When uncertain whether a sentence is normative, mark it as a **note** instead. Silently upgrading guidance into a requirement changes the spec.

### Informative — `> [!NOTE]`

Use for rationale, context, design history, or guidance that helps the reader but is not enforced. Examples:

- "This boundary exists because raw output may contain secrets..."
- "Adopters typically use slug-style IDs, though any non-empty string is valid."
- Cross-references to related sections.

### Example — fenced code block

Use fenced code blocks for payloads, commands, and scenarios. Mark them clearly if context is ambiguous:

````markdown
**Example:** a minimal `RoutingDecision` payload.

```json
{ "id": "rd-20260520-001", "choice_cards": [], "selected_item_id": null }
```
````

> [!NOTE]
> Examples illustrate one valid shape. They are **not** payload templates — only the JSON Schema is normative for payload shape.

---

## Applying the convention

Apply the convention to the **high-traffic spec pages first**, then extend gradually:

1. `README.md`
2. `docs/INVARIANTS.md` (invariants are already normative; surface them visually)
3. `docs/BOUNDARIES.md` (boundary statements are normative; rationale is informative)
4. `docs/ARCHITECTURE.md`
5. `docs/GLOSSARY.md`
6. Other docs as they are revised

Do **not** rewrite full pages to apply the convention. Mark text only where it improves clarity and where the meaning is unambiguous.

---

## Authority hierarchy

When this convention conflicts with canonical docs, canonical docs win. Per `AGENTS.md`:

`docs/INVARIANTS.md` → `docs/BOUNDARIES.md` → `docs/ARCHITECTURE.md` → everything else.

A `> [!IMPORTANT]` callout in any doc cannot promote a non-invariant into an invariant or a non-boundary into a boundary. If a callout in a lower-authority doc appears to contradict a higher-authority doc, the higher-authority doc wins and the lower-authority doc should be reworded.

---

## RFC 2119 keywords (optional)

The convention does not require RFC 2119 keywords (MUST / SHOULD / MAY). They may be used inside a normative callout for additional precision:

> [!IMPORTANT]
> Every PolicyDecision MUST be paired with a TraceEvent recording the same `capability_id` and `principal`. Implementations MAY batch multiple TraceEvents into one audit-log record so long as the pairing is preserved.

When using RFC 2119 keywords, capitalize them (`MUST`, not `must`) so they are visually distinct.

---

## Update policy

- **Adding the convention to a doc:** acceptable as a docs-only PR; no version bump.
- **Removing or renaming a marker on an existing requirement:** treat as a possibly-breaking documentation change — verify against `docs/INVARIANTS.md` first.
- **Adding a new marker style:** propose in an issue first; this page is the single source of truth for the convention.
