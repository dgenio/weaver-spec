# Glossary

Canonical definitions for all terms used in the Weaver spec. When these terms appear in code, schemas, or documentation, they carry the meaning defined here.

---

## SelectableItem

A single option that can be presented to an LLM for selection. Represents one possible action, tool, or capability in the context of a routing decision.

**Key fields:** `id` (unique within a ChoiceCard), `label` (human-readable), `description` (concise, safe to include in a prompt).

**Owned by:** contextweaver (produces); agent-kernel (consumes as authorization target).

---

## ChoiceCard

A curated, bounded set of `SelectableItem` objects presented to the LLM as a structured menu. The LLM selects from the ChoiceCard rather than from an unbounded tool list. A ChoiceCard typically contains 3–7 items.

**Key fields:** `id`, `items` (list of SelectableItem), `context_hint` (optional guidance for the LLM).

**Owned by:** contextweaver.

**Invariant:** A ChoiceCard must never include a SelectableItem that requires injecting the full tool schema into the prompt to make the selection.

---

## RoutingDecision

The output of the contextweaver routing phase. Contains one or more `ChoiceCard` objects and the selected item (if the LLM has already responded) or a pending state (if awaiting LLM response).

**Key fields:** `id`, `choice_cards` (list of ChoiceCard), `selected_item_id` (nullable), `timestamp`.

**Owned by:** contextweaver (produces); agent-kernel (consumes to determine what to execute).

---

## Capability

A named, versioned unit of executable functionality. Represents a tool, service call, or computation that can be invoked through agent-kernel. Capabilities have stable IDs and declared input/output schemas.

**Key fields:** `id`, `name`, `version`, `description`, `input_schema` (JSON Schema reference), `output_schema` (JSON Schema reference).

**Owned by:** agent-kernel (capability registry).

---

## CapabilityToken (Token)

A signed, scoped authorization credential that grants the bearer permission to invoke one or more specific capabilities. Issued by agent-kernel's authorization subsystem. Must have an explicit scope and expiry or single-use flag.

**Key fields:** `token_id`, `principal`, `scope` (list of capability IDs), `issued_at`, `expires_at`, `single_use`.

**Owned by:** agent-kernel (issues and validates).

**Invariant:** A CapabilityToken must not grant unbounded execution scope.

---

## PolicyDecision

The authorization verdict produced by agent-kernel's policy engine for a given capability invocation request. Contains the decision (allow/deny), the reason, and the capability and principal involved.

**Key fields:** `decision` (allow | deny), `capability_id`, `principal`, `reason`, `timestamp`.

**Owned by:** agent-kernel.

**Invariant:** Every tool execution must be preceded by a PolicyDecision. PolicyDecisions are always recorded in the audit log.

---

## Frame

A safe, filtered view of a tool execution result. Produced by the agent-kernel firewall after processing raw tool output. A Frame is what contextweaver and the LLM see. It contains a summary or structured representation of the result, never raw output.

**Key fields:** `frame_id`, `capability_id`, `summary`, `structured_data` (optional, safe subset), `redaction_notes` (optional), `handle_refs` (list of Handle IDs for full artifacts).

**Owned by:** agent-kernel (produces); contextweaver (consumes).

**Invariant:** A Frame never contains raw tool output. If raw output exists, it is stored as a Handle.

---

## Handle

An opaque, access-controlled reference to a raw artifact produced by a tool execution. The actual content is stored in the HandleStore and is not included in the Handle itself. A Handle can be resolved only by an authorized principal through agent-kernel.

**Key fields:** `handle_id`, `capability_id`, `artifact_type`, `created_at`, `expires_at`, `access_policy`.

**Owned by:** agent-kernel (produces and resolves); HandleStore (stores artifacts).

**Invariant:** A Handle ID must never be enough to access the underlying artifact without authorization.

---

## TraceEvent

An immutable audit log entry recording a single significant event in the execution lifecycle. Used for observability, debugging, and compliance.

**Key fields:** `event_id`, `event_type` (e.g., `capability_authorized`, `capability_executed`, `firewall_applied`), `capability_id`, `principal`, `timestamp`, `metadata`.

**Owned by:** agent-kernel (produces); audit log (stores).

**Invariant:** TraceEvents are append-only and must not be modified after creation.

---

## Artifact / HandleStore

The storage backend for raw tool output artifacts referenced by Handles. The HandleStore is an agent-kernel internal component; its implementation is not specified here. What is specified is the Handle contract that references artifacts stored within it.

**Key property:** Artifacts in the HandleStore are accessible only through Handle resolution, which requires authorization.
