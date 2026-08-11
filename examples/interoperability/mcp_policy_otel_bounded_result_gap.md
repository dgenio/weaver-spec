# MCP + policy engine + OpenTelemetry bounded-result gap experiment

> [!IMPORTANT]
> This is a **non-normative falsification experiment** for
> [#205](https://github.com/dgenio/weaver-spec/issues/205). It intentionally
> starts from existing standards and asks what, if anything, is still missing.
> It does **not** propose a new Core contract or profile.

## Question

Can an ordinary agent/tool system preserve the useful semantics currently spread
across Weaver `Capability`, `CapabilityToken`, `PolicyDecision`, `Frame`,
`Handle`, and `TraceEvent` by using existing standards alone?

The experiment composes:

1. an MCP tool definition + call/result;
2. OAuth-based MCP transport authorization;
3. an existing policy-engine decision record (OPA is the concrete example);
4. OpenTelemetry GenAI tool-execution telemetry;
5. MCP resource links or A2A artifacts for out-of-band/raw artifacts.

Primary references:

- MCP Tools: <https://modelcontextprotocol.io/specification/2025-11-25/server/tools>
- MCP Authorization: <https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization>
- MCP schema / `ResourceLink`: <https://modelcontextprotocol.io/specification/2025-11-25/schema>
- A2A specification / `Artifact`: <https://a2a-protocol.org/dev/specification/>
- OpenTelemetry GenAI semantic conventions: <https://github.com/open-telemetry/semantic-conventions-genai>
- OPA decision logs: <https://www.openpolicyagent.org/docs/management-decision-logs>

## Scenario

An agent wants to call an MCP tool `customers.lookup`.

The underlying tool can return a rich customer record containing fields that
must **not** all be exposed to the model. The application therefore needs to:

1. authenticate/authorize the HTTP request;
2. decide whether this principal may perform the lookup;
3. execute the tool;
4. retain the raw result for controlled downstream use;
5. expose only an approved subset/summary to the model;
6. make the operation observable and auditable.

This is deliberately the scenario in which Weaver's `Frame` invariant appears
most likely to add value.

## Step 1 — tool identity and schemas

MCP already defines the tool identity and executable interface:

```json
{
  "name": "customers.lookup",
  "title": "Customer lookup",
  "description": "Lookup a customer record by customer ID.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": {"type": "string"}
    },
    "required": ["customer_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "segment": {"type": "string"},
      "email": {"type": "string"},
      "account_balance": {"type": "number"}
    }
  }
}
```

### Weaver concepts displaced

A separate generic `Capability` adds little here:

- identity/name/description → MCP Tool;
- input/output schema → MCP Tool JSON Schemas;
- implementation metadata → MCP `_meta` / annotations / application metadata;
- version → deployment/catalog concern.

**Experiment result:** no distinct portable `Capability` artifact is required
for this path. An adapter can refer directly to the MCP tool identity.

## Step 2 — transport authentication and access token

For HTTP transports, MCP's authorization specification uses established OAuth
mechanisms and resource/audience binding.

The access token remains an OAuth/MCP concern. The application does **not** mint
or pass a second Weaver bearer credential.

### Weaver concepts displaced

`CapabilityToken` should not be required as a second transport credential.

If a later domain artifact needs to reference the authorization basis, it can
reference an external credential/grant/decision identifier without re-defining
OAuth token semantics.

**Experiment result:** a universal Weaver authorization token is unnecessary in
this path.

## Step 3 — application policy decision

The application asks an existing policy engine whether the authenticated
principal may invoke `customers.lookup` with the requested context.

OPA is only the concrete example here; the experiment does not require OPA. Its
decision logs already demonstrate common policy/audit fields such as:

- decision ID;
- input;
- result;
- policy/bundle revision;
- requester;
- timestamp;
- W3C trace/span correlation;
- masking/erasure metadata.

Illustrative native decision projection:

```json
{
  "decision_id": "decision-123",
  "path": "agent/tools/customers_lookup/allow",
  "input": {
    "principal": "user:42",
    "tool": "customers.lookup",
    "customer_id": "C-1001"
  },
  "result": true,
  "timestamp": "2026-08-11T05:00:00Z"
}
```

### What remains potentially useful

The native decision log is richer than Weaver `PolicyDecision`, but it is
engine-specific. A *minimal cross-engine projection* could still be valuable if
unrelated runtimes really need to exchange:

- decision/correlation reference;
- principal/subject reference;
- action/resource reference;
- allow/deny result;
- policy/reason/provenance reference;
- timestamp.

That is a possible portability seam, but this experiment alone does not prove
that another standard is required.

**Experiment result:** policy evaluation and native decision logs must stay out
of scope. Only a small cross-engine decision projection remains a hypothesis.

## Step 4 — execute and record telemetry

The application executes the MCP tool and records an OpenTelemetry GenAI
`execute_tool` operation.

OpenTelemetry already has semantics for tool name, tool-call ID, arguments,
result, agent/workflow operations, and normal trace/span correlation.

### Weaver concepts displaced

Most `TraceEvent` lifecycle facts can be represented as ordinary spans/events
or attributes:

- tool/capability executed;
- call correlation;
- timing;
- success/failure;
- arguments/result where policy allows collection;
- agent/workflow context.

Policy engines such as OPA can also include W3C trace/span IDs in decision logs,
so correlation does not require a parallel Weaver trace hierarchy.

**Experiment result:** generic lifecycle telemetry belongs in OpenTelemetry, not
in a second universal trace vocabulary.

## Step 5 — preserve raw result out of band

Assume the raw tool result is:

```json
{
  "name": "Ada Example",
  "segment": "gold",
  "email": "ada@example.invalid",
  "account_balance": 1234.56
}
```

The application stores this raw result behind access control rather than placing
it in model context.

Existing portable reference mechanisms already cover most `Handle` fields:

- MCP `ResourceLink`: URI, name/title, description, MIME type, size, metadata;
- A2A `Artifact`: artifact ID, parts including URL/raw/data/text, media type,
  metadata, extension URIs;
- ordinary HTTPS/object-store URIs plus external authorization.

Illustrative MCP resource link:

```json
{
  "type": "resource_link",
  "name": "raw-customer-record",
  "uri": "https://artifacts.example.invalid/customer-lookups/run-123/raw",
  "mimeType": "application/json",
  "size": 128,
  "_meta": {
    "access_policy_ref": "policy://customer-raw-result/read"
  }
}
```

### What remains potentially useful

The distinctive statement is not the URI/size/MIME metadata. It is:

> this reference identifies the **protected raw counterpart** of a different,
> model-visible bounded result, and resolving it is outside the model exposure
> boundary.

**Experiment result:** prefer existing resource/artifact references. Only the
relationship to a bounded model-safe projection may need new semantics.

## Step 6 — expose a bounded result to the model

The application deliberately exposes only:

```json
{
  "summary": "Customer Ada Example is in the gold segment.",
  "structured_data": {
    "name": "Ada Example",
    "segment": "gold"
  },
  "redaction_notes": "Email and account balance withheld from model context."
}
```

MCP can technically carry this in `content` / `structuredContent`, and
OpenTelemetry can observe the call/result. But **neither representation, by
itself, asserts the trust-boundary semantic** that:

1. raw output exists separately;
2. the model-visible content is a deliberately filtered/approved projection;
3. the protected raw reference is correlated with that projection;
4. an authorization/redaction policy produced the projection;
5. downstream consumers must not substitute the raw artifact for the approved
   projection merely because both are reachable.

This is the strongest residual semantic found in the experiment.

## Residual-gap matrix

| Need | Existing owner | New contract needed? |
| --- | --- | --- |
| Tool identity/description/input/output schema | MCP / OpenAPI / native catalog | **No** |
| Agent skill discovery | A2A | **No** |
| HTTP authentication/access token | OAuth/MCP | **No** |
| Policy evaluation | OPA/Cedar/OpenFGA/native policy system | **No** |
| Native policy decision log | Policy engine | **No** |
| Tool execution telemetry | OpenTelemetry GenAI | **No** |
| Trace/span correlation | W3C Trace Context / OpenTelemetry | **No** |
| Raw artifact URI/MIME/size | MCP ResourceLink / A2A Artifact / URI | **No** |
| Generic signed JSON envelope | JOSE/JWS or deployment security | **No** |
| Minimal cross-engine policy-decision projection | No clear single owner | **Maybe — external evidence required** |
| Explicit model-safe projection distinct from raw result | No clear single portable semantic found | **Maybe — strongest candidate** |
| Link: bounded projection ↔ protected raw artifact ↔ policy decision | No clear single portable semantic found | **Maybe — strongest candidate** |

## What this experiment falsifies

The following broad standardization claims are **not supported** by this
scenario:

- Weaver needs its own generic tool/capability format.
- Weaver needs its own access token format.
- Weaver needs its own generic trace-event lifecycle.
- Weaver needs its own generic artifact-reference object.
- Weaver needs its own signing envelope merely to make the above portable.

Existing standards cover those jobs well enough for this scenario.

## What survives as a hypothesis

A much smaller candidate remains:

> a portable assurance relationship saying **which action decision applied, what
> bounded result is approved for model exposure, and where the protected raw
> counterpart lives**, without redefining transport, authentication, policy
> evaluation, telemetry, or storage.

Do **not** turn this sentence into a stable schema yet. The next gate is external
problem validation under #210.

## Implications for current contracts

- `Capability` → mapping/profile rather than universal required artifact.
- `CapabilityToken` → demote from generic Core unless a different non-credential
  semantic is externally justified.
- `TraceEvent` → map to OpenTelemetry; upstream missing assurance semantics where
  appropriate.
- `Handle` → prefer MCP/A2A/resource references; keep only relationship semantics
  if proven necessary.
- `PolicyDecision` → possible tiny decision projection, not policy-engine schema.
- `Frame` → possible tiny bounded-result profile; its **invariant** matters more
  than its current field names.

## Exit criteria

This experiment is complete when:

- [x] existing standards can represent tool identity, auth, policy evaluation,
  telemetry, and raw artifact references without Weaver-specific objects;
- [x] the residual semantic gap is stated explicitly rather than assumed;
- [ ] at least three independent projects are asked whether that residual gap is
  real in their systems (#210);
- [ ] at least two external projects are willing to test a common representation
  before any stable profile is defined.
