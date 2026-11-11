# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Tooling hygiene (#83): strict YAML loading, unreadable input, script headers, ADR sync."""
import subprocess
import sys

import pytest
import yaml

import check_arc42_adr_sync as adr_sync
import o4r_common
import validate

# --- YAML 1.1 traps -------------------------------------------------------------

@pytest.mark.parametrize("word", ["no", "yes", "on", "off", "No", "YES", "y", "n"])
def test_yaml_1_1_boolean_words_stay_strings(word):
    assert o4r_common.load_text(f"value: {word}\n") == {"value": word}


@pytest.mark.parametrize("text, expected", [("true", True), ("false", False), ("True", True), ("FALSE", False)])
def test_true_and_false_are_booleans(text, expected):
    assert o4r_common.load_text(f"value: {text}\n") == {"value": expected}


@pytest.mark.parametrize("text", ["1.10", "2.50", "-1.20", "10.00"])
def test_decimal_that_would_lose_a_trailing_zero_is_rejected(text):
    with pytest.raises(o4r_common.AmbiguousScalarError, match=r"cat\.yaml: line 2: unquoted value"):
        o4r_common.load_text(f"a: 1\nversion: {text}\n", source="cat.yaml")


@pytest.mark.parametrize("text, expected", [
    ("1.5", 1.5), ("30", 30), ("0.25", 0.25), ("'1.10'", "1.10"), ('"1.10"', "1.10"), ("1.10.2", "1.10.2")])
def test_other_scalars_load_as_before(text, expected):
    assert o4r_common.load_text(f"value: {text}\n") == {"value": expected}


def test_strict_loader_is_still_a_safe_loader():
    with pytest.raises(yaml.YAMLError):
        o4r_common.load_text("value: !!python/object/apply:os.system ['true']\n")


def test_versioned_artifacts_load_unchanged(repo):
    files = subprocess.run(["git", "ls-files", "*.yaml"], cwd=repo, capture_output=True, text=True).stdout.split()
    assert files
    for rel in files:
        path = repo / rel
        assert o4r_common.load_document(path) == yaml.safe_load(path.read_text(encoding="utf-8")), rel


# --- unreadable input is a validation error, not a traceback --------------------

@pytest.mark.parametrize("content, expected", [
    ("", "empty document"),
    ("# only a comment\n", "empty document"),
    ("- a\n- b\n", "top-level list"),
    ("just a string\n", "top-level str"),
    ("catalog: [unclosed\n", "cannot read document"),
    ("catalog:\n  metadata:\n    version: 1.10\n", "unquoted value 1.10"),
])
def test_unreadable_yaml_is_reported(tmp_path, content, expected):
    path = tmp_path / "broken.yaml"
    path.write_text(content, encoding="utf-8")
    result = validate.validate_file(path, strict=True)
    assert result["ok"] is False
    assert result["nist_pass"]["status"] == "error"
    assert expected in result["nist_pass"]["errors"][0]


def test_invalid_json_is_reported(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    result = validate.validate_file(path, strict=True)
    assert result["ok"] is False and "cannot read document" in result["nist_pass"]["errors"][0]


def test_cli_reports_an_empty_file_without_traceback(repo, tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    result = subprocess.run([sys.executable, "tools/validate.py", "--strict", "--report", "none", str(path)],
                            cwd=repo, capture_output=True, text=True)
    assert result.returncode == 1
    assert "empty document" in result.stdout
    assert "Traceback" not in result.stderr


def test_change_cli_reports_an_ambiguous_version_without_traceback(repo, example_catalog, tmp_path):
    good = tmp_path / "good.yaml"
    good.write_text(yaml.safe_dump(example_catalog), encoding="utf-8")
    bad = tmp_path / "bad.yaml"
    bad.write_text("catalog:\n  metadata:\n    version: 1.10\n", encoding="utf-8")
    result = subprocess.run([sys.executable, "tools/change.py", "--from", str(good), "--to", str(bad), "--summary"],
                            cwd=repo, capture_output=True, text=True)
    assert result.returncode != 0
    assert "unquoted value 1.10" in result.stderr and "Traceback" not in result.stderr


# --- script headers ---------------------------------------------------------------

def test_every_tool_starts_with_a_shebang_and_carries_spdx(repo):
    for path in sorted((repo / "tools").glob("*.py")):
        lines = path.read_text(encoding="utf-8").splitlines()
        head = "\n".join(lines[:4])
        # (split so that REUSE does not read this line as a licence tag)
        assert "SPDX-License-" + "Identifier: Apache-2.0" in head, path.name
        if "#!" in head:
            assert lines[0].startswith("#!"), f"{path.name}: the shebang must be line 1"


# --- arc42 / ADR sync -------------------------------------------------------------

def _adr(tmp_path, name, status):
    (tmp_path / name).write_text(f"# {name}\n\n**Status:** {status}\n", encoding="utf-8")


ARC42 = """\
ADR-099 is mentioned in the text only.

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Embedded | Accepted | - |
| [ADR-005](adr/ADR-005-x.md) | Linked | Accepted (amended by ADR-014) | 2026-06-25 |
| [ADR-007](adr/ADR-007-x.md) | Tooling | Proposed | 2026-08-03 |
"""


def test_adr_sync_passes_when_row_and_status_keyword_match(tmp_path):
    _adr(tmp_path, "ADR-005-x.md", "Accepted (amended, see note below)")
    _adr(tmp_path, "ADR-007-x.md", "Proposed")
    checked, problems = adr_sync.find_problems(tmp_path, ARC42)
    assert checked == ["ADR-005-x.md", "ADR-007-x.md"] and problems == []


def test_adr_sync_reports_a_status_difference(tmp_path):
    _adr(tmp_path, "ADR-007-x.md", "Accepted")
    _, problems = adr_sync.find_problems(tmp_path, ARC42)
    assert problems == ["ADR-007-x.md: status differs: ADR file says 'Accepted', arc42.md table says 'Proposed'"]


def test_adr_sync_requires_a_table_row_not_a_mention(tmp_path):
    _adr(tmp_path, "ADR-099-x.md", "Accepted")
    _, problems = adr_sync.find_problems(tmp_path, ARC42)
    assert problems == ["ADR-099-x.md: no row in the master table of arc42.md §9"]


def test_adr_sync_reports_a_missing_status_line(tmp_path):
    (tmp_path / "ADR-007-x.md").write_text("# no status\n", encoding="utf-8")
    _, problems = adr_sync.find_problems(tmp_path, ARC42)
    assert problems == ["ADR-007-x.md: no '**Status:**' line in the ADR file"]
