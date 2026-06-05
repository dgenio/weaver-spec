# Ecosystem Launch Post — Draft

> [!NOTE]
> This is a **draft marketing artifact**, not a specification. It is kept in the
> repo so the ecosystem-level narrative has one versioned source. It is distinct
> from each repo's own launch. Keep it honest about maturity — the project is
> early and single-author; lead with the architecture and the ideas. The
> canonical technical source is [`docs/WEAVER_STACK.md`](WEAVER_STACK.md).

---

## Title options

- "The Weaver Stack: a governed, self-improving agent runtime — assembled from
  small, independent contracts"
- "Show HN: Weaver Stack — bounded tool routing, a firewalled kernel, and a
  closed learning loop, sharing one contract set"

---

## Blog / Show HN body

Most agent frameworks ship as one large runtime. The Weaver Stack is the
opposite bet: a handful of **independently adoptable** repositories that agree on
**one shared contract layer**, so each piece is useful alone and the set composes
without lock-in.

The four problems it targets — tool explosion, context bloat, unsafe execution,
and flaky orchestration — are familiar. What is different here is solving them
behind shared, language-agnostic contracts (JSON Schemas + a stdlib Python
mirror) rather than inside one framework's internals:

- **contextweaver** compiles context and routes — the LLM picks from a small set
  of pre-screened `ChoiceCard`s instead of an unbounded tool list.
- **agent-kernel** authorizes, executes, and firewalls. Raw tool output never
  reaches the model by default; only a safe `Frame` (and an opaque `Handle`)
  leaves the kernel. Every call is recorded as a `TraceEvent`.
- **ChainWeaver** runs deterministic flows, delegating every step back to the
  kernel.
- A **closed learning loop** turns those audit traces into reviewed
  `LessonCard` / `SkillCard` artifacts (via lessonweaver) that re-enter routing
  and improve the next request.

Because the boundaries are defined as **contracts, not code coupling**, you can
adopt one layer and bring your own for the rest — or read the schemas and
integrate nothing at all.

### The honest part

This is early, single-author work. The credible deliverable today is the
**architecture and the contracts**: the invariants, the responsibility
boundaries, and the schemas in
[weaver-spec](https://github.com/dgenio/weaver-spec) — not production scale or an
adoption story. If you care about *how to draw the boundaries* for a safe,
auditable, self-improving agent runtime, that is what this is for.

### Try it

The cross-repo [golden path](GOLDEN_PATH.md) is the centerpiece: one request
flowing through routing → execution → audit → learning. The runnable
[reference implementation](../examples/reference_impl/) constructs every Core
artifact end-to-end and validates it against the schemas.

Start at [weaver-spec](https://github.com/dgenio/weaver-spec); the
[explainer](WEAVER_STACK.md) has the full architecture and the closed-loop
diagram.

---

## Distribution checklist

- [ ] Publish on the landing page / org profile (see the front-door section of
      [`docs/WEAVER_STACK.md`](WEAVER_STACK.md)).
- [ ] Cross-post (blog + Show HN / relevant subreddits) as the *ecosystem*
      story, distinct from the per-repo launches.
- [ ] Link the golden-path demo as the centerpiece proof.
- [ ] Keep claims consistent with the per-repo positioning and the maturity note.
