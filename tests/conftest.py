# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Shared fixtures. The tools are importable via `pythonpath` in pyproject.toml."""
import copy
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO


@pytest.fixture(scope="session")
def _example_docs():
    rules_dir = REPO / "examples" / "rules"
    return {
        name: yaml.safe_load((rules_dir / f"{name}.yaml").read_text(encoding="utf-8"))
        for name in ("example-catalog", "example-rules")
    }


@pytest.fixture
def example_catalog(_example_docs) -> dict:
    """A fresh, mutable copy of examples/rules/example-catalog.yaml."""
    return copy.deepcopy(_example_docs["example-catalog"])


@pytest.fixture
def example_rules(_example_docs) -> dict:
    """A fresh, mutable copy of examples/rules/example-rules.yaml."""
    return copy.deepcopy(_example_docs["example-rules"])


@pytest.fixture
def write_yaml(tmp_path):
    """Write a document as YAML into the test's temp dir and return the path."""
    def _write(name: str, doc: dict) -> Path:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return path
    return _write
