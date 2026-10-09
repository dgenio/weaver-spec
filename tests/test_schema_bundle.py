#!/usr/bin/env python3
"""Validate the conformance schema corpus through the compound schema bundle."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_PATH = REPO_ROOT / "contracts" / "bundles" / "weaver-contracts.bundle.json"
CORPUS_PATH = REPO_ROOT / "conformance" / "corpus.yaml"


def _load_bundle() -> tuple[dict, Registry]:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    resource = Resource.from_contents(bundle, default_specification=DRAFT202012)
    registry = (
        Registry()
        .with_resource("urn:weaver-spec:offline-bundle", resource)
        .crawl()
    )
    return bundle, registry


def _schemas_by_name(bundle: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for key, schema in bundle["$defs"].items():
        _tier, separator, name = key.partition("__")
        if separator != "__" or not name:
            raise AssertionError(f"invalid generated bundle definition key: {key}")
        if name in result:
            raise AssertionError(f"duplicate schema name in bundle: {name}")
        result[name] = schema
    return result


def _errors(payload: dict, schema: dict, registry: Registry) -> list:
    validator = Draft202012Validator(
        schema,
        registry=registry,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    return list(validator.iter_errors(payload))


def main() -> None:
    bundle, registry = _load_bundle()
    schemas = _schemas_by_name(bundle)
    corpus = yaml.safe_load(CORPUS_PATH.read_text(encoding="utf-8"))

    positive_count = 0
    for case in corpus["positive"]:
        payload = json.loads((REPO_ROOT / case["payload"]).read_text(encoding="utf-8"))
        errors = _errors(payload, schemas[case["schema"]], registry)
        assert not errors, (
            f"positive bundle case failed: {case['payload']} -> {case['schema']}: "
            + "; ".join(error.message for error in errors)
        )
        positive_count += 1

    negative_count = 0
    for case in corpus["negative"]:
        if case["by"] != "schema":
            continue
        payload = json.loads((REPO_ROOT / case["payload"]).read_text(encoding="utf-8"))
        errors = _errors(payload, schemas[case["schema"]], registry)
        assert errors, (
            f"schema-negative bundle case was accepted: "
            f"{case['payload']} -> {case['schema']}"
        )
        negative_count += 1

    assert positive_count > 0
    assert negative_count > 0
    print(
        f"Bundle conformance passed: {positive_count} positive case(s), "
        f"{negative_count} schema-negative case(s)."
    )


if __name__ == "__main__":
    main()
