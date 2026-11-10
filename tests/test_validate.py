# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Validator contracts that are enforced today (ADR-013, ADR-018 §10)."""
import pytest

import validate

# Versioned artifacts that pass both passes on `main`. The examples that do not yet
# pass --strict are tracked in #68 and are deliberately not listed here.
STRICT_CLEAN = [
    "catalogs/bs-ki/de/bs-ki-de.yaml",
    "examples/rules/example-catalog.yaml",
    "examples/rules/example-rules.yaml",
    "examples/change/example-change.yaml",
    "examples/profiles/company-over-bsi-grundschutz.profile.yaml",
]


@pytest.mark.parametrize("relpath", STRICT_CLEAN)
def test_versioned_artifact_passes_strict(repo, relpath):
    result = validate.validate_file(repo / relpath, strict=True)
    assert result["nist_pass"]["status"] in ("pass", "skipped"), result["nist_pass"]["errors"]
    assert result["o4r_pass"]["status"] == "pass", result["o4r_pass"]["errors"]
    assert result["ok"] is True


def test_nist_violation_fails(example_catalog, write_yaml):
    del example_catalog["catalog"]["metadata"]["title"]
    result = validate.validate_file(write_yaml("c.yaml", example_catalog), strict=False)
    assert result["nist_pass"]["status"] == "fail"
    assert result["ok"] is False


def test_pattern_violation_fails(example_catalog, write_yaml):
    example_catalog["catalog"]["uuid"] = "not-a-uuid"
    result = validate.validate_file(write_yaml("c.yaml", example_catalog), strict=False)
    assert result["nist_pass"]["status"] == "fail"
    assert any("does not match" in e for e in result["nist_pass"]["errors"])


def test_unknown_root_is_an_error(write_yaml):
    result = validate.validate_file(write_yaml("x.yaml", {"something-else": {}}), strict=True)
    assert result["nist_pass"]["status"] == "error"
    assert result["ok"] is False


def test_catalog_and_rule_set_in_one_document_is_rejected(example_catalog, example_rules, write_yaml):
    mixed = {**example_catalog, **example_rules}
    result = validate.validate_file(write_yaml("mixed.yaml", mixed), strict=True)
    assert result["ok"] is False
    assert any("ADR-018" in e for e in result["nist_pass"]["errors"])


def test_o4r_pass_runs_only_with_strict(repo):
    result = validate.validate_file(repo / "examples/rules/example-catalog.yaml", strict=False)
    assert result["o4r_pass"]["status"] == "not-run"
    assert result["ok"] is True


def test_rule_set_without_strict_is_not_a_pass(repo):
    result = validate.validate_file(repo / "examples/rules/example-rules.yaml", strict=False)
    assert result["nist_pass"]["status"] == "skipped"
    assert result["ok"] is False


def test_oscal_version_mismatch_is_reported_not_enforced(example_catalog, write_yaml):
    example_catalog["catalog"]["metadata"]["oscal-version"] = "1.1.2"
    result = validate.validate_file(write_yaml("c.yaml", example_catalog), strict=False)
    assert result["oscal_version"]["match"] is False
    assert "mismatch" in result["oscal_version"]["note"]
    assert result["ok"] is True


def test_rule_referencing_an_unknown_control_fails(example_catalog, example_rules, write_yaml):
    write_yaml("example-catalog.yaml", example_catalog)
    example_rules["rule-set"]["rules"][0]["control-id"] = "does-not-exist"
    result = validate.validate_file(write_yaml("example-rules.yaml", example_rules), strict=True)
    assert result["o4r_pass"]["status"] == "fail"
    assert any("does-not-exist" in e for e in result["o4r_pass"]["errors"])


def test_reports_are_written_beside_the_artifact(example_catalog, write_yaml):
    path = write_yaml("c.yaml", example_catalog)
    written = validate.write_reports(validate.validate_file(path, strict=True), strict=True)
    assert all(p.parent == path.parent and p.exists() for p in written)
    assert (path.parent / "c.validation.md") in written
