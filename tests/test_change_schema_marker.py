# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""A change report must carry the mapping-level `o4r-artifact: change-report` marker (#63)."""
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import validate  # noqa: E402

EXAMPLE = REPO / "examples" / "change" / "example-change.yaml"


def _validate(tmp_path, mutate):
    doc = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    mutate(doc["mapping-collection"]["mappings"][0])
    path = tmp_path / "change.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return validate.validate_file(path, strict=True)


def _drop_props(mapping):
    del mapping["props"]


def _empty_props(mapping):
    mapping["props"] = [{"name": "other", "value": "x"}]


def _wrong_value(mapping):
    mapping["props"] = [{"name": "o4r-artifact", "value": "something-else"}]


def test_example_with_marker_passes(tmp_path):
    result = _validate(tmp_path, lambda mapping: None)
    assert result["nist_pass"]["status"] == "pass", result["nist_pass"]["errors"]
    assert result["o4r_pass"]["status"] == "pass", result["o4r_pass"]["errors"]


@pytest.mark.parametrize("mutate", [_drop_props, _empty_props, _wrong_value])
def test_report_without_marker_fails_the_o4r_pass(tmp_path, mutate):
    result = _validate(tmp_path, mutate)
    assert result["nist_pass"]["status"] == "pass", result["nist_pass"]["errors"]
    assert result["o4r_pass"]["status"] == "fail"
    assert result["ok"] is False
