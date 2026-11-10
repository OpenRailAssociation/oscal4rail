# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""The NIST pass checks tokens and formats; what it cannot check, it reports (#66)."""
import json

import pytest

import validate


def _first_control(catalog):
    return catalog["catalog"]["groups"][0]["controls"][0]


def _nist(catalog, write_yaml):
    return validate.validate_file(write_yaml("c.yaml", catalog), strict=True)["nist_pass"]


def test_schemas_use_only_formats_that_have_a_checker(repo):
    """Guard: with the declared dependencies nothing is left unchecked."""
    used = set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("format"), str):
                used.add(node["format"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for path in list((repo / "schemas" / "nist").glob("oscal-*.json")) + \
            list((repo / "schemas" / "oscal4rail").glob("*.json")):
        walk(json.loads(path.read_text(encoding="utf-8")))
    assert used
    assert used <= set(validate.Draft7Validator.FORMAT_CHECKER.checkers)


def test_valid_catalog_has_no_unevaluated_constraints(example_catalog, write_yaml):
    result = _nist(example_catalog, write_yaml)
    assert result["status"] == "pass"
    assert result["skipped_constraints"] == {}


@pytest.mark.parametrize("bad_id", ["ex 1.1 !", "1-starts-with-digit", "has/slash"])
def test_invalid_token_fails(example_catalog, write_yaml, bad_id):
    _first_control(example_catalog)["id"] = bad_id
    result = _nist(example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert any("controls.0.id]" in e and "does not match" in e for e in result["errors"])


@pytest.mark.parametrize("good_id", ["übergang-1.1", "_x", "ex-1.1_smt"])
def test_unicode_letters_are_valid_tokens(example_catalog, write_yaml, good_id):
    _first_control(example_catalog)["id"] = good_id
    assert _nist(example_catalog, write_yaml)["status"] == "pass"


def test_invalid_uri_reference_fails(example_catalog, write_yaml):
    _first_control(example_catalog)["links"] = [{"href": "ht tp://x y"}]
    result = _nist(example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert any("links.0.href]" in e and "uri-reference" in e for e in result["errors"])


def test_relative_uri_reference_passes(example_catalog, write_yaml):
    _first_control(example_catalog)["links"] = [{"href": "docs/source.pdf#section-2"}]
    assert _nist(example_catalog, write_yaml)["status"] == "pass"


def test_invalid_date_time_fails(example_catalog, write_yaml):
    example_catalog["catalog"]["metadata"]["last-modified"] = "yesterday"
    result = _nist(example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert any("metadata.last-modified]" in e for e in result["errors"])


def test_missing_regex_module_is_reported_not_silent(monkeypatch, example_catalog, write_yaml, capsys):
    monkeypatch.setattr(validate, "_regex", None)
    _first_control(example_catalog)["id"] = "ex 1.1 !"
    path = write_yaml("c.yaml", example_catalog)
    result = validate.validate_file(path, strict=True)

    skipped = result["nist_pass"]["skipped_constraints"]
    assert len(skipped) == 1 and sum(skipped.values()) > 0
    assert "regex" in next(iter(skipped))

    validate._print_summary(result, quiet=False)
    assert "NOT evaluated" in capsys.readouterr().out
    markdown = validate.render_markdown(validate.build_report(result, strict=True))
    assert "Constraints NOT evaluated" in markdown


def test_missing_format_checker_is_reported_not_silent(monkeypatch, example_catalog, write_yaml):
    reduced = validate.jsonschema.FormatChecker(formats=["date", "email"])
    monkeypatch.setattr(validate.Draft7Validator, "FORMAT_CHECKER", reduced)
    _first_control(example_catalog)["links"] = [{"href": "ht tp://x y"}]
    result = _nist(example_catalog, write_yaml)
    assert any("format 'uri-reference' not checked" in reason for reason in result["skipped_constraints"])


def test_error_message_names_the_offending_value(example_catalog, write_yaml):
    _first_control(example_catalog)["id"] = "ex 1.1 !"
    errors = _nist(example_catalog, write_yaml)["errors"]
    assert len(errors) == 1
    assert errors[0].startswith("[catalog.groups.0.controls.0.id] 'ex 1.1 !'")
