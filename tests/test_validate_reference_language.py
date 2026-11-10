# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""`reference-language` value range and no-mixing rule (ADR-017 points 3 and 4, #70)."""
import pytest

import validate


def _with(example_catalog, *values):
    example_catalog["catalog"]["metadata"]["props"] += [
        {"name": "reference-language", "value": v} for v in values]
    return example_catalog


def _o4r(catalog, write_yaml, **kwargs):
    return validate.validate_file(write_yaml("c.yaml", catalog), strict=True, **kwargs)["o4r_pass"]


@pytest.mark.parametrize("values", [(), ("de",), ("deu",), ("de", "fr", "it"), ("all",)])
def test_permitted_values_pass(example_catalog, write_yaml, values):
    result = _o4r(_with(example_catalog, *values), write_yaml)
    assert result["status"] == "pass", result["errors"]


@pytest.mark.parametrize("value", ["klingonisch", "DE", "d", "de-CH", "german", "ALL", ""])
def test_anything_else_is_rejected(example_catalog, write_yaml, value):
    result = _o4r(_with(example_catalog, value), write_yaml)
    assert result["status"] == "fail"
    assert any(f"reference-language '{value}' is neither" in e for e in result["errors"])


def test_non_string_value_is_rejected():
    doc = {"catalog": {"metadata": {"props": [{"name": "reference-language", "value": False}]}}}
    assert len(validate.reference_language_violations(doc)) == 1


@pytest.mark.parametrize("values", [("all", "de"), ("de", "all"), ("all", "all")])
def test_all_must_not_be_mixed(example_catalog, write_yaml, values):
    result = _o4r(_with(example_catalog, *values), write_yaml)
    assert result["status"] == "fail"
    assert any("'all' MUST NOT be combined" in e for e in result["errors"])


def test_absence_asserts_nothing(example_catalog):
    assert validate.reference_language_violations(example_catalog) == []
    assert validate.reference_language_violations({}) == []
    assert validate.reference_language_violations({"catalog": {"metadata": {"props": None}}}) == []


def test_not_applied_to_foreign_catalogs(example_catalog, write_yaml):
    result = _o4r(_with(example_catalog, "klingonisch"), write_yaml, foreign=True)
    assert result["status"] == "skipped"


@pytest.mark.parametrize("name", ["example-de.yaml", "example-fr.yaml"])
def test_multilingual_examples_have_no_reference_language_finding(repo, name):
    result = validate.validate_file(repo / "examples" / "multilingual" / name, strict=True)
    assert not any("reference-language" in e and "ADR-017" in e for e in result["o4r_pass"]["errors"])
