# weaver_contracts Python Package

Minimal Python contracts for the Weaver Stack.

This package provides dataclasses and type definitions for all Core Weaver contracts. It has **no runtime dependencies** beyond the Python standard library (Python 3.9+).

---

## Installation

```bash
pip install weaver_contracts
```

For development (includes `pytest` and `jsonschema`):

```bash
pip install "weaver_contracts[dev]"
```

---

## Usage

```python
from weaver_contracts import (
    SelectableItem,
    ChoiceCard,
    RoutingDecision,
    Capability,
    CapabilityToken,
    PolicyDecision,
    Frame,
    Handle,
    TraceEvent,
)
from weaver_contracts.version import CONTRACT_VERSION, is_compatible
from datetime import datetime, timezone

# Routing
item = SelectableItem(id="search-1", label="Search docs", description="Search documentation")
card = ChoiceCard(id="card-1", items=[item], context_hint="Select a retrieval action")
rd = RoutingDecision(
    id="rd-abc",
    choice_cards=[card],
    timestamp=datetime.now(timezone.utc),
    selected_item_id="search-1",
)

# Authorization
token = CapabilityToken(
    token_id="tok-xyz",
    principal="my-agent",
    scope=["org.myapp.search_docs"],
    issued_at=datetime.now(timezone.utc),
    expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
)

# Frame (safe output)
frame = Frame(
    frame_id="frame-001",
    capability_id="org.myapp.search_docs",
    summary="Found 3 documents matching 'query'.",
    created_at=datetime.now(timezone.utc),
    handle_refs=["handle-abc"],  # reference to raw artifact
)
```

---

## Contract Tiers

| Module | Contents | Stability |
| -------- | ---------- | ----------- |
| `weaver_contracts.core` | Core contracts (all 9 types) | Stable within major version |
| `weaver_contracts.extended` | Optional metadata types | May evolve in minor versions |
| `weaver_contracts.version` | Version constants + `is_compatible()` | Stable |

---

## Running Tests

```bash
cd contracts/python
pip install -e ".[dev]"
pytest
```

---

## Schema Alignment

The JSON Schemas in `contracts/json/` are the language-agnostic source of truth. The Python types mirror the schemas exactly. If a schema changes, the corresponding Python type and tests should be updated in the same PR.
