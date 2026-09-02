# Adoption-stage guardrails

> [!IMPORTANT]
> This document records the **proposed adoption-stage operating policy** tracked by
> [#206](https://github.com/dgenio/weaver-spec/issues/206) and the broader
> [adoption reset epic #211](https://github.com/dgenio/weaver-spec/issues/211).
> It does not override the Charter or the existing ADR process. Any substantive
> governance change that belongs in the Charter must follow that process.

`weaver-spec` is intentionally pre-1.0. During the current adoption phase, the
main risk is expanding the specification faster than independent interoperability
demand can validate it. The project therefore optimizes for **minimality,
external evidence, and compatibility with existing standards** rather than for
contract count.

## Current operating posture

Until the adoption reset is resolved:

- do not add new Core concepts merely because they are useful to a dgenio
  implementation;
- existing Core may receive correctness fixes, contradiction fixes, compatibility
  repairs, and changes required by validated adoption work;
- new concepts start as experimental/research unless they pass the external
  evidence gate below;
- dgenio sibling repositories are reference implementations, not independent
  adoption evidence;
- deletion, demotion, profile-scoping, or contribution to an upstream standard are
  valid successful outcomes.

The v1 hardening umbrella is blocked while this scope is revalidated; see
[#48](https://github.com/dgenio/weaver-spec/issues/48).

## External-evidence gate

Before a new concept can graduate toward stable/Core status, its proposal should
show all of the following:

1. At least two independently designed systems need substantially the same
   semantics.
2. At least one external project or organization outside `dgenio` is willing to
   consume or test the representation.
3. The proposal explains why an established standard does not already own the
   concern.
4. The proposal identifies concrete information loss or integration cost removed
   by the contract.
5. Conformance examples/vectors cover the independently observed use cases.

For a v1-stable surface, the expected bar is higher: independent organizations,
multiple implementation languages, and at least one implementation primarily
owned outside `dgenio`.

## Standards ownership check

Before adding normative surface, check whether the concern is already owned by an
established ecosystem. The detailed audit is tracked by
[#205](https://github.com/dgenio/weaver-spec/issues/205).

The working presumption is to delegate, not duplicate:

| Concern | Prefer existing owner |
| --- | --- |
| Agent-to-tool transport and protocol authorization | MCP and its authorization extensions |
| Agent-to-agent transport, discovery, skills, task/artifact exchange | A2A |
| Authentication and identity | OAuth 2.x, OpenID Connect, mTLS, and related standards |
| JSON signing/key-discovery mechanisms | JOSE/JWS/JWK/JWKS where suitable |
| Generic GenAI operational telemetry | OpenTelemetry semantic conventions |
| API description | OpenAPI / JSON Schema as applicable |
| Policy-engine implementation | Existing policy/authorization systems |

A Weaver contract should remain normative only when it represents a distinct,
portable semantic boundary that these standards do not already preserve.

## Evidence ladder

Not all integrations prove the same thing:

| Evidence | What it proves |
| --- | --- |
| `dgenio` builds an adapter | Technical feasibility |
| External maintainer co-builds an adapter | Interest |
| External maintainer implements without `dgenio` code | Independent demand |
| External maintainer keeps conformance in CI and survives a spec upgrade | Adoption |

The external discovery programme is tracked by
[#210](https://github.com/dgenio/weaver-spec/issues/210).

## Compatibility claims

The existing single `Weaver-compatible` claim is under review. An external
implementation should not be required to adopt unrelated contract families to
claim a useful interoperability boundary. Profile-based conformance is tracked by
[#207](https://github.com/dgenio/weaver-spec/issues/207).

Conformance should also be language-neutral: normative vectors and expected
results must be implementable independently of the Python reference runner. See
[#209](https://github.com/dgenio/weaver-spec/issues/209).

## Security-specific rule

A security-sensitive contract does not graduate to Core merely because the
reference implementations use it. In particular,
`CapabilityTokenSignature` remains Extended while
[#208](https://github.com/dgenio/weaver-spec/issues/208) evaluates JOSE/JWS and
other established-envelope options. Core security semantics require independent
security review and external interoperability evidence.

## Naming gate

External promotion of `Weaver` as a standards brand is paused pending
[#204](https://github.com/dgenio/weaver-spec/issues/204), because OpenTelemetry
already maintains an official project named Weaver in the adjacent
schema/conformance ecosystem. Published schema identifiers remain subject to the
immutability policy regardless of any future branding decision.

## Kill criteria

The project should stop or radically shrink the independent-standard ambition if
any of these becomes true:

- external discovery does not reveal a recurring shared interoperability gap;
- MCP, A2A, OpenTelemetry, or another established standard can cleanly absorb the
  important semantics;
- meaningful consumers remain exclusively `dgenio` projects;
- external adopters consistently need only one small profile or contract;
- translating native framework concepts into this ontology costs more than the
  interoperability benefit;
- proprietary transport, identity, authentication, or cryptographic machinery is
  required to make the model useful.

These are not failure states. Keeping only the part that independent adopters
actually need is preferable to maintaining a broader but unused specification.

## Related work

- [#204](https://github.com/dgenio/weaver-spec/issues/204) — naming/namespace decision
- [#205](https://github.com/dgenio/weaver-spec/issues/205) — standards ownership audit
- [#206](https://github.com/dgenio/weaver-spec/issues/206) — Core freeze and graduation rule
- [#207](https://github.com/dgenio/weaver-spec/issues/207) — profile-based conformance
- [#208](https://github.com/dgenio/weaver-spec/issues/208) — signing/security review
- [#209](https://github.com/dgenio/weaver-spec/issues/209) — language-neutral conformance
- [#210](https://github.com/dgenio/weaver-spec/issues/210) — external design-partner validation
- [#211](https://github.com/dgenio/weaver-spec/issues/211) — adoption reset epic
