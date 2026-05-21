# Charter

This charter describes governance for `weaver-spec`: how decisions are made, who participates, and how cross-repo work is coordinated. It is intentionally lightweight and grows only when the ecosystem demands it.

For the contribution mechanics (PR workflow, ADR process, six-artifact rule), see [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).

---

## Mission

`weaver-spec` is the canonical specification and shared contract surface for the Weaver Stack. Its sole purpose is to keep `contextweaver`, `agent-kernel`, and `ChainWeaver` interoperable and safe to combine, by publishing minimal, stable, language-agnostic contracts (JSON Schemas + a thin Python mirror) and the invariants that guard them. The repository is documentation and contracts only — never runtime logic.

---

## Roles

| Role | Responsibilities | How you become one |
| ----- | ----------------- | -------------------- |
| **Contributor** | Open issues, propose PRs, write ADRs, file bugs. | Anyone who opens a PR or issue. |
| **Reviewer** | Review PRs in their area of expertise; no merge rights. | Sustained quality review activity; invited by a Maintainer. |
| **Maintainer** | Triage issues, approve PRs, request changes. Merge rights for non-Core docs and CI changes. | Invited by Core Maintainers based on sustained reviewer activity. |
| **Core Maintainer** | Final approval for Core contract changes, ADRs, and version bumps. Owns the authority hierarchy (`INVARIANTS.md` → `BOUNDARIES.md` → `ARCHITECTURE.md`). | Invited by existing Core Maintainers. |

---

## Decision flow

1. **Issue** — every change starts as a GitHub issue. Use the bug, feature, or ADR-proposal template under [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/).
2. **ADR (if applicable)** — breaking Core contract changes follow the ADR process documented in [CONTRIBUTING.md](CONTRIBUTING.md#adr-process-for-breaking-contract-changes): minimum 3 business days of discussion before the PR opens.
3. **PR** — opened against `main`. Required reviewers come from [`.github/CODEOWNERS`](.github/CODEOWNERS).
4. **Working Group (if applicable)** — see below.
5. **Merge** — by a Maintainer (non-Core changes) or Core Maintainer (Core contract changes and ADRs).

---

## Working Groups

A **Working Group** is formed on demand for any change that affects two or more sibling repositories. Working Groups are short-lived: they spawn when the ADR or coordinating issue opens and dissolve when the corresponding PR merges.

A Working Group must include:

- One Maintainer or Core Maintainer from `weaver-spec`.
- At least one designated reviewer from each affected sibling repository (`contextweaver`, `agent-kernel`, `ChainWeaver`).

Working Group sign-off is recorded in the merging PR's description under a `## Cross-repo impact` section, with a link to the issue or ADR that opened the group.

---

## Current maintainers

| GitHub handle | Role |
| --------------- | ------ |
| [@dgenio](https://github.com/dgenio) | Core Maintainer |

Roster updates are submitted via PR amending this section.

---

## Updating this charter

Substantive changes to this charter (role definitions, decision flow, Working Group rules) follow the ADR process. Editorial fixes (typos, link rot, roster updates) may merge as a normal docs PR.
