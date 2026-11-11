# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for the OSCAL4Rail tools.

One place for the three things several tools need, so they cannot drift apart:

- reading the pinned OSCAL version from the NIST schema manifest (ADR-008),
- loading an artifact from YAML or JSON, without YAML 1.1 surprises,
- walking every control of a catalog, at any depth.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
NIST_DIR = REPO_ROOT / "schemas" / "nist"
MANIFEST = NIST_DIR / "manifest.json"


class AmbiguousScalarError(ValueError):
    """An unquoted YAML scalar would silently lose information when loaded."""


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader without the two YAML 1.1 traps that corrupt governance data.

    - Booleans are only `true` and `false` (as in YAML 1.2 and JSON). `yes`, `no`,
      `on`, `off`, `y`, `n` stay strings, so the language code `no` is not `False`.
    - A decimal with a trailing zero (`1.10`, `2.50`) is rejected instead of being
      loaded as a float: `version: 1.10` would become `1.1` and compare equal to
      version 1.1. The author must quote it (`'1.10'`) or drop the zero.
    """


_StrictLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:bool"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_StrictLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF"))

_LOSSY_DECIMAL = re.compile(r"[-+]?\d+\.\d+0")


def _construct_float(loader: yaml.SafeLoader, node: yaml.ScalarNode) -> float:
    if _LOSSY_DECIMAL.fullmatch(node.value):
        raise AmbiguousScalarError(
            f"line {node.start_mark.line + 1}: unquoted value {node.value} would be read as the "
            f"number {float(node.value)} and lose its trailing zero; quote it ('{node.value}') "
            "if it is a version or an identifier")
    return loader.construct_yaml_float(node)


_StrictLoader.add_constructor("tag:yaml.org,2002:float", _construct_float)


def load_text(text: str, source: str = "<text>"):
    """Parse YAML text with the strict loader (see `_StrictLoader`)."""
    try:
        return yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - subclass of SafeLoader
    except AmbiguousScalarError as exc:
        raise AmbiguousScalarError(f"{source}: {exc}") from None


def load_document(path: Path):
    """Load an artifact: YAML (strict, see `_StrictLoader`) for `.yaml`/`.yml`, JSON otherwise."""
    with open(path, encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            return load_text(f.read(), source=str(path))
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
