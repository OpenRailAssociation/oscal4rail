# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""The change tool sees every control, at any depth (#61)."""
import copy
import subprocess
import sys

import pytest

import change
import o4r_common
import validate

BS_KI = "catalogs/bs-ki/de/bs-ki-de.yaml"


def _build(old_cat, new_cat):
    return change.build_mapping(old_cat, new_cat, None, None, "old", "new", "1.0", "1.1")


def _single_mapping(report):
    return report["mapping-collection"]["mappings"][0]


def _nested_catalog():
    def control(cid):
        return {"id": cid, "title": cid, "parts": [{"id": f"{cid}_smt", "name": "statement", "prose": f"Text {cid}."}]}
    return {"catalog": {
        "groups": [{
            "id": "g", "title": "g",
            "controls": [dict(control("t-1"), controls=[control("t-1.a")])],
            "groups": [{"id": "g-sub", "title": "g-sub", "controls": [control("t-2")]}],
        }],
        "controls": [control("t-3")],
    }}


def _statement(control):
    return next(p for p in control["parts"] if p["name"] == "statement")


def test_reference_catalog_is_fully_indexed(repo):
    doc = o4r_common.load_document(repo / BS_KI)
    assert len(change._controls(doc)) == 42


def test_validator_and_change_tool_see_the_same_controls(repo):
    doc = o4r_common.load_document(repo / BS_KI)
    validator_ids, _, _ = validate._load_catalog_controls(repo / BS_KI)
    assert set(change._controls(doc)) == validator_ids


@pytest.mark.parametrize("control_id", ["t-1.a", "t-2", "t-3"])
def test_change_below_the_top_level_is_reported(control_id):
    old = _nested_catalog()
    new = copy.deepcopy(old)
    _statement(change._controls(new)[control_id])["prose"] += " (changed)"
    maps = _single_mapping(_build(old, new))["maps"]
    assert [(m["relationship"], m["sources"][0]["id-ref"]) for m in maps] == [("content-changed", control_id)]


def test_change_in_a_sub_group_of_the_reference_catalog_is_reported(repo):
    old = o4r_common.load_document(repo / BS_KI)
    new = copy.deepcopy(old)
    parent = next(g for g in new["catalog"]["groups"] if g.get("groups"))
    nested = parent["groups"][0]["controls"][0]
    _statement(nested)["prose"] += " (changed)"
    maps = _single_mapping(_build(old, new))["maps"]
    assert [m["sources"][0]["id-ref"] for m in maps] == [nested["id"]]


def test_moving_a_control_into_a_sub_group_is_not_an_existence_change():
    old = _nested_catalog()
    new = copy.deepcopy(old)
    group = new["catalog"]["groups"][0]
    group["groups"][0]["controls"].append(new["catalog"]["controls"].pop())  # t-3: root -> sub-group
    mapping = _single_mapping(_build(old, new))
    assert "source-gap-summary" not in mapping
    assert "target-gap-summary" not in mapping
    assert mapping["maps"] == []


@pytest.mark.parametrize("side", ["old", "new"])
def test_duplicate_control_id_is_an_error(side):
    clean = _nested_catalog()
    broken = copy.deepcopy(clean)
    broken["catalog"]["groups"][0]["groups"][0]["controls"].append(copy.deepcopy(broken["catalog"]["controls"][0]))
    args = (broken, clean) if side == "old" else (clean, broken)
    with pytest.raises(change.DuplicateControlId, match=rf"'t-3' in the {side} catalog state"):
        _build(*args)


def test_cli_exits_non_zero_on_a_duplicate_control_id(repo, write_yaml):
    broken = _nested_catalog()
    broken["catalog"]["controls"].append(copy.deepcopy(broken["catalog"]["controls"][0]))
    clean, dup = write_yaml("clean.yaml", _nested_catalog()), write_yaml("dup.yaml", broken)
    result = subprocess.run(
        [sys.executable, "tools/change.py", "--from", str(clean), "--to", str(dup), "--summary"],
        cwd=repo, capture_output=True, text=True)
    assert result.returncode != 0
    assert "duplicate control id 't-3'" in result.stderr
    assert "Traceback" not in result.stderr
