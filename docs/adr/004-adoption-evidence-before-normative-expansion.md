# ADR 004: Require external evidence before normative expansion

- **Status:** Proposed
- **Date:** 2026-08-11
- **Decision owners:** Core Maintainers
- **Related:** #205, #206, #207, #210, #211, #48

## Context

`weaver-spec` began as the shared contract layer for the author-maintained
`contextweaver`, `agent-kernel`, and `ChainWeaver` repositories. That architecture
produced useful schemas, invariants, conformance tooling, and reference
implementations, but the specification surface expanded faster than independent
external adoption evidence.

A pre-1.0 red-team found three risks:

1. **Circular validation.** A contract used by repositories maintained by the
   same author proves feasibility and compatibility, but does not prove that
   independently designed systems need the same abstraction.
2. **Standards overlap.** MCP, A2A, OpenTelemetry, OAuth/OIDC/JOSE, OpenAPI, and
   existing policy systems already own substantial parts of tool transport,
   agent discovery, authentication, telemetry, signed-object mechanics, and
   policy decision logging.
3. **Premature stability.** Calling a contract Core/stable before unrelated
   implementers depend on it creates a compatibility burden that can make later
   simplification harder than necessary.

The project therefore needs an explicit rule for when a useful implementation
concept is allowed to become a normative interoperability commitment.

## Decision

During the pre-1.0 adoption phase, `weaver-spec` will use an **external-evidence
gate** for normative expansion.

### 1. Freeze speculative Core expansion

New Core concepts are frozen unless they are needed to:

- fix an existing correctness or compatibility problem;
- preserve a previously published compatibility promise; or
- satisfy an interoperability need that passes the evidence gate below.

Interesting but unvalidated concepts remain experimental/research work and do
not gain a committed Core-graduation path merely because a dgenio implementation
uses them.

### 2. Require independent interoperability evidence

Before a new concept can graduate toward stable/Core status, its proposal must
show:

1. at least two **independently designed systems** need substantially the same
   semantics;
2. at least one project or organization outside `dgenio` is willing to consume
   or test the representation;
3. the proposal explains why an established standard does not already own the
   concern;
4. the concrete information loss or integration cost removed by the contract is
   documented; and
5. conformance examples/vectors cover the independently observed cases.

Author-maintained sibling repositories may satisfy implementation-feasibility
requirements, but they do **not** count as independent external adoption.

### 3. Prefer mapping to existing standards over local ownership

Before adding normative surface, maintainers must evaluate whether the concern
belongs to an established owner. The working presumption is:

- MCP for agent/tool transport and its protocol authorization mechanisms;
- A2A for agent discovery, skills, tasks/artifacts, and agent-to-agent protocol;
- OAuth/OIDC/mTLS and related standards for identity/authentication;
- JOSE/JWS/JWK/JWKS for signed-object/key-discovery mechanics where suitable;
- OpenTelemetry semantic conventions for generic operational telemetry;
- OpenAPI/JSON Schema for API/interface description;
- existing policy systems for policy-engine implementation and native decision
  logs.

A Weaver contract should remain normative only for a distinct portable semantic
boundary those standards do not already preserve.

### 4. Separate stability from conformance obligation

A contract's stability level and an implementation's required conformance
surface are separate concepts. Optional profiles may require only the contracts
and invariants needed for a specific interoperability claim.

A third-party implementation must not be forced to implement unrelated contract
families simply to claim compatibility with one useful boundary.

### 5. Treat simplification as success

The following are valid outcomes of the evidence process:

- map an existing contract to another standard;
- make it profile-specific rather than universal;
- demote it from Core;
- deprecate/remove it through the normal compatibility process; or
- contribute the missing semantics upstream instead of maintaining a competing
  local standard.

### 6. Use explicit kill criteria

The project will stop or radically shrink the independent-standard ambition if:

- external discovery does not reveal a recurring shared interoperability gap;
- an established standard can cleanly absorb the important semantics;
- meaningful consumers remain exclusively dgenio projects;
- external adopters consistently need only one smaller subset;
- translation cost exceeds interoperability value; or
- proprietary transport, identity, authentication, or cryptographic machinery
  becomes necessary to make the model useful.

These are not project failures. A smaller correctly owned specification is
preferable to a broader unused one.

## Consequences

### Positive

- The stable surface is driven by independent demand rather than architecture
  aesthetics.
- The project can delete or map overlapping contracts before v1 without treating
  that simplification as failure.
- External implementers can influence the model before compatibility promises
  harden.
- Existing standards remain authoritative in their own domains.
- Conformance claims can become narrower and more honest through profiles.

### Negative

- Some attractive contract ideas will remain experimental for longer.
- v1 becomes evidence-gated rather than schedule-gated.
- Maintainers must do external problem discovery and standards research before
  adding normative surface.
- The current Core/Extended labels may require migration once profile/stability
  semantics are finalized.
- Some existing issue/PR work may need to be split, demoted, or abandoned.

### Neutral / expected

- `contextweaver`, `agent-kernel`, and `ChainWeaver` remain valuable reference
  implementations.
- Existing published identifiers and compatibility commitments continue to
  follow the normal versioning/deprecation policy; the freeze does not authorize
  silent breakage.

## Alternatives considered

### Continue the original v1 roadmap using sibling adoption as proof

Rejected. The same maintainer controls the specification and reference
implementations, so this is circular evidence for an industry-facing standard.

### Freeze all contract changes, including fixes

Rejected. Correctness fixes, compatibility repairs, and evidence-backed adoption
work must remain possible.

### Require an external standards foundation before further work

Rejected. Neutral governance should follow genuine independent implementation
activity, not simulate an ecosystem before one exists.

### Keep every current contract but label it experimental

Rejected as a default. If overlap analysis shows another standard owns the
semantics or no real consumer exists, deprecation/removal can be the correct
outcome.

## Implementation / rollout

If this ADR is accepted:

1. `CONTRIBUTING.md` and the PR template enforce the evidence questions.
2. The README links to the adoption-stage guardrails.
3. #205 owns the current Core standards-overlap audit.
4. #138 owns the Extended usage/simplification audit.
5. #207 separates profile obligations from contract stability.
6. #163 defines evidence-derived stability states.
7. #210 gathers independent problem/design-partner evidence.
8. #48 remains blocked until the retained v1 surface passes these gates.
9. Any Charter wording required to make this permanent is updated through the
   Charter's own ADR-governed process after this decision is accepted.

## Revisit criteria

Revisit this ADR after either:

- at least two independent external implementations are maintaining stable
  profile conformance; or
- the independent-standard ambition is intentionally stopped/shrunk under the
  kill criteria.

At that point the project may relax or replace the pre-1.0 freeze with mature
standards governance appropriate to the actual ecosystem.
