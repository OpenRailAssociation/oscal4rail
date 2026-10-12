#!/usr/bin/env python3
"""Validate OSCAL4Rail YAML/JSON artifacts against NIST OSCAL JSON Schemas.

Supports: Catalog, Profile, Assessment Results, Component Definition, Mapping.
Schema auto-detection based on root element.
"""

import json
import sys
from pathlib import Path

import jsonschema
import jsonschema._keywords
import yaml
from jsonschema import Draft7Validator

# Schema directory relative to this script
SCHEMA_DIR = Path(__file__).parent.parent / "schemas"

# Map OSCAL root element → schema file
SCHEMA_MAP = {
    "catalog": "oscal-catalog.json",
    "profile": "oscal-profile.json",
    "assessment-results": "oscal-assessment-results.json",
    "component-definition": "oscal-component-definition.json",
    "mapping-collection": "oscal-mapping.json",
}


def safe_pattern(validator, patrn, instance, schema):
    """Skip Unicode regex patterns (\\p{L}) not supported by Python re."""
    if r"\p{" in patrn:
        return
    yield from jsonschema._keywords.pattern(validator, patrn, instance, schema)


CustomValidator = jsonschema.validators.extend(Draft7Validator, {"pattern": safe_pattern})


def detect_model_type(data: dict) -> str | None:
    """Detect OSCAL model type from root element."""
    for key in SCHEMA_MAP:
        if key in data:
            return key
    return None


def validate(file_path: str) -> bool:
    path = Path(file_path)

    # Load YAML or JSON
    with open(path) as f:
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    # Detect model type
    model_type = detect_model_type(data)
    if not model_type:
        print(f"⚠️  {file_path}: Cannot detect OSCAL model type (root keys: {list(data.keys())[:5]})")
        return False

    # Load schema
    schema_file = SCHEMA_DIR / SCHEMA_MAP[model_type]
    if not schema_file.exists():
        print(f"⚠️  {file_path}: Schema not found: {schema_file}")
        print(f"   Download from: https://github.com/usnistgov/OSCAL/releases/tag/v1.2.1")
        return False

    with open(schema_file) as f:
        schema = json.load(f)

    # Validate
    validator = CustomValidator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))

    if not errors:
        print(f"✅ {file_path}: Valid OSCAL {model_type.replace('-', ' ').title()}")
        return True

    print(f"❌ {file_path}: {len(errors)} validation error(s) [{model_type}]:")
    for e in errors[:20]:
        path_str = ".".join(str(p) for p in e.absolute_path)
        print(f"  - [{path_str}] {e.message[:150]}")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate.py <file.yaml> [<file2.yaml> ...]")
        print("")
        print("Validates OSCAL artifacts against NIST OSCAL v1.2.1 JSON Schema.")
        print(f"Schemas expected in: {SCHEMA_DIR}")
        print(f"Supported models: {', '.join(SCHEMA_MAP.keys())}")
        sys.exit(1)

    all_valid = all(validate(f) for f in sys.argv[1:])
    sys.exit(0 if all_valid else 1)
