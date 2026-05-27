"""
Tests that Extended sample payloads validate against the Extended JSON
Schemas in contracts/json/extended/.

Mirrors test_json_schema_alignment.py (which covers Core), but targets the
Extended tier. Each Extended type is listed by its dataclass name so the
coverage table generator (scripts/generate_coverage_table.py) detects the
schema-test artifact for that type.
"""

import json
import pathlib

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
CORE_SCHEMA_DIR = REPO_ROOT / "contracts" / "json"
EXTENDED_SCHEMA_DIR = CORE_SCHEMA_DIR / "extended"
PAYLOADS_DIR = REPO_ROOT / "examples" / "sample_payloads"

# (dataclass name, snake_case schema/payload stem). The dataclass names appear
# here as whole tokens so the coverage generator marks the schema test present:
# ReviewArtifact, MemoryArtifact, SessionHandoff, LessonCard, SkillCard,
# EvaluationArtifact, ArtifactSafetyGateRequest, ArtifactSafetyReport.
EXTENDED_TYPES = [
    ("ReviewArtifact", "review_artifact"),
    ("MemoryArtifact", "memory_artifact"),
    ("SessionHandoff", "session_handoff"),
    ("LessonCard", "lesson_card"),
    ("SkillCard", "skill_card"),
    ("EvaluationArtifact", "evaluation_artifact"),
    ("ArtifactSafetyGateRequest", "artifact_safety_gate_request"),
    ("ArtifactSafetyReport", "artifact_safety_report"),
]


def load_extended_schema(stem: str) -> dict:
    with open(EXTENDED_SCHEMA_DIR / f"{stem}.schema.json") as f:
        return json.load(f)


def load_payload(stem: str) -> dict:
    with open(PAYLOADS_DIR / f"{stem}.json") as f:
        return json.load(f)


def build_store() -> dict:
    """URI -> schema for all local schemas (Core + Extended), so $ref
    resolution works without network access."""
    store = {}
    for schema_file in list(CORE_SCHEMA_DIR.glob("*.schema.json")) + list(
        EXTENDED_SCHEMA_DIR.glob("*.schema.json")
    ):
        with open(schema_file) as f:
            schema = json.load(f)
        if "$id" in schema:
            store[schema["$id"]] = schema
    return store


_SCHEMA_STORE = build_store()


def validate(payload: dict, schema: dict) -> None:
    resolver = jsonschema.RefResolver(
        base_uri=schema.get("$id", ""),
        referrer=schema,
        store=_SCHEMA_STORE,
    )
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(
        schema,
        resolver=resolver,
        format_checker=jsonschema.FormatChecker(),
    )
    errors = list(validator.iter_errors(payload))
    if errors:
        msgs = "\n".join(str(e) for e in errors)
        raise AssertionError(f"Schema validation failed:\n{msgs}")


class TestExtendedSchemaStructure:
    """Every Extended schema must declare the required metadata fields."""

    @pytest.mark.parametrize(
        "schema_file", sorted(EXTENDED_SCHEMA_DIR.glob("*.schema.json"))
    )
    def test_schema_has_required_metadata(self, schema_file):
        with open(schema_file) as f:
            data = json.load(f)
        for key in ("$id", "title", "description", "required"):
            assert key in data, f"{schema_file.name} must declare {key}"
        assert "extended/" in data["$id"], (
            f"{schema_file.name} $id must live under the extended/ namespace"
        )


class TestExtendedPayloadValidation:
    """Each Extended sample payload validates against its schema."""

    @pytest.mark.parametrize("class_name,stem", EXTENDED_TYPES)
    def test_payload_validates(self, class_name, stem):
        schema = load_extended_schema(stem)
        payload = load_payload(stem)
        validate(payload, schema)


class TestExtendedNegativeCases:
    """A few targeted negatives confirm the schemas actually constrain."""

    def test_memory_artifact_missing_required_fails(self):
        schema = load_extended_schema("memory_artifact")
        bad = {"memory_id": "m1"}  # missing memory_type/content/source/created_at
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_evaluation_artifact_bad_support_state_fails(self):
        schema = load_extended_schema("evaluation_artifact")
        bad = {
            "artifact_id": "e1",
            "producer": "skdr-eval",
            "created_at": "2026-05-27T10:00:00Z",
            "support_state": "explosive",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)

    def test_artifact_safety_report_bad_decision_fails(self):
        schema = load_extended_schema("artifact_safety_report")
        bad = {
            "report_id": "r1",
            "gate_id": "g1",
            "decision": "maybe",
            "created_at": "2026-05-27T10:30:00Z",
        }
        with pytest.raises(AssertionError, match="Schema validation failed"):
            validate(bad, schema)
