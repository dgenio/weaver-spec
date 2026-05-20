<!-- AUTO-GENERATED — DO NOT EDIT.
     Regenerate with: python scripts/generate_coverage_table.py -->

# Contract Artifact Coverage

Auto-generated map of which artifacts exist for each Weaver contract type.
Five artifacts per type are tracked: JSON Schema, Python class, sample payload,
roundtrip test, and JSON Schema validation test.

Regenerate with:

```bash
python scripts/generate_coverage_table.py
```

CI runs the same script with `--check` and fails if this file is stale.

## Summary

- Total contract types: **16**
- JSON Schemas: **9 / 16**
- Python classes: **16 / 16**
- Sample payloads: **16 / 16**
- Roundtrip tests: **16 / 16**
- Schema validation tests: **9 / 16**

## Coverage table

| Tier | Type | JSON Schema | Python Class | Sample Payload | Roundtrip Test | Schema Test |
| ---- | ---- | :---------: | :----------: | :------------: | :------------: | :---------: |
| Core | `SelectableItem` | OK | OK | OK | OK | OK |
| Core | `ChoiceCard` | OK | OK | OK | OK | OK |
| Core | `RoutingDecision` | OK | OK | OK | OK | OK |
| Core | `Capability` | OK | OK | OK | OK | OK |
| Core | `CapabilityToken` | OK | OK | OK | OK | OK |
| Core | `PolicyDecision` | OK | OK | OK | OK | OK |
| Core | `Frame` | OK | OK | OK | OK | OK |
| Core | `Handle` | OK | OK | OK | OK | OK |
| Core | `TraceEvent` | OK | OK | OK | OK | OK |
| Extended | `TelemetryHint` | -- | OK | OK | OK | -- |
| Extended | `SchemaFingerprint` | -- | OK | OK | OK | -- |
| Extended | `RedactionPolicy` | -- | OK | OK | OK | -- |
| Extended | `UIHint` | -- | OK | OK | OK | -- |
| Extended | `RiskAssessment` | -- | OK | OK | OK | -- |
| Extended | `ExtendedFrameMetadata` | -- | OK | OK | OK | -- |
| Extended | `ExtendedSelectableItemMetadata` | -- | OK | OK | OK | -- |

## Legend

- `OK` — artifact present.
- `--` — artifact missing (gap to be filled in a future PR).

Cells map to file conventions:

- **JSON Schema** — `contracts/json/<snake>.schema.json` (Core) or
  `contracts/json/extended/<snake>.schema.json` (Extended).
- **Python Class** — declared in `contracts/python/src/weaver_contracts/core.py`
  (Core) or `extended.py` (Extended).
- **Sample Payload** — `examples/sample_payloads/<snake>.json`
  (`frame` also accepts `frame_with_handles.json`).
- **Roundtrip Test** — class name referenced in
  `contracts/python/tests/test_roundtrip_examples.py` (Core) or
  `test_extended.py` (Extended).
- **Schema Test** — class name referenced in
  `contracts/python/tests/test_json_schema_alignment.py` (Core) or
  `test_extended_schema_alignment.py` (Extended).
