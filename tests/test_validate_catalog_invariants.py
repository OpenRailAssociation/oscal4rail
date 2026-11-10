# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Catalog invariants stated in catalog-format.md sections 2 and 3 are enforced (#69)."""
import copy

import pytest

import validate

BS_KI = "catalogs/bs-ki/de/bs-ki-de.yaml"


def _controls(catalog):
    return catalog["catalog"]["groups"][0]["controls"]


def _o4r(catalog, write_yaml):
    result = validate.validate_file(write_yaml("c.yaml", catalog), strict=True)
    assert result["nist_pass"]["status"] == "pass", result["nist_pass"]["errors"]
    return result["o4r_pass"]


def _child(cid="ex-1.1.1", chapter="1.1.1", prose="Child statement."):
    return {"id": cid, "title": "Child",
            "props": [{"name": "source-chapter", "value": chapter}],
            "parts": [{"name": "statement", "prose": prose}]}


def test_reference_catalog_satisfies_the_invariants(repo):
    result = validate.validate_file(repo / BS_KI, strict=True)
    assert result["o4r_pass"]["status"] == "pass", result["o4r_pass"]["errors"]


# --- section 2: the id encodes the source chapter ------------------------------

def test_id_must_encode_the_source_chapter(example_catalog, write_yaml):
    control = _controls(example_catalog)[0]
    next(p for p in control["props"] if p["name"] == "source-chapter")["value"] = "9.9"
    result = _o4r(example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert result["errors"] == [
        f"[control {control['id']}] id does not encode source-chapter '9.9'; expected "
        "'<regulation>-9.9[-<context>]' (catalog-format.md section 2)"]


def test_page_based_id_is_caught_by_the_cross_check(example_catalog, write_yaml):
    _controls(example_catalog)[0]["id"] = "ex-seite-12"   # source-chapter stays 1.1
    result = _o4r(example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert any("[control ex-seite-12] id does not encode source-chapter '1.1'" in e for e in result["errors"])


@pytest.mark.parametrize("cid, chapter", [
    ("ex-1.1", "1.1"), ("ex-1.1-stop", "1.1"), ("iso-27001-5.1", "5.1"), ("bs-ki-2", "2")])
def test_ids_that_encode_their_chapter_pass(cid, chapter):
    doc = {"catalog": {"controls": [{"id": cid, "props": [{"name": "source-chapter", "value": chapter}]}]}}
    assert validate.catalog_consistency(doc) == []


@pytest.mark.parametrize("cid, chapter", [
    ("ex-1.10", "1.1"), ("ex-11.1", "1.1"), ("ex-1.1", "1"), ("ex-1.1", "")])
def test_ids_that_only_resemble_their_chapter_fail(cid, chapter):
    doc = {"catalog": {"controls": [{"id": cid, "props": [{"name": "source-chapter", "value": chapter}]}]}}
    assert len(validate.catalog_consistency(doc)) == 1


# --- unique control ids ---------------------------------------------------------

def test_duplicate_control_id_fails(example_catalog, write_yaml):
    controls = _controls(example_catalog)
    controls.append(copy.deepcopy(controls[0]))
    result = _o4r(example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert result["errors"] == [
        f"[control {controls[0]['id']}] duplicate control id; ids MUST be unique within a catalog"]


def test_duplicate_control_id_across_levels_fails(example_catalog, write_yaml):
    controls = _controls(example_catalog)
    controls[1]["controls"] = [copy.deepcopy(controls[0])]   # same id, now as a child control
    result = _o4r(example_catalog, write_yaml)
    assert any("duplicate control id" in e for e in result["errors"])


# --- section 3: the statement is not empty --------------------------------------

@pytest.mark.parametrize("prose", [" ", "\n\t  \n"])
def test_whitespace_only_statement_fails(example_catalog, write_yaml, prose):
    _controls(example_catalog)[0]["parts"][0]["prose"] = prose
    assert _o4r(example_catalog, write_yaml)["status"] == "fail"


def test_every_statement_part_must_have_prose_not_just_one(example_catalog, write_yaml):
    _controls(example_catalog)[0]["parts"].append({"name": "statement", "prose": "   "})
    assert _o4r(example_catalog, write_yaml)["status"] == "fail"


def test_non_statement_parts_are_not_constrained(example_catalog, write_yaml):
    _controls(example_catalog)[0]["parts"].append({"name": "guidance", "title": "Note", "prose": "Text."})
    assert _o4r(example_catalog, write_yaml)["status"] == "pass"


# --- child controls and root-level controls are covered -------------------------

def test_valid_child_control_passes(example_catalog, write_yaml):
    _controls(example_catalog)[0]["controls"] = [_child()]
    result = _o4r(example_catalog, write_yaml)
    assert result["status"] == "pass", result["errors"]


@pytest.mark.parametrize("break_child, expected", [
    (lambda c: c.pop("props"), "'props' is a required property"),
    (lambda c: c.update(id="Not An O4R Id"), "does not match"),
    (lambda c: c["parts"][0].update(prose="  "), "does not match"),
    (lambda c: c["props"][0].update(value="7.7"), "does not encode source-chapter '7.7'"),
])
def test_child_control_violations_fail(example_catalog, write_yaml, break_child, expected):
    child = _child()
    break_child(child)
    _controls(example_catalog)[0]["controls"] = [child]
    result = validate.validate_file(write_yaml("c.yaml", example_catalog), strict=True)["o4r_pass"]
    assert result["status"] == "fail"
    assert any(expected in e for e in result["errors"]), result["errors"]


def test_root_level_control_violations_fail(example_catalog, write_yaml):
    broken = _child(cid="ex-9.1", chapter="9.1")
    del broken["props"]
    example_catalog["catalog"]["controls"] = [broken]
    result = _o4r(example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert any("'props' is a required property" in e for e in result["errors"])


# --- scope ----------------------------------------------------------------------

def test_invariants_are_not_applied_to_foreign_catalogs(example_catalog, write_yaml):
    controls = _controls(example_catalog)
    controls.append(copy.deepcopy(controls[0]))
    result = validate.validate_file(write_yaml("c.yaml", example_catalog), strict=True, foreign=True)
    assert result["o4r_pass"]["status"] == "skipped"

