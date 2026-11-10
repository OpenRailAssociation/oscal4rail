# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""The change constraints require the mapping-level `o4r-artifact: change-report` marker (#63).

The tests apply the change schema directly. Which schema the validator selects for a
mapping-collection is a separate concern (#67) and is tested there.
"""
import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

REPO = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO / "schemas" / "oscal4rail" / "oscal4rail-change.schema.json").read_text(encoding="utf-8"))
EXAMPLE = yaml.safe_load((REPO / "examples" / "change" / "example-change.yaml").read_text(encoding="utf-8"))


def _errors(mutate):
    doc = copy.deepcopy(EXAMPLE)
    mutate(doc["mapping-collection"]["mappings"])
    return [e.message for e in Draft7Validator(SCHEMA).iter_errors(doc)]


def _drop_props(mappings):
    del mappings[0]["props"]


def _other_props_only(mappings):
    mappings[0]["props"] = [{"name": "other", "value": "x"}]


def _wrong_value(mappings):
    mappings[0]["props"] = [{"name": "o4r-artifact", "value": "something-else"}]


def _second_mapping_without_marker(mappings):
    second = copy.deepcopy(mappings[0])
    del second["props"]
    mappings.append(second)


def test_example_with_marker_satisfies_the_change_constraints():
    assert _errors(lambda mappings: None) == []


@pytest.mark.parametrize(
    "mutate", [_drop_props, _other_props_only, _wrong_value, _second_mapping_without_marker])
def test_mapping_without_marker_violates_the_change_constraints(mutate):
    assert len(_errors(mutate)) == 1
