# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""O4R constraints are selected by artifact subtype, not by root key alone (#67)."""
import copy

import o4r_common
import validate

CHANGE_REPORT = "examples/change/example-change.yaml"
CONTROL_MAPPING = "examples/mappings/company-subset-to-iso27001.mapping.yaml"


def test_change_report_is_checked_against_the_change_constraints(repo):
    result = validate.validate_file(repo / CHANGE_REPORT, strict=True)
    assert result["subtype"] == "change-report"
    assert result["o4r_pass"]["schema"] == "oscal4rail-change.schema.json"
    assert result["o4r_pass"]["status"] == "pass"
    assert result["ok"] is True


def test_invalid_change_report_still_fails_the_o4r_pass(repo, write_yaml):
    report = o4r_common.load_document(repo / CHANGE_REPORT)
    report["mapping-collection"]["mappings"][0]["maps"][0]["ns"] = "https://example.org/other"
    result = validate.validate_file(write_yaml("change.yaml", report), strict=True)
    assert result["subtype"] == "change-report"
    assert result["o4r_pass"]["status"] == "fail"


def test_ordinary_control_mapping_is_not_checked_as_a_change_report(repo):
    result = validate.validate_file(repo / CONTROL_MAPPING, strict=True)
    assert result["subtype"] == "control-mapping"
    assert result["nist_pass"]["status"] == "pass", result["nist_pass"]["errors"]
    assert result["o4r_pass"]["status"] == "skipped"
    assert result["o4r_pass"]["errors"] == []
    assert "control-mapping" in result["o4r_pass"]["reason"]
    assert result["ok"] is True


def test_marker_on_any_mapping_makes_it_a_change_report(repo):
    mapping = o4r_common.load_document(repo / CONTROL_MAPPING)
    assert validate.detect_subtype(mapping, "mapping-collection") == "control-mapping"
    marked = copy.deepcopy(mapping)
    marked["mapping-collection"]["mappings"][0].setdefault("props", []).append(
        {"name": "o4r-artifact", "value": "change-report"})
    assert validate.detect_subtype(marked, "mapping-collection") == "change-report"


def test_subtype_detection_tolerates_malformed_mappings():
    for root in (None, {}, {"mappings": None}, {"mappings": ["x", {"props": "y"}, {"props": [None]}]}):
        assert validate.detect_subtype({"mapping-collection": root}, "mapping-collection") == "control-mapping"


def test_other_models_are_their_own_subtype(example_catalog, example_rules):
    assert validate.detect_subtype(example_catalog, "catalog") == "catalog"
    assert validate.detect_subtype(example_rules, "rule-set") == "rule-set"


def _foreign_catalog(example_catalog):
    """Valid OSCAL that does not follow the OSCAL4Rail catalog conventions."""
    for control in example_catalog["catalog"]["groups"][0]["controls"]:
        control["props"] = [p for p in control["props"] if p["name"] != "source-chapter"]
    return example_catalog


def test_foreign_catalog_fails_the_o4r_pass_unless_declared(example_catalog, write_yaml):
    path = write_yaml("upstream.yaml", _foreign_catalog(example_catalog))
    assert validate.validate_file(path, strict=True)["o4r_pass"]["status"] == "fail"

    result = validate.validate_file(path, strict=True, foreign=True)
    assert result["nist_pass"]["status"] == "pass"
    assert result["o4r_pass"]["status"] == "skipped"
    assert result["o4r_pass"]["errors"] == []
    assert "foreign" in result["o4r_pass"]["reason"]
    assert result["ok"] is True


def test_foreign_does_not_waive_the_nist_pass(example_catalog, write_yaml):
    del example_catalog["catalog"]["metadata"]["title"]
    result = validate.validate_file(write_yaml("upstream.yaml", example_catalog), strict=True, foreign=True)
    assert result["nist_pass"]["status"] == "fail"
    assert result["ok"] is False


def test_foreign_has_no_effect_on_a_rule_set(repo):
    result = validate.validate_file(repo / "examples/rules/example-rules.yaml", strict=True, foreign=True)
    assert result["o4r_pass"]["status"] == "pass"


def test_report_states_subtype_and_applied_constraints(repo):
    result = validate.validate_file(repo / CONTROL_MAPPING, strict=True, foreign=True)
    report = validate.build_report(result, strict=True, foreign=True)
    assert report["mode"]["foreign"] is True
    markdown = validate.render_markdown(report)
    assert "**Subtype:** `control-mapping`" in markdown
    assert "only the NIST base schema was applied" in markdown
