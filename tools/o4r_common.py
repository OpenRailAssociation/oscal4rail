# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for the OSCAL4Rail tools.

One place for the three things several tools need, so they cannot drift apart:

- reading the pinned OSCAL version from the NIST schema manifest (ADR-008),
- loading an artifact from YAML or JSON,
- walking every control of a catalog, at any depth.
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
NIST_DIR = REPO_ROOT / "schemas" / "nist"
MANIFEST = NIST_DIR / "manifest.json"


def load_document(path: Path) -> dict:
    """Load an artifact: YAML for `.yaml`/`.yml`, JSON otherwise."""
    with open(path, encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        return json.load(f)


def pinned_oscal_version() -> str | None:
    """The OSCAL version pinned in the schema manifest, or None if it cannot be read."""
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f).get("oscal_version")
    except (OSError, ValueError):
        return None


def iter_controls(catalog_doc: dict) -> Iterator[dict]:
    """Yield every control of a catalog document, in document order.

    Covers controls in groups, in nested groups, directly under the catalog, and
    child controls of controls. A control is yielded before its children.
    """
    catalog = catalog_doc.get("catalog") or {}

    def _from_control(control: dict) -> Iterator[dict]:
        yield control
        for child in control.get("controls") or []:
            yield from _from_control(child)

    def _from_groups(groups: list | None) -> Iterator[dict]:
        for group in groups or []:
            for control in group.get("controls") or []:
                yield from _from_control(control)
            yield from _from_groups(group.get("groups"))

    yield from _from_groups(catalog.get("groups"))
    for control in catalog.get("controls") or []:
        yield from _from_control(control)
