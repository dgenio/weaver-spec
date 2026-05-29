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

- Total contract types: **32**
- JSON Schemas: **32 / 32**
- Python classes: **32 / 32**
- Sample payloads: **32 / 32**
- Roundtrip tests: **32 / 32**
- Schema validation tests: **26 / 32**

## Coverage table

| Tier | Type | JSON Schema | Python Class | Sample Payload | Roundtrip Test | Schema Test |
| ---- | ---- | :---------: | :----------: | :------------: | :------------: | :---------: |
| Core | `SelectableItem` | OK | OK | OK | OK | -- |
| Core | `ChoiceCard` | OK | OK | OK | OK | OK |
| Core | `RoutingDecision` | OK | OK | OK | OK | -- |
| Core | `Capability` | OK | OK | OK | OK | -- |
| Core | `CapabilityToken` | OK | OK | OK | OK | OK |
| Core | `PolicyDecision` | OK | OK | OK | OK | -- |
| Core | `Frame` | OK | OK | OK | OK | OK |
| Core | `Handle` | OK | OK | OK | OK | -- |
| Core | `TraceEvent` | OK | OK | OK | OK | -- |
| Extended | `TelemetryHint` | OK | OK | OK | OK | OK |
| Extended | `SchemaFingerprint` | OK | OK | OK | OK | OK |
| Extended | `RedactionPolicy` | OK | OK | OK | OK | OK |
| Extended | `UIHint` | OK | OK | OK | OK | OK |
| Extended | `RiskAssessment` | OK | OK | OK | OK | OK |
| Extended | `ExtendedFrameMetadata` | OK | OK | OK | OK | OK |
| Extended | `ExtendedSelectableItemMetadata` | OK | OK | OK | OK | OK |
| Extended | `ReviewArtifact` | OK | OK | OK | OK | OK |
| Extended | `MemoryArtifact` | OK | OK | OK | OK | OK |
| Extended | `SessionHandoff` | OK | OK | OK | OK | OK |
| Extended | `LessonCard` | OK | OK | OK | OK | OK |
| Extended | `SkillCard` | OK | OK | OK | OK | OK |
| Extended | `EvaluationArtifact` | OK | OK | OK | OK | OK |
| Extended | `ArtifactSafetyGateRequest` | OK | OK | OK | OK | OK |
| Extended | `ArtifactSafetyReport` | OK | OK | OK | OK | OK |
| Extended | `CapabilityTokenSignature` | OK | OK | OK | OK | OK |
| Extended | `OtelTraceMapping` | OK | OK | OK | OK | OK |
| Extended | `CompiledFlow` | OK | OK | OK | OK | OK |
| Extended | `ExecutionCandidate` | OK | OK | OK | OK | OK |
| Extended | `ExecutionRoutingDecision` | OK | OK | OK | OK | OK |
| Extended | `ExecutionFeedback` | OK | OK | OK | OK | OK |
| Extended | `TraceBundle` | OK | OK | OK | OK | OK |
| Extended | `FailureCaseArtifact` | OK | OK | OK | OK | OK |

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
