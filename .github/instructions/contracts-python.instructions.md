---
applyTo: "contracts/python/**"
---

# Python Contract Instructions

## Constraints

- Use stdlib only (`dataclasses`, `typing`). No third-party runtime dependencies in `core.py` or `extended.py`.
- Validation is construction-time only (dataclass `__post_init__`). Never add runtime validation, conversion helpers, or business logic.
- Field names, types, and required/optional status in `core.py` must match the corresponding JSON schema exactly. Zero divergence.

## Required artifacts

- Every new or changed Python type must have a roundtrip test in `tests/test_roundtrip_examples.py`.
- Python changes to contract types are never standalone — the same PR must include the corresponding schema change and all other required artifacts. See `AGENTS.md` for the full six-artifact rule.
