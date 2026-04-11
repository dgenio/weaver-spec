# JSON Schemas

This directory contains JSON Schema definitions for all Core Weaver contracts.

## Schema List

| Schema | Description |
| -------- | ------------- |
| `selectable_item.schema.json` | A single option in a ChoiceCard |
| `choice_card.schema.json` | A bounded set of SelectableItems for LLM selection |
| `routing_decision.schema.json` | Output of contextweaver routing phase |
| `capability.schema.json` | A registered executable capability in agent-kernel |
| `capability_token.schema.json` | Scoped authorization credential for capability invocation |
| `policy_decision.schema.json` | Authorization verdict from the policy engine |
| `frame.schema.json` | Safe, filtered view of a tool execution result |
| `handle.schema.json` | Opaque reference to a raw artifact in the HandleStore |
| `trace_event.schema.json` | Immutable audit log entry |

## Usage

Validate a payload against a schema using any JSON Schema Draft 2020-12 compatible library.

**Python (jsonschema):**

```python
import json
import jsonschema

schema = json.load(open("frame.schema.json"))
payload = json.load(open("../../examples/sample_payloads/frame_with_handles.json"))
jsonschema.validate(payload, schema)
```

**Node.js (ajv):**

```js
const Ajv = require("ajv/dist/2020");
const ajv = new Ajv();
const schema = require("./frame.schema.json");
const validate = ajv.compile(schema);
const valid = validate(payload);
```

## Schema Design Principles

- All schemas use `$schema: https://json-schema.org/draft/2020-12/schema`.
- All schemas have `$id`, `title`, and `description`.
- `required` fields are minimal — only truly required fields are listed.
- `additionalProperties: true` allows extensions without breaking validation.
- Cross-schema references use the full `$id` URI.

## Versioning

Schema `$id` URIs include a version prefix (`/v0/`, `/v1/`, etc.) corresponding to the MAJOR contract version. Old schemas are preserved when the major version increments.

See [../../docs/VERSIONING.md](../../docs/VERSIONING.md) for the full versioning policy.
