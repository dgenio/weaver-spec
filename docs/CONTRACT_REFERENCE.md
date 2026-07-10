# Contract Field Reference

A single-page field reference for every Weaver contract type — both Core (9) and Extended (24).

For narrative and adoption guidance, read [ARCHITECTURE.md](ARCHITECTURE.md), [BOUNDARIES.md](BOUNDARIES.md), and [GLOSSARY.md](GLOSSARY.md). For a runnable code path, use [QUICKSTART.md](QUICKSTART.md).

---

## Source of truth and authority

- **Core types** — the JSON Schemas in [`contracts/json/`](../contracts/json/) are the language-agnostic source of truth. The Python dataclasses in [`contracts/python/src/weaver_contracts/core.py`](../contracts/python/src/weaver_contracts/core.py) mirror them exactly.
- **Extended types** — schema-led, the same as Core: the JSON Schemas in [`contracts/json/extended/`](../contracts/json/extended/) are the source of truth and the Python dataclasses in [`contracts/python/src/weaver_contracts/extended.py`](../contracts/python/src/weaver_contracts/extended.py) mirror them exactly. Unlike Core, Extended contracts may have breaking changes in MINOR versions (see [VERSIONING.md](VERSIONING.md)). Dataclass ⟷ schema parity is enforced mechanically by `test_schema_parity.py`.

If this document ever disagrees with a schema or dataclass, the schema or dataclass wins. Open an issue.

---

## Conventions

- **Required** means listed in the JSON Schema's `required` array (Core) or has no default in the Python dataclass (Extended).
- **Type** uses JSON Schema vocabulary for Core (`string`, `object`, `array<X>`, `string | null`, `enum{…}`, `date-time` for ISO 8601) and Python typing vocabulary for Extended (`str`, `Optional[X]`, `List[X]`, `Dict[str, str]`).
- Required ID fields (e.g., `SelectableItem.id`, `ChoiceCard.id`, `RoutingDecision.id`, `Capability.id`, `CapabilityToken.token_id`, `PolicyDecision.decision_id`, `Frame.frame_id`, `Handle.handle_id`, `TraceEvent.event_id`) carry `minLength: 1`. Optional ID-like fields (e.g., `SelectableItem.capability_id`, `RoutingDecision.selected_item_id`, `TraceEvent.capability_id`) are plain `string` or `string | null` without `minLength`. IDs are not required to be UUIDs; slug-style identifiers are common in sample payloads.
- All Core schemas set `additionalProperties: true`, so adopters may add namespaced fields (e.g., `x_myorg_*`) without breaking validation.

---

## Core types (9)

### SelectableItem

**Purpose:** A single option presented to the LLM within a `ChoiceCard`.

**Source of truth:** [`contracts/json/selectable_item.schema.json`](../contracts/json/selectable_item.schema.json) · [`core.py` SelectableItem](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` (minLength 1) | Yes | Unique identifier within its `ChoiceCard`. |
| `label` | `string` (minLength 1) | Yes | Short human-readable label. Safe to include in an LLM prompt. |
| `description` | `string` (minLength 1) | Yes | Concise description. Must not include raw tool-schema details (see I-03). |
| `capability_id` | `string` | No | Reference to the `Capability` this item maps to (used by agent-kernel). |
| `metadata` | `object` | No | Implementation-specific metadata. `additionalProperties: true`. |

### ChoiceCard

**Purpose:** A curated, bounded menu of `SelectableItem` objects presented to the LLM.

**Source of truth:** [`contracts/json/choice_card.schema.json`](../contracts/json/choice_card.schema.json) · [`core.py` ChoiceCard](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` (minLength 1) | Yes | Unique identifier for this `ChoiceCard`. |
| `items` | `array<SelectableItem>` (minItems 1, maxItems 20) | Yes | Ordered options. 3–7 is the practical range for LLM selection. |
| `context_hint` | `string` | No | Optional guidance for the LLM about how to interpret this card. |
| `metadata` | `object` | No | Implementation-specific metadata. |

### RoutingDecision

**Purpose:** The output of the contextweaver routing phase. Wraps one or more `ChoiceCard` objects with selection state and a timestamp.

**Source of truth:** [`contracts/json/routing_decision.schema.json`](../contracts/json/routing_decision.schema.json) · [`core.py` RoutingDecision](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` (minLength 1) | Yes | Unique identifier for this routing decision. |
| `choice_cards` | `array<ChoiceCard>` (minItems 1) | Yes | One or more cards presented during this cycle. |
| `timestamp` | `string` (date-time) | Yes | ISO 8601 creation time. |
| `selected_item_id` | `string \| null` | No | Item the LLM chose; null while awaiting response. |
| `selected_card_id` | `string \| null` | No | Card containing the selected item. |
| `context_summary` | `string` | No | Brief diagnostic summary for audit. |
| `metadata` | `object` | No | Implementation-specific metadata. |

### Capability

**Purpose:** A named, versioned unit of executable functionality registered in agent-kernel.

**Source of truth:** [`contracts/json/capability.schema.json`](../contracts/json/capability.schema.json) · [`core.py` Capability](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` (minLength 1) | Yes | Stable, namespaced identifier (e.g., `org.myapp.search_docs`). |
| `name` | `string` (minLength 1) | Yes | Human-readable name. |
| `version` | `string` (minLength 1) | Yes | Semantic version of this capability. |
| `description` | `string` (minLength 1) | Yes | What the capability does and when to use it. |
| `input_schema_ref` | `string` | No | URI to the JSON Schema describing valid inputs. |
| `output_schema_ref` | `string` | No | URI to the JSON Schema describing the `Frame` content. |
| `tags` | `array<string>` | No | Optional tags for categorization. |
| `metadata` | `object` | No | Implementation-specific metadata. |

### CapabilityToken

**Purpose:** A scoped authorization credential for capability invocation. Issued by agent-kernel.

**Source of truth:** [`contracts/json/capability_token.schema.json`](../contracts/json/capability_token.schema.json) · [`core.py` CapabilityToken](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `token_id` | `string` (minLength 1) | Yes | Unique identifier for this token. |
| `principal` | `string` (minLength 1) | Yes | Identity (user, agent, or service) this token was issued to. |
| `scope` | `array<string>` (minItems 1) | Yes | Capability IDs this token authorizes. Unbounded scope is not permitted (I-06). |
| `issued_at` | `string` (date-time) | Yes | ISO 8601 issuance timestamp. |
| `expires_at` | `string \| null` (date-time) | Conditional | Required unless `single_use=true`. Enforced by an `anyOf` constraint in the schema and by `__post_init__` in Python. |
| `single_use` | `boolean` (default `false`) | No | When `true`, the token is invalidated after one successful authorization. |
| `issuer` | `string` | No | Optional identifier of the issuing agent-kernel instance. |
| `metadata` | `object` | No | Implementation-specific metadata. |

The token must either be single-use **or** carry an expiry. This is invariant I-06 and is enforced structurally by the `anyOf` clause in the schema and at construction time in Python. The word "signed" used in the Glossary is aspirational — the current contract does not encode cryptographic verification.

### PolicyDecision

**Purpose:** The authorization verdict produced by agent-kernel's policy engine.

**Source of truth:** [`contracts/json/policy_decision.schema.json`](../contracts/json/policy_decision.schema.json) · [`core.py` PolicyDecision](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `decision_id` | `string` (minLength 1) | Yes | Used to correlate with `TraceEvent` entries. |
| `decision` | `enum{"allow","deny"}` | Yes | The verdict. |
| `capability_id` | `string` (minLength 1) | Yes | The capability evaluated. |
| `principal` | `string` (minLength 1) | Yes | Principal whose authorization was evaluated. |
| `timestamp` | `string` (date-time) | Yes | ISO 8601 decision time. |
| `token_id` | `string \| null` | No | `CapabilityToken` ID used, if any. |
| `reason` | `string` | No | Human-readable explanation. Recommended for `deny`. |
| `metadata` | `object` | No | Implementation-specific metadata. |

### Frame

**Purpose:** Safe, filtered view of a tool execution result. Produced by the agent-kernel firewall.

**Source of truth:** [`contracts/json/frame.schema.json`](../contracts/json/frame.schema.json) · [`core.py` Frame](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `frame_id` | `string` (minLength 1) | Yes | Unique identifier for this `Frame`. |
| `capability_id` | `string` (minLength 1) | Yes | Capability that produced this `Frame`. |
| `summary` | `string` (minLength 1) | Yes | LLM-safe summary. Never contains raw output (I-01, I-05). |
| `created_at` | `string` (date-time) | Yes | ISO 8601 creation timestamp. |
| `structured_data` | `object \| null` | No | Firewall-filtered structured subset approved for LLM consumption. |
| `handle_refs` | `array<string>` (each minLength 1) | No | `Handle` IDs referencing raw artifacts. Resolution requires authorization. |
| `redaction_notes` | `string` | No | Description of what was redacted or filtered. |
| `metadata` | `object` | No | Implementation-specific metadata. |

### Handle

**Purpose:** Opaque, access-controlled reference to a raw artifact. The artifact lives in the HandleStore; the `Handle` carries only the reference plus access metadata.

**Source of truth:** [`contracts/json/handle.schema.json`](../contracts/json/handle.schema.json) · [`core.py` Handle](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `handle_id` | `string` (minLength 1) | Yes | Reference identifier. Must not be sufficient for unauthorized access. |
| `capability_id` | `string` (minLength 1) | Yes | Capability that produced the referenced artifact. |
| `artifact_type` | `string` (minLength 1) | Yes | MIME or semantic type (e.g., `application/json`, `image/png`). |
| `created_at` | `string` (date-time) | Yes | ISO 8601 creation timestamp. |
| `expires_at` | `string \| null` (date-time) | No | Optional artifact expiry. |
| `access_policy` | `string` | No | Reference to the policy governing who can resolve this `Handle`. |
| `byte_size` | `integer \| null` (minimum 0) | No | Optional artifact size for capacity planning. |
| `metadata` | `object` | No | Implementation-specific metadata. |

### TraceEvent

**Purpose:** Immutable audit log entry for a single significant lifecycle event. Append-only.

**Source of truth:** [`contracts/json/trace_event.schema.json`](../contracts/json/trace_event.schema.json) · [`core.py` TraceEvent](../contracts/python/src/weaver_contracts/core.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `event_id` | `string` (minLength 1) | Yes | Unique event identifier. |
| `event_type` | `enum{…}` | Yes | One of the values listed below. |
| `timestamp` | `string` (date-time) | Yes | ISO 8601 event time. |
| `capability_id` | `string \| null` | No | Capability involved, if applicable. |
| `principal` | `string \| null` | No | Principal involved, if applicable. |
| `decision_id` | `string \| null` | No | Associated `PolicyDecision`, if applicable. |
| `frame_id` | `string \| null` | No | Associated `Frame`, if applicable. |
| `handle_id` | `string \| null` | No | Associated `Handle`, if applicable. |
| `outcome` | `enum{"success","failure","partial"}` | No | High-level outcome. |
| `error_message` | `string \| null` | No | Error message for failure events. |
| `metadata` | `object` | No | Implementation-specific metadata. |

**Allowed `event_type` values:** `capability_authorized`, `capability_denied`, `capability_executed`, `firewall_applied`, `handle_created`, `handle_resolved`, `token_issued`, `token_invalidated`, `flow_started`, `flow_step_started`, `flow_step_completed`, `flow_completed`, `flow_failed`. Adding a new value requires a spec update (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

---

## Extended types (23)

Extended types are optional. None is required for spec compliance. Each has a JSON Schema in [`contracts/json/extended/`](../contracts/json/extended/) (the source of truth) mirrored by a dataclass in [`contracts/python/src/weaver_contracts/extended.py`](../contracts/python/src/weaver_contracts/extended.py). Per [VERSIONING.md](VERSIONING.md), Extended contracts may have breaking changes in MINOR versions.

Adopters typically attach Extended objects to their own payloads via the `metadata` field of a Core contract (Core schemas set `additionalProperties: true`), or by composing them into Extended wrappers like `ExtendedFrameMetadata`.

### TelemetryHint

**Purpose:** Observability metadata attachable to any event or contract.

**Source of truth:** [`extended.py` TelemetryHint](../contracts/python/src/weaver_contracts/extended.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `trace_id` | `Optional[str]` (default `None`) | No | Distributed-trace identifier. |
| `span_id` | `Optional[str]` (default `None`) | No | Span identifier within the trace. |
| `baggage` | `Dict[str, str]` (default `{}`) | No | Free-form trace baggage. |

**Relationship to Core:** Carried as metadata alongside any Core contract — most commonly on `Frame` or `TraceEvent` payloads.

**Example:**

```json
{
  "trace_id": "trace-20260308-001",
  "span_id": "span-20260308-001",
  "baggage": {"tenant": "acme", "request_id": "req-20260308-001"}
}
```

### SchemaFingerprint

**Purpose:** Records the schema version and content hash for a contract payload, supporting schema evolution and drift detection.

**Source of truth:** [`extended.py` SchemaFingerprint](../contracts/python/src/weaver_contracts/extended.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_id` | `str` (non-empty) | Yes | The schema's `$id` (or another stable identifier). |
| `schema_version` | `str` (non-empty) | Yes | Version of the schema referenced. |
| `content_hash` | `Optional[str]` (default `None`) | No | Hex digest of the payload (length depends on `hash_algorithm`). |
| `hash_algorithm` | `str` (default `"sha256"`) | No | Hash algorithm; default produces a 64-character hex digest. |

**Relationship to Core:** Pairs with any Core payload to declare "this object validates against schema X version Y". Useful when receiver and sender may have different schema generations.

**Example:**

```json
{
  "schema_id": "https://weaver-spec.dev/contracts/v0/frame.schema.json",
  "schema_version": "0.2.0",
  "content_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "hash_algorithm": "sha256"
}
```

### RedactionPolicy

**Purpose:** Describes the redaction rules applied by the firewall when producing a `Frame`.

**Source of truth:** [`extended.py` RedactionPolicy](../contracts/python/src/weaver_contracts/extended.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `policy_id` | `str` (non-empty) | Yes | Identifier of the policy applied. |
| `redacted_fields` | `List[str]` (default `[]`) | No | Field paths that were redacted. |
| `truncated_fields` | `List[str]` (default `[]`) | No | Field paths that were truncated. |
| `redaction_reason` | `Optional[str]` (default `None`) | No | Human-readable reason. |
| `pii_detected` | `bool` (default `False`) | No | Whether PII was found in raw output. |
| `pii_types` | `List[str]` (default `[]`) | No | Categories of PII detected. |

**Relationship to Core:** Documents the firewall transformation that produced a `Frame`. Composed into `ExtendedFrameMetadata.redaction_policy`.

**Example:**

```json
{
  "policy_id": "policy-default-2026Q1",
  "redacted_fields": ["headers.authorization"],
  "truncated_fields": ["body.text"],
  "redaction_reason": "Detected secret in upstream response.",
  "pii_detected": true,
  "pii_types": ["email"]
}
```

### UIHint

**Purpose:** Display guidance for UI layers that render `ChoiceCard` items.

**Source of truth:** [`extended.py` UIHint](../contracts/python/src/weaver_contracts/extended.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `icon` | `Optional[str]` (default `None`) | No | Icon identifier or URI. |
| `color` | `Optional[str]` (default `None`) | No | Display color (CSS, theme token, etc.). |
| `priority` | `Optional[int]` (default `None`) | No | Display priority. |
| `group` | `Optional[str]` (default `None`) | No | Logical grouping label. |
| `disabled` | `bool` (default `False`) | No | Whether the item should be rendered as disabled. |
| `tooltip` | `Optional[str]` (default `None`) | No | Hover tooltip text. |

**Relationship to Core:** Pairs with a `SelectableItem` or `ChoiceCard` for clients that render the menu. Composed into `ExtendedSelectableItemMetadata.ui_hint`.

**Example:**

```json
{
  "icon": "search",
  "color": "#1f6feb",
  "priority": 1,
  "group": "retrieval",
  "tooltip": "Full-text search across docs."
}
```

### RiskAssessment

**Purpose:** Optional risk metadata for a capability invocation.

**Source of truth:** [`extended.py` RiskAssessment](../contracts/python/src/weaver_contracts/extended.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `risk_level` | `enum{"low","medium","high","critical"}` (default `"low"`) | No | Risk classification. Validated in `__post_init__`. |
| `risk_reasons` | `List[str]` (default `[]`) | No | Free-form rationale entries. |
| `requires_human_approval` | `bool` (default `False`) | No | Whether the invocation requires a human approver. |
| `approval_principal` | `Optional[str]` (default `None`) | No | Identity required to approve. |
| `mitigations` | `List[str]` (default `[]`) | No | Mitigations already applied. |

**Relationship to Core:** Pairs with a `RoutingDecision`, `PolicyDecision`, or `SelectableItem` to convey risk. Composed into `ExtendedSelectableItemMetadata.risk_assessment`.

**Example:**

```json
{
  "risk_level": "high",
  "risk_reasons": ["destructive_action"],
  "requires_human_approval": true,
  "approval_principal": "user:operator-on-call",
  "mitigations": ["dry_run_preview"]
}
```

### ExtendedFrameMetadata

**Purpose:** Wrapper that bundles common Extended metadata for a `Frame`.

**Source of truth:** [`extended.py` ExtendedFrameMetadata](../contracts/python/src/weaver_contracts/extended.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `redaction_policy` | `Optional[RedactionPolicy]` (default `None`) | No | Policy applied by the firewall. |
| `telemetry` | `Optional[TelemetryHint]` (default `None`) | No | Observability metadata. |
| `schema_fingerprint` | `Optional[SchemaFingerprint]` (default `None`) | No | Schema version and content hash. |
| `confidence_score` | `Optional[float]` (default `None`) | No | Optional confidence value attached by the firewall. |
| `source_capability_version` | `Optional[str]` (default `None`) | No | Version of the capability that produced the underlying artifact. |
| `extra` | `Dict[str, Any]` (default `{}`) | No | Free-form additional metadata. |

**Relationship to Core:** Attach to a `Frame` (typically inside `Frame.metadata`) to enrich it without modifying the Core schema.

**Example:**

```json
{
  "redaction_policy": {
    "policy_id": "policy-default-2026Q1",
    "redacted_fields": ["headers.authorization"]
  },
  "telemetry": {"trace_id": "trace-20260308-001"},
  "confidence_score": 0.93,
  "source_capability_version": "1.4.0"
}
```

### ExtendedSelectableItemMetadata

**Purpose:** Wrapper that bundles UI and risk metadata for a `SelectableItem`.

**Source of truth:** [`extended.py` ExtendedSelectableItemMetadata](../contracts/python/src/weaver_contracts/extended.py)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `ui_hint` | `Optional[UIHint]` (default `None`) | No | Display metadata. |
| `risk_assessment` | `Optional[RiskAssessment]` (default `None`) | No | Risk metadata. |
| `estimated_duration_ms` | `Optional[int]` (default `None`) | No | Estimated time to complete the action. |
| `requires_confirmation` | `bool` (default `False`) | No | Whether the UI should require a confirmation step. |
| `extra` | `Dict[str, Any]` (default `{}`) | No | Free-form additional metadata. |

**Relationship to Core:** Attach to a `SelectableItem` (typically inside `SelectableItem.metadata`) to provide UI and risk hints without modifying the Core schema.

**Example:**

```json
{
  "ui_hint": {"icon": "delete", "color": "#cf222e"},
  "risk_assessment": {"risk_level": "high", "requires_human_approval": true},
  "estimated_duration_ms": 800,
  "requires_confirmation": true
}
```

---

## Updating this reference

This file mirrors the JSON Schemas in [`contracts/json/`](../contracts/json/) and the Python dataclasses in [`extended.py`](../contracts/python/src/weaver_contracts/extended.py). When either source changes, update the corresponding row(s) in the same PR. Treat the schema or dataclass as authoritative; this document is derived.
