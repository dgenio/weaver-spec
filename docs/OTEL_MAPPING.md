# TraceEvent → OpenTelemetry GenAI semantic conventions mapping

> [!IMPORTANT]
> This document is the normative mapping from Weaver `TraceEvent` fields onto
> [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/).
> Sibling repos that emit OTel spans MUST follow this mapping so telemetry
> remains interoperable across vendors (Datadog, Honeycomb, New Relic, and
> any other backend that consumes OTel GenAI semconv). Tracked in issue #47.

The Extended contract `OtelTraceMapping`
(`contracts/json/extended/otel_trace_mapping.schema.json`,
`weaver_contracts.extended.OtelTraceMapping`) carries the OTel identifiers
and GenAI attributes for a single TraceEvent. Producers attach an
`OtelTraceMapping` to each `TraceEvent` they emit (under their own metadata
extension key, since `TraceEvent.metadata` is `additionalProperties: true`).

---

## Pinned semconv snapshot

| Field | Value |
| ----- | ----- |
| `semconv_version` | `1.30.0` |
| Snapshot URL | <https://opentelemetry.io/docs/specs/semconv/gen-ai/> |
| Anchor pages | [GenAI spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/), [Agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/) |

Producers SHOULD set `OtelTraceMapping.semconv_version` to the snapshot they
mapped against; verifiers can use the value to detect drift.

---

## Field-by-field mapping

The table below lists every `TraceEvent` field and the OTel attribute or span
shape it maps onto. "No mapping" means the Weaver-only field carries
information OTel GenAI semconv does not currently define an attribute for —
attach it under `gen_ai.weaver.*` or leave it out.

| TraceEvent field | OTel attribute / span shape | Notes |
| ---------------- | --------------------------- | ----- |
| `event_id` | `gen_ai.weaver.event_id` (custom) | OTel has no first-class event identifier separate from span ID; expose for cross-linking back to Weaver traces. |
| `event_type` | `gen_ai.operation.name` (mapped via §"Event type → operation name") | See translation table below. |
| `timestamp` | Span `start_time` (and `end_time` for completion events) | RFC 3339 / ISO 8601 input, OTel uses Unix nanos internally. |
| `capability_id` | `gen_ai.tool.name` | Direct mapping; Weaver `capability_id` *is* the tool name. |
| `principal` | `gen_ai.agent.id` | Weaver principal identifies the agent or service invoking the capability. |
| `decision_id` | `gen_ai.weaver.policy_decision_id` (custom) | No OTel semconv attribute for policy/authz decisions yet. |
| `frame_id` | `gen_ai.weaver.frame_id` (custom) | Frame is a Weaver concept. |
| `handle_id` | `gen_ai.weaver.handle_id` (custom) | Handle is a Weaver concept. |
| `outcome` | `error.type` (when `failure`) + span `status_code` (`OK` / `ERROR`) | OTel span status replaces an explicit success/failure attribute. |
| `error_message` | `exception.message` (when present) | Recorded as a span event per [OTel exceptions semconv](https://opentelemetry.io/docs/specs/semconv/exceptions/). |
| `metadata` | passthrough | Implementation-specific. Namespace any custom keys under `gen_ai.weaver.*` or your own producer namespace. |

---

## Event type → `gen_ai.operation.name`

| Weaver `event_type` | `gen_ai.operation.name` | OTel `span_kind` |
| ------------------- | ----------------------- | ---------------- |
| `capability_authorized` | `agent.invoke_agent` | `INTERNAL` |
| `capability_denied` | `agent.invoke_agent` | `INTERNAL` (span status = `ERROR`, `error.type = "policy_denied"`) |
| `capability_executed` | `execute_tool` | `INTERNAL` (or `CLIENT` if the capability calls out of process) |
| `firewall_applied` | `agent.invoke_agent` | `INTERNAL` |
| `handle_created` | `agent.invoke_agent` | `INTERNAL` |
| `handle_resolved` | `agent.invoke_agent` | `INTERNAL` |
| `token_issued` | `agent.invoke_agent` | `INTERNAL` |
| `token_invalidated` | `agent.invoke_agent` | `INTERNAL` |
| `flow_started` | `agent.invoke_agent` | `INTERNAL` |
| `flow_step_started` | `execute_tool` | `INTERNAL` |
| `flow_step_completed` | `execute_tool` | `INTERNAL` |
| `flow_completed` | `agent.invoke_agent` | `INTERNAL` |
| `flow_failed` | `agent.invoke_agent` | `INTERNAL` (span status = `ERROR`) |

OTel GenAI semconv reserves `agent.invoke_agent` for agent-control events and
`execute_tool` for the actual tool invocation; the table above keeps that
separation.

---

## OtelTraceMapping field reference

| Field | Source / formula | Example |
| ----- | ---------------- | ------- |
| `trace_id` | W3C Trace Context `trace-id` (32 lowercase hex chars). Producers SHOULD propagate from the inbound `traceparent` header. | `4bf92f3577b34da6a3ce929d0e0e4736` |
| `span_id` | W3C Trace Context `span-id` (16 lowercase hex chars), unique per span. | `00f067aa0ba902b7` |
| `span_kind` | Per the table above. | `INTERNAL` |
| `gen_ai_operation_name` | Per the event-type table above. | `execute_tool` |
| `gen_ai_agent_id` | `TraceEvent.principal` | `agent-kernel-prod-1` |
| `gen_ai_agent_name` | Stable display name of the agent. | `agent-kernel` |
| `gen_ai_tool_name` | `TraceEvent.capability_id` | `org.myapp.search_docs` |
| `gen_ai_system` | Producer-defined; `weaver` for native Weaver events. | `weaver` |
| `parent_span_id` | The OTel span ID of the parent operation, if any (16 lowercase hex chars). | `b9c7c989f97918e1` |
| `semconv_version` | Snapshot referenced above. | `1.30.0` |

---

## Inline example

<!-- schema: otel_trace_mapping -->
```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "span_kind": "INTERNAL",
  "gen_ai_operation_name": "execute_tool",
  "gen_ai_agent_id": "agent-kernel-prod-1",
  "gen_ai_agent_name": "agent-kernel",
  "gen_ai_tool_name": "org.myapp.search_docs",
  "gen_ai_system": "weaver",
  "parent_span_id": "b9c7c989f97918e1",
  "semconv_version": "1.30.0"
}
```

This example accompanies the
`capability_executed` TraceEvent fired when the `org.myapp.search_docs`
capability completes; the OTel collector receiving it would create one
`INTERNAL` span named `execute_tool` with `gen_ai.tool.name = org.myapp.search_docs`.

---

## Related

- Extended schema: `contracts/json/extended/otel_trace_mapping.schema.json`
- Extended dataclass: `weaver_contracts.extended.OtelTraceMapping`
- Sample payload: `examples/sample_payloads/otel_trace_mapping.json`
- Issue #47 — original proposal.
- OTel GenAI semconv index: <https://opentelemetry.io/docs/specs/semconv/gen-ai/>
- OTel Agent spans: <https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/>
