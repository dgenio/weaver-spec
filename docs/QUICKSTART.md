# Quick-Start Integration Guide

A minimal, copy-paste path for getting productive with the Weaver contracts in Python or JavaScript/TypeScript.

For deeper background, read [ADOPTION_GUIDE.md](ADOPTION_GUIDE.md) (which adoption mode fits you) and [CONTRACT_REFERENCE.md](CONTRACT_REFERENCE.md) (full field reference). For boundary rules and invariants you must respect, see [BOUNDARIES.md](BOUNDARIES.md) and [INVARIANTS.md](INVARIANTS.md).

---

## What this guide covers

- Installing the language-agnostic JSON Schemas and the optional Python package.
- Constructing, serializing, deserializing, and validating Core contracts.
- Constructing an Extended (optional) contract for telemetry.
- One integration snippet per sibling repo (contextweaver, agent-kernel, ChainWeaver).

This guide does **not** add any runtime dependencies to your application beyond the JSON Schema validator of your choice (and, optionally, the `weaver_contracts` Python package).

---

## Prerequisites

- For the Python path: Python 3.10 or newer (tested on 3.10–3.14).
- For the JS/TS path: Node.js 18 or newer, with `ajv` for validation.
- A clone of this repository (for direct schema access) **or** the published JSON Schema files served at the `$id` URIs declared in each schema.

---

## Python

### Install

The Python package vendors the same field shapes as the JSON Schemas as stdlib `dataclasses`. Pick whichever install line works for your environment:

```bash
# From PyPI (preferred once the release is available):
pip install weaver_contracts

# From a local checkout (always works):
pip install -e ./contracts/python
```

Install the `dev` extras (`pytest`, `jsonschema`, `mypy`, `pytest-cov`) only if you intend to run the spec's own tests or do schema validation in development.

### Construct a Core contract

```python
from datetime import datetime, timezone

from weaver_contracts import (
    SelectableItem,
    ChoiceCard,
    RoutingDecision,
)

item = SelectableItem(
    id="search-docs",
    label="Search documentation",
    description="Full-text search across the product documentation index.",
    capability_id="org.myapp.search_docs",
)
card = ChoiceCard(
    id="card-retrieval",
    items=[item],
    context_hint="Select the most appropriate document retrieval action.",
)
decision = RoutingDecision(
    id="rd-20260308-001",
    choice_cards=[card],
    timestamp=datetime.now(timezone.utc),
    selected_item_id="search-docs",
    selected_card_id="card-retrieval",
)
```

Construction-time validation runs in each dataclass's `__post_init__`. For example, a `SelectableItem` with an empty `id` raises `ValueError` immediately.

### Serialize and deserialize

The Python types are plain dataclasses, so any JSON-friendly serializer works. The shortest stdlib path is `dataclasses.asdict` plus a small helper for `datetime`:

```python
import json
from dataclasses import asdict
from datetime import datetime

def _default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Not serializable: {type(value).__name__}")

payload = json.dumps(asdict(decision), default=_default)
```

To deserialize, parse the JSON and re-hydrate the dataclasses by hand (or use your preferred deserialization library — `pydantic`, `attrs`, `cattrs`, etc.). The `weaver_contracts` package deliberately does not ship a deserializer to keep its surface minimal.

### Validate a payload against a JSON Schema

The JSON Schemas in [`contracts/json/`](../contracts/json/) are the language-agnostic source of truth. Use any Draft 2020-12 validator.

`routing_decision.schema.json` `$ref`s `choice_card.schema.json`, which in turn `$ref`s `selectable_item.schema.json`. With a plain `jsonschema.validate(...)` call, those references would trigger remote URL resolution and fail offline. Pre-load every Core schema into a `referencing.Registry` so validation stays local — this is the same pattern the repository's CI uses (`Draft202012Validator` + `iter_errors`, with format checking enabled):

```python
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

registry = Registry()
for schema_path in Path("contracts/json").glob("*.schema.json"):
    schema = json.loads(schema_path.read_text())
    registry = registry.with_resource(
        uri=schema["$id"],
        resource=Resource(contents=schema, specification=DRAFT202012),
    )

schema = json.loads(Path("contracts/json/routing_decision.schema.json").read_text())
payload = json.loads(Path("examples/sample_payloads/routing_decision.json").read_text())

validator = Draft202012Validator(
    schema,
    registry=registry,
    format_checker=Draft202012Validator.FORMAT_CHECKER,
)
errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
if errors:
    raise SystemExit("\n".join(f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors))
```

The `format_checker` argument is what catches `date-time` violations on fields such as `timestamp`, `issued_at`, and `created_at`. CI enables the same Draft 2020-12 format checker — see [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (`validate-walkthroughs` job).

### Construct an Extended (optional) contract

Extended contracts are not required for spec compliance. They carry optional metadata such as telemetry and risk hints.

```python
from weaver_contracts.extended import TelemetryHint

telemetry = TelemetryHint(
    trace_id="trace-20260308-001",
    span_id="span-20260308-001",
    baggage={"tenant": "acme", "request_id": "req-20260308-001"},
)
```

Extended types can be attached to your own payloads via the contract's `metadata` field (`additionalProperties: true` on every Core schema makes this safe). See [CONTRACT_REFERENCE.md](CONTRACT_REFERENCE.md) for the full Extended catalog and per-type relationships.

### Check version compatibility

```python
from weaver_contracts.version import CONTRACT_VERSION, is_compatible

print(CONTRACT_VERSION)                # e.g. "0.2.0"
print(is_compatible("0.1.0"))          # True — same MAJOR
print(is_compatible("1.0.0"))          # False — different MAJOR
```

`is_compatible` enforces the contract promise documented in [VERSIONING.md](VERSIONING.md): two versions interoperate when they share the same MAJOR.

---

## JavaScript / TypeScript

### Validate with ajv

The repository's [`contracts/json/README.md`](../contracts/json/README.md) documents this pattern; it is reproduced here for completeness.

```js
// 1. Install: npm install ajv ajv-formats
const Ajv2020 = require("ajv/dist/2020");
const addFormats = require("ajv-formats");

const ajv = new Ajv2020({ strict: false });
addFormats(ajv);

// Load the Core schemas you need. choice_card refs selectable_item; routing_decision refs choice_card.
ajv.addSchema(require("./contracts/json/selectable_item.schema.json"));
ajv.addSchema(require("./contracts/json/choice_card.schema.json"));

const validate = ajv.compile(
  require("./contracts/json/routing_decision.schema.json"),
);

const payload = require("./examples/sample_payloads/routing_decision.json");
if (!validate(payload)) {
  console.error(validate.errors);
  process.exit(1);
}
```

`addFormats` is what enforces `date-time` and other format keywords. The `Ajv2020` import matches the Draft 2020-12 dialect declared by every schema's `$schema` field.

### Construct a contract-conformant object

```ts
// Authoring style — these object literals mirror the JSON Schema shapes.
// Required fields per selectable_item.schema.json: id, label, description.
const item = {
  id: "search-docs",
  label: "Search documentation",
  description: "Full-text search across the product documentation index.",
  capability_id: "org.myapp.search_docs",
};
```

### Type generation hint

If you want compile-time types in TypeScript without hand-writing interfaces, run a JSON-Schema-to-TypeScript codegen step against `contracts/json/*.schema.json`:

```bash
npx json-schema-to-typescript contracts/json/routing_decision.schema.json \
  --no-additionalProperties=false \
  > types/RoutingDecision.ts
```

The flag preserves the `additionalProperties: true` declared on every Core schema. See [contracts/json/README.md](../contracts/json/README.md) for schema design principles you may need to honor at the type level.

---

## Per-sibling-repo integration

Each sibling repo produces or consumes a specific subset of the contracts. The snippets below show the minimum each side needs.

### contextweaver — producing a RoutingDecision

contextweaver compiles bounded `ChoiceCard` lists and emits a `RoutingDecision`. It never executes a tool and never receives raw output (see [INVARIANTS.md](INVARIANTS.md) I-03 and I-05).

```python
from datetime import datetime, timezone

from weaver_contracts import (
    SelectableItem,
    ChoiceCard,
    RoutingDecision,
)

def build_routing_decision(candidates, intent) -> RoutingDecision:
    items = [
        SelectableItem(
            id=cap.short_id,
            label=cap.label,
            description=cap.short_description,
            capability_id=cap.id,
        )
        for cap in rank(candidates, intent)[:7]   # 3-7 is the practical range; choice_card.schema.json caps at maxItems: 20
    ]
    card = ChoiceCard(id=f"card-{intent.slug}", items=items)
    return RoutingDecision(
        id=f"rd-{intent.slug}",
        choice_cards=[card],
        timestamp=datetime.now(timezone.utc),
    )
```

### agent-kernel — consuming a RoutingDecision, producing Frame + Handle

agent-kernel validates the `CapabilityToken`, authorizes the capability (emits a `PolicyDecision`), executes the tool, and produces a `Frame` (LLM-safe) plus optional `Handle` (opaque reference to the raw artifact). Raw output never leaves the kernel.

```python
from datetime import datetime, timezone

from weaver_contracts import (
    RoutingDecision,
    CapabilityToken,
    PolicyDecision,
    Frame,
    Handle,
)

def execute(decision: RoutingDecision, token: CapabilityToken):
    capability_id = _resolve(decision)
    policy = PolicyDecision(
        decision_id=f"pd-{decision.id}",
        decision="allow",
        capability_id=capability_id,
        principal=token.principal,
        token_id=token.token_id,
        timestamp=datetime.now(timezone.utc),
    )
    raw = _invoke_tool(capability_id, _args(decision))   # internal to kernel
    handle = Handle(
        handle_id=f"h-{decision.id}",
        capability_id=capability_id,
        artifact_type="application/json",
        created_at=datetime.now(timezone.utc),
        byte_size=len(raw),
    )
    frame = Frame(
        frame_id=f"f-{decision.id}",
        capability_id=capability_id,
        summary=_safe_summary(raw),
        created_at=datetime.now(timezone.utc),
        handle_refs=[handle.handle_id],
    )
    return policy, frame, handle
```

The `_safe_summary` step is the firewall boundary required by invariants I-01 and I-05. See [BOUNDARIES.md](BOUNDARIES.md) for the artifact-ownership table this code respects.

### ChainWeaver — orchestrating multi-agent flow

ChainWeaver coordinates multi-step flows. Tool-invocation steps must delegate to agent-kernel (or a compatible execution layer) — see I-07.

```python
from weaver_contracts import RoutingDecision

def run_flow(steps, token):
    state = {}
    for step in steps:
        decision: RoutingDecision = step.route(state)
        # Delegate execution; do not call tools directly.
        policy, frame, _handle = agent_kernel.execute(decision, token)
        if policy.decision == "deny":
            return _abort(policy)
        state[step.id] = frame
    return state
```

The full multi-agent walkthrough is in [`examples/multi_agent_orchestration.md`](../examples/multi_agent_orchestration.md).

---

## Next steps

- **Pick your adoption mode:** [ADOPTION_GUIDE.md](ADOPTION_GUIDE.md) lists the seven supported modes and the minimum contracts each requires.
- **Look up fields:** [CONTRACT_REFERENCE.md](CONTRACT_REFERENCE.md) has the complete field tables for all 16 Core and Extended types.
- **Common questions:** [FAQ.md](FAQ.md) covers extending contracts, version mismatches, telemetry, and spec compliance.
- **Read the worked examples:** [`examples/minimal_e2e_sequence.md`](../examples/minimal_e2e_sequence.md), [`examples/failure_scenarios.md`](../examples/failure_scenarios.md), [`examples/multi_agent_orchestration.md`](../examples/multi_agent_orchestration.md), [`examples/partial_capability_routing.md`](../examples/partial_capability_routing.md).
