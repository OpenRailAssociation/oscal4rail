# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Every versioned catalog and example passes `validate.py --strict` (#68).

There are no negative examples in the repository. If one is ever added, list it
in NEGATIVE_EXAMPLES with the reason, so the exclusion is explicit.
"""
from pathlib import Path

import pytest

import validate

REPO = Path(__file__).resolve().parent.parent
NEGATIVE_EXAMPLES: dict[str, str] = {}


def _versioned_artifacts() -> list[str]:
    found = []
    for top in ("catalogs", "examples"):
        for path in sorted((REPO / top).rglob("*.yaml")):
            rel = path.relative_to(REPO).as_posix()
            # generated or fetched, git-ignored: not versioned
            if any(part in ("_fetched", "_rendered") for part in path.parts) or ".validation." in path.name:
                continue
            if rel not in NEGATIVE_EXAMPLES:
                found.append(rel)
    return found


def test_artifacts_are_discovered():
    artifacts = _versioned_artifacts()
    assert "catalogs/bs-ki/de/bs-ki-de.yaml" in artifacts
    assert len(artifacts) >= 10


@pytest.mark.parametrize("relpath", _versioned_artifacts())
def test_versioned_artifact_passes_strict(relpath):
    result = validate.validate_file(REPO / relpath, strict=True)
    assert result["nist_pass"]["status"] in ("pass", "skipped"), result["nist_pass"]["errors"]
    assert result["o4r_pass"]["status"] in ("pass", "skipped"), result["o4r_pass"]["errors"]
    assert result["ok"] is True
    assert result["nist_pass"]["skipped_constraints"] == {}
    assert result["o4r_pass"]["skipped_constraints"] == {}
