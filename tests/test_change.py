# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Change tool: classification that works today (ADR-019 D3).

Known gaps (nested groups, non-statement changes, one-sided-only reports) are tracked
in #61, #72 and #74 and get their tests with those fixes.
"""
import copy

import change
import o4r_common
import validate


def _first_control(catalog):
    return catalog["catalog"]["groups"][0]["controls"][0]


def _single_mapping(report):
    return report["mapping-collection"]["mappings"][0]


def _build(old_cat, new_cat, old_rules=None, new_rules=None):
    return change.build_mapping(old_cat, new_cat, old_rules, new_rules, "old", "new", "1.0", "1.1")


def _rule(rules, rule_id):
    return next(r for r in rules["rule-set"]["rules"] if r["rule-id"] == rule_id)


def test_report_declares_the_pinned_oscal_version(example_catalog):
    report = _build(example_catalog, example_catalog)
    assert report["mapping-collection"]["metadata"]["oscal-version"] == o4r_common.pinned_oscal_version()


def test_statement_change_without_rules_is_content_changed(example_catalog):
    new = copy.deepcopy(example_catalog)
    control = _first_control(new)
    next(p for p in control["parts"] if p["name"] == "statement")["prose"] += " (changed)"
    maps = _single_mapping(_build(example_catalog, new))["maps"]
    assert [(m["relationship"], m["sources"][0]["id-ref"]) for m in maps] == [("content-changed", control["id"])]


def test_added_and_removed_controls_go_to_the_gap_summaries(example_catalog):
    new = copy.deepcopy(example_catalog)
    controls = new["catalog"]["groups"][0]["controls"]
    removed_id = controls.pop(0)["id"]
    controls.append({"id": "ex-9.9", "title": "New", "parts": [{"id": "ex-9.9_smt", "name": "statement", "prose": "New."}]})
    mapping = _single_mapping(_build(example_catalog, new))
    assert mapping["source-gap-summary"]["unmapped-controls"] == [{"with-ids": [removed_id]}]
    assert mapping["target-gap-summary"]["unmapped-controls"] == [{"with-ids": ["ex-9.9"]}]


def test_stronger_modality_is_tightened_and_weaker_is_relaxed(example_catalog, example_rules):
    stronger = copy.deepcopy(example_rules)
    _rule(stronger, "ex-1.2")["modality"] = "binding"  # recommended (rank 2) -> binding (rank 1)
    tightened = _single_mapping(_build(example_catalog, example_catalog, example_rules, stronger))["maps"]
    relaxed = _single_mapping(_build(example_catalog, example_catalog, stronger, example_rules))["maps"]
    assert [(m["relationship"], m["sources"][0]["id-ref"]) for m in tightened] == [("tightened", "ex-1.2")]
    assert [(m["relationship"], m["sources"][0]["id-ref"]) for m in relaxed] == [("relaxed", "ex-1.2")]


def test_lifecycle_wins_over_strength(example_catalog, example_rules):
    new = copy.deepcopy(example_rules)
    rule = _rule(new, "ex-1.2")
    rule["modality"], rule["status"] = "binding", "retired"  # tightened AND withdrawn
    maps = _single_mapping(_build(example_catalog, example_catalog, example_rules, new))["maps"]
    assert [m["relationship"] for m in maps] == ["withdrawn"]


def test_two_sided_report_passes_both_validation_passes(example_catalog, example_rules, write_yaml):
    stronger = copy.deepcopy(example_rules)
    _rule(stronger, "ex-1.2")["modality"] = "binding"
    path = write_yaml("change.yaml", _build(example_catalog, example_catalog, example_rules, stronger))
    result = validate.validate_file(path, strict=True)
    assert result["nist_pass"]["status"] == "pass", result["nist_pass"]["errors"]
    assert result["o4r_pass"]["status"] == "pass", result["o4r_pass"]["errors"]
