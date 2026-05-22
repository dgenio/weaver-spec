#!/usr/bin/env python3
"""Generate the schema-to-artifact coverage table.

Scans the repository for each Weaver contract type and reports which of the
five expected artifacts is present:

  1. JSON Schema    — contracts/json/<snake>.schema.json (Core)
                      or contracts/json/extended/<snake>.schema.json (Extended)
  2. Python class   — class definition in core.py / extended.py
  3. Sample payload — examples/sample_payloads/<snake>.json
  4. Roundtrip test — class name appears in test_roundtrip_examples.py
                      or test_extended.py
  5. Schema test    — class name appears in test_json_schema_alignment.py
                      or test_extended_schema_alignment.py

Output is written to contracts/COVERAGE.md.

Run modes:
  python scripts/generate_coverage_table.py            # write COVERAGE.md
  python scripts/generate_coverage_table.py --check    # exit non-zero if stale

Stdlib only — no third-party dependencies (per AGENTS.md "no runtime logic").
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

CORE_DIR = REPO_ROOT / "contracts" / "json"
EXTENDED_DIR = CORE_DIR / "extended"
PAYLOADS_DIR = REPO_ROOT / "examples" / "sample_payloads"
CORE_PY = REPO_ROOT / "contracts" / "python" / "src" / "weaver_contracts" / "core.py"
EXTENDED_PY = REPO_ROOT / "contracts" / "python" / "src" / "weaver_contracts" / "extended.py"
ROUNDTRIP_TEST = REPO_ROOT / "contracts" / "python" / "tests" / "test_roundtrip_examples.py"
SCHEMA_TEST = REPO_ROOT / "contracts" / "python" / "tests" / "test_json_schema_alignment.py"
EXTENDED_TEST = REPO_ROOT / "contracts" / "python" / "tests" / "test_extended.py"
EXTENDED_SCHEMA_TEST = REPO_ROOT / "contracts" / "python" / "tests" / "test_extended_schema_alignment.py"

OUTPUT_PATH = REPO_ROOT / "contracts" / "COVERAGE.md"

CHECK = "OK"
MISS = "--"


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def discover_class_names(path: Path) -> List[str]:
    """Return @dataclass-decorated class names in a Python source file, in source order."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    # Only match classes immediately preceded by @dataclass (with optional args).
    return re.findall(
        r"^@dataclass.*\n^class\s+([A-Za-z_][A-Za-z0-9_]*)\b", text, re.MULTILINE
    )


def schema_path_for(snake: str, tier: str) -> Path:
    if tier == "Core":
        return CORE_DIR / f"{snake}.schema.json"
    return EXTENDED_DIR / f"{snake}.schema.json"


def payload_path_for(snake: str, tier: str) -> List[Path]:
    """Candidate payload paths. Some Frames are stored as frame_with_handles.json."""
    candidates = [PAYLOADS_DIR / f"{snake}.json"]
    if snake == "frame":
        candidates.append(PAYLOADS_DIR / "frame_with_handles.json")
    return candidates


def references_class(path: Path, class_name: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return bool(re.search(r"\b" + re.escape(class_name) + r"\b", text))


def row_for(class_name: str, tier: str) -> Tuple[str, str, str, str, str, str, str]:
    snake = camel_to_snake(class_name)
    schema_p = schema_path_for(snake, tier)
    has_schema = CHECK if schema_p.exists() else MISS

    py_file = CORE_PY if tier == "Core" else EXTENDED_PY
    has_py = CHECK if references_class(py_file, class_name) else MISS

    has_payload = MISS
    for c in payload_path_for(snake, tier):
        if c.exists():
            has_payload = CHECK
            break

    if tier == "Core":
        has_roundtrip = CHECK if references_class(ROUNDTRIP_TEST, class_name) else MISS
        has_schema_test = CHECK if references_class(SCHEMA_TEST, class_name) else MISS
    else:
        has_roundtrip = CHECK if references_class(EXTENDED_TEST, class_name) else MISS
        has_schema_test = (
            CHECK if references_class(EXTENDED_SCHEMA_TEST, class_name) else MISS
        )

    return (
        tier,
        class_name,
        has_schema,
        has_py,
        has_payload,
        has_roundtrip,
        has_schema_test,
    )


def build_table() -> Tuple[List[Tuple[str, str, str, str, str, str, str]], dict]:
    rows: List[Tuple[str, str, str, str, str, str, str]] = []
    for cls in discover_class_names(CORE_PY):
        rows.append(row_for(cls, "Core"))
    for cls in discover_class_names(EXTENDED_PY):
        rows.append(row_for(cls, "Extended"))

    totals = {"types": len(rows)}
    artifact_idx = {"schemas": 2, "py": 3, "payloads": 4, "roundtrip": 5, "schema_test": 6}
    for key, idx in artifact_idx.items():
        totals[key] = sum(1 for r in rows if r[idx] == CHECK)
    return rows, totals


def render_markdown(rows: List[Tuple[str, str, str, str, str, str, str]], totals: dict) -> str:
    lines = [
        "<!-- AUTO-GENERATED — DO NOT EDIT.",
        "     Regenerate with: python scripts/generate_coverage_table.py -->",
        "",
        "# Contract Artifact Coverage",
        "",
        "Auto-generated map of which artifacts exist for each Weaver contract type.",
        "Five artifacts per type are tracked: JSON Schema, Python class, sample payload,",
        "roundtrip test, and JSON Schema validation test.",
        "",
        "Regenerate with:",
        "",
        "```bash",
        "python scripts/generate_coverage_table.py",
        "```",
        "",
        "CI runs the same script with `--check` and fails if this file is stale.",
        "",
        "## Summary",
        "",
        f"- Total contract types: **{totals['types']}**",
        f"- JSON Schemas: **{totals['schemas']} / {totals['types']}**",
        f"- Python classes: **{totals['py']} / {totals['types']}**",
        f"- Sample payloads: **{totals['payloads']} / {totals['types']}**",
        f"- Roundtrip tests: **{totals['roundtrip']} / {totals['types']}**",
        f"- Schema validation tests: **{totals['schema_test']} / {totals['types']}**",
        "",
        "## Coverage table",
        "",
        "| Tier | Type | JSON Schema | Python Class | Sample Payload | Roundtrip Test | Schema Test |",
        "| ---- | ---- | :---------: | :----------: | :------------: | :------------: | :---------: |",
    ]
    for tier, cls, schema, py, payload, roundtrip, schema_test in rows:
        lines.append(
            f"| {tier} | `{cls}` | {schema} | {py} | {payload} | {roundtrip} | {schema_test} |"
        )

    lines.extend([
        "",
        "## Legend",
        "",
        "- `OK` — artifact present.",
        "- `--` — artifact missing (gap to be filled in a future PR).",
        "",
        "Cells map to file conventions:",
        "",
        "- **JSON Schema** — `contracts/json/<snake>.schema.json` (Core) or",
        "  `contracts/json/extended/<snake>.schema.json` (Extended).",
        "- **Python Class** — declared in `contracts/python/src/weaver_contracts/core.py`",
        "  (Core) or `extended.py` (Extended).",
        "- **Sample Payload** — `examples/sample_payloads/<snake>.json`",
        "  (`frame` also accepts `frame_with_handles.json`).",
        "- **Roundtrip Test** — class name referenced in",
        "  `contracts/python/tests/test_roundtrip_examples.py` (Core) or",
        "  `test_extended.py` (Extended).",
        "- **Schema Test** — class name referenced in",
        "  `contracts/python/tests/test_json_schema_alignment.py` (Core) or",
        "  `test_extended_schema_alignment.py` (Extended).",
        "",
    ])
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if COVERAGE.md is stale instead of writing it.",
    )
    args = parser.parse_args(argv)

    rows, totals = build_table()
    content = render_markdown(rows, totals)

    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"FAIL: {OUTPUT_PATH.relative_to(REPO_ROOT)} does not exist.", file=sys.stderr)
            print("Run: python scripts/generate_coverage_table.py", file=sys.stderr)
            return 1
        existing = OUTPUT_PATH.read_text(encoding="utf-8")
        if existing != content:
            print(
                f"FAIL: {OUTPUT_PATH.relative_to(REPO_ROOT)} is stale.",
                file=sys.stderr,
            )
            print("Run: python scripts/generate_coverage_table.py", file=sys.stderr)
            return 1
        print(f"OK: {OUTPUT_PATH.relative_to(REPO_ROOT)} is up to date.")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({totals['types']} types).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
