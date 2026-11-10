# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""A transition to `superseded` names its replacement and yields a valid report (#62)."""
import copy
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import change  # noqa: E402
import validate  # noqa: E402

RULES = REPO / "examples" / "rules"


def _load(name):
    return yaml.safe_load((RULES / name).read_text(encoding="utf-8"))


def _superseded_ruleset(old_rules):
    """ex-1.1 moves to a status whose binding is lifecycle=superseded, superseded-by=ex-1.2."""
    new_rules = copy.deepcopy(old_rules)
    rule_set = new_rules["rule-set"]
    rule_set["vocabularies"]["status"]["replaced"] = {
        "active": False, "lifecycle": "superseded", "superseded-by": "ex-1.2",
    }
    next(r for r in rule_set["rules"] if r["rule-id"] == "ex-1.1")["status"] = "replaced"
    return new_rules


def test_superseded_ruleset_is_schema_valid(tmp_path):
    """Guard: the test input itself is a valid rule-set (the binding carries superseded-by)."""
    path = tmp_path / "example-rules.yaml"
    path.write_text(yaml.safe_dump(_superseded_ruleset(_load("example-rules.yaml"))), encoding="utf-8")
    (tmp_path / "example-catalog.yaml").write_text(
        (RULES / "example-catalog.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    result = validate.validate_file(path, strict=True)
    assert result["o4r_pass"]["status"] == "pass", result["o4r_pass"]["errors"]


def test_superseded_change_carries_replacement_and_validates(tmp_path):
    catalog = _load("example-catalog.yaml")
    old_rules = _load("example-rules.yaml")
    report = change.build_mapping(
        catalog, catalog, old_rules, _superseded_ruleset(old_rules), "old", "new", "1.0", "1.0")

    maps = report["mapping-collection"]["mappings"][0]["maps"]
    superseded = [m for m in maps if m["relationship"] == "superseded"]
    assert [m["sources"][0]["id-ref"] for m in superseded] == ["ex-1.1"]
    assert {"name": "superseded-by", "value": "ex-1.2"} in superseded[0]["props"]

    path = tmp_path / "change.yaml"
    path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    result = validate.validate_file(path, strict=True)
    assert result["nist_pass"]["status"] == "pass", result["nist_pass"]["errors"]
    assert result["o4r_pass"]["status"] == "pass", result["o4r_pass"]["errors"]
