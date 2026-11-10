# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""generate_doc renders everything or fails loudly (#75)."""
import copy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import generate_doc  # noqa: E402

VERSIONED_CATALOGS = [
    "catalogs/bs-ki/de/bs-ki-de.yaml",
    "examples/rules/example-catalog.yaml",
    "examples/multilingual/example-de.yaml",
    "examples/multilingual/example-fr.yaml",
    "examples/multilingual/example-multilingual-parts.yaml",
]


def _full_catalog() -> dict:
    """A catalog that uses every element the renderer handles, each with a unique value."""
    return {
        "uuid": "11111111-1111-4111-8111-111111111111",
        "metadata": {
            "title": "META-TITLE", "version": "META-VERSION", "published": "META-PUBLISHED",
            "last-modified": "META-MODIFIED", "oscal-version": "META-OSCAL", "remarks": "META-REMARKS",
            "links": [{"href": "META-LINK-HREF", "rel": "META-LINK-REL", "text": "META-LINK-TEXT"}],
            "props": [
                {"name": "country", "value": "META-COUNTRY"},
                {"name": "language", "value": "META-LANG-1", "remarks": "META-LANG-REMARKS"},
                {"name": "language", "value": "META-LANG-2"},
                {"name": "source-document", "value": "META-SRC-DOC"},
                {"name": "source-url", "value": "META-SRC-URL"},
                {"name": "meta-custom", "value": "META-CUSTOM", "ns": "META-NS"},
            ],
        },
        "params": [{"id": "CAT-PARAM", "label": "CAT-PARAM-LABEL"}],
        "groups": [{
            "id": "t-1", "title": "GROUP-TITLE",
            "props": [{"name": "group-prop", "value": "GROUP-PROP"}],
            "parts": [{"name": "overview", "prose": "GROUP-PROSE"}],
            "params": [{"id": "GROUP-PARAM", "values": ["GROUP-PARAM-VALUE"]}],
            "links": [{"href": "GROUP-LINK"}],
            "controls": [{
                "id": "t-1.1", "title": "CONTROL-TITLE",
                "props": [
                    {"name": "source-chapter", "value": "1.1"},
                    {"name": "applicability", "class": "APP-CLASS-A", "value": "APP-VALUE-A", "remarks": "APP-REM-A"},
                    {"name": "applicability", "class": "APP-CLASS-B", "value": "APP-VALUE-B"},
                    {"name": "source-document", "value": "CTRL-SRC-DOC", "remarks": "CTRL-SRC-REM"},
                    {"name": "ctrl-custom", "value": "CTRL-CUSTOM", "class": "CTRL-CUSTOM-CLASS"},
                ],
                "params": [{
                    "id": "CTRL-PARAM", "label": "CTRL-PARAM-LABEL", "usage": "CTRL-PARAM-USAGE",
                    "select": {"how-many": "one", "choice": ["CHOICE-A", "CHOICE-B"]},
                    "remarks": "CTRL-PARAM-REMARKS",
                }],
                "links": [{"href": "CTRL-LINK-HREF", "rel": "decision-logic", "text": "CTRL-LINK-TEXT"}],
                "parts": [
                    {"id": "t-1.1_smt", "name": "statement", "prose": "STATEMENT-DE",
                     "props": [{"name": "language", "value": "de"}],
                     "parts": [{"name": "item", "prose": "NESTED-ITEM",
                                "parts": [{"name": "item", "title": "DEEP-TITLE", "prose": "DEEP-ITEM"}]}]},
                    {"name": "statement", "prose": "STATEMENT-FR", "props": [{"name": "language", "value": "fr"}]},
                    {"name": "guidance", "title": "GUIDANCE-TITLE", "prose": "GUIDANCE-PROSE",
                     "links": [{"href": "PART-LINK"}], "props": [{"name": "part-prop", "value": "PART-PROP"}]},
                    {"name": "assessment-objective", "prose": "OBJECTIVE-PROSE"},
                ],
                "controls": [{
                    "id": "t-1.1.a", "title": "CHILD-TITLE",
                    "parts": [{"name": "statement", "prose": "CHILD-PROSE"}],
                }],
            }],
            "groups": [{
                "id": "t-1-sub", "title": "SUBGROUP-TITLE",
                "controls": [{"id": "t-1.2", "title": "SUB-CONTROL-TITLE",
                              "parts": [{"name": "statement", "prose": "SUB-CONTROL-PROSE"}]}],
            }],
        }],
        "controls": [{"id": "t-9", "title": "ROOT-CONTROL-TITLE",
                      "parts": [{"name": "statement", "prose": "ROOT-CONTROL-PROSE"}]}],
        "back-matter": {"resources": [{
            "uuid": "22222222-2222-4222-8222-222222222222", "title": "RES-TITLE",
            "description": "RES-DESCRIPTION", "remarks": "RES-REMARKS",
            "props": [{"name": "type", "value": "RES-PROP"}],
            "rlinks": [{"href": "RES-HREF", "media-type": "RES-MEDIA"}],
            "citation": {"text": "RES-CITATION"},
        }]},
    }


def _leaf_strings(obj):
    if isinstance(obj, dict):
        for value in obj.values():
            yield from _leaf_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _leaf_strings(value)
    elif isinstance(obj, str):
        yield obj


def _control(catalog, cid="t-1.1"):
    return next(c for c in catalog["groups"][0]["controls"] if c["id"] == cid)


def _problems(findings):
    return [f"{f['location']}: {f['problem']}" for f in findings]


# --- completeness -------------------------------------------------------------

def test_every_value_of_every_handled_element_is_rendered():
    catalog = _full_catalog()
    markdown = generate_doc.generate_markdown(catalog, "cat.yaml")
    not_rendered = {"11111111-1111-4111-8111-111111111111", "t-1.1_smt"}  # catalog uuid, part id
    structural = {"statement", "guidance", "item", "country", "language", "source-document", "source-url",
                  "source-chapter", "applicability", "t-1", "t-1-sub"}
    missing = [s for s in _leaf_strings(catalog)
               if s not in not_rendered and s not in structural and s not in markdown]
    assert missing == []
    assert generate_doc.verify_roundtrip(catalog, markdown) == []


@pytest.mark.parametrize("relpath", VERSIONED_CATALOGS)
def test_versioned_catalogs_verify(relpath):
    catalog = yaml.safe_load((REPO / relpath).read_text(encoding="utf-8"))["catalog"]
    markdown = generate_doc.generate_markdown(catalog, relpath)
    assert generate_doc.verify_roundtrip(catalog, markdown) == []


def test_reference_catalog_back_matter_is_rendered():
    catalog = yaml.safe_load((REPO / VERSIONED_CATALOGS[0]).read_text(encoding="utf-8"))["catalog"]
    markdown = generate_doc.generate_markdown(catalog)
    resources = catalog["back-matter"]["resources"]
    assert len(resources) == 3
    assert all(r["title"] in markdown and r["rlinks"][0]["href"] in markdown for r in resources)


@pytest.mark.parametrize("mutate, expected", [
    (lambda c: c["metadata"].update(roles=[{"id": "owner", "title": "Owner"}]), "metadata: `roles` is not rendered"),
    (lambda c: c.update(extra="x"), "catalog: `extra` is not rendered"),
    (lambda c: c["groups"][0].update({"class": "x"}), "t-1: `class` is not rendered"),
    (lambda c: _control(c).update({"class": "x"}), "t-1/t-1.1: `class` is not rendered"),
    (lambda c: _control(c)["parts"][0].update(ns="x"), "t-1/t-1.1/part `statement`: `ns` is not rendered"),
    (lambda c: _control(c)["params"][0].update(constraints=[{"description": "x"}]),
     "t-1/t-1.1/param `CTRL-PARAM`: `constraints` is not rendered"),
    (lambda c: _control(c)["links"][0].update({"media-type": "x"}),
     "t-1/t-1.1/link `CTRL-LINK-HREF`: `media-type` is not rendered"),
    (lambda c: _control(c)["props"][0].update(uuid="x"),
     "t-1/t-1.1/prop `source-chapter`: `uuid` is not rendered"),
    (lambda c: c["back-matter"]["resources"][0].update(base64={"value": "x"}),
     "back-matter/resource `22222222-2222-4222-8222-222222222222`: `base64` is not rendered"),
])
def test_unknown_element_fails_verification_by_name(mutate, expected):
    catalog = _full_catalog()
    mutate(catalog)
    findings = generate_doc.verify_roundtrip(catalog, generate_doc.generate_markdown(catalog))
    assert _problems(findings) == [expected]


def test_prop_with_more_than_its_layout_shows_is_listed_in_the_generic_table():
    markdown = generate_doc.generate_markdown(_full_catalog())
    assert "| language | META-LANG-1 |  |  | META-LANG-REMARKS |" in markdown   # remarks kept
    assert "| language | META-LANG-2 |  |  |  |" in markdown                    # second occurrence kept


# --- fidelity -----------------------------------------------------------------

def test_statement_parts_carry_their_language_label():
    markdown = generate_doc.generate_markdown(_full_catalog())
    assert markdown.index("> Sprache: `de`") < markdown.index("STATEMENT-DE")
    assert markdown.index("STATEMENT-DE") < markdown.index("> Sprache: `fr`") < markdown.index("STATEMENT-FR")


def test_prose_swapped_between_two_controls_is_detected():
    catalog = _full_catalog()
    markdown = generate_doc.generate_markdown(catalog)
    swapped = (markdown.replace("CHILD-PROSE", "\0").replace("SUB-CONTROL-PROSE", "CHILD-PROSE")
               .replace("\0", "SUB-CONTROL-PROSE"))
    findings = generate_doc.verify_roundtrip(catalog, swapped)
    assert sorted(f["control_id"] for f in findings) == ["t-1.1.a", "t-1.2"]
    assert all("prose not found verbatim in its own section" in f["problem"] for f in findings)


def test_identical_prose_in_two_parts_must_be_rendered_twice():
    catalog = _full_catalog()
    _control(catalog)["parts"][1]["prose"] = "STATEMENT-DE"
    markdown = generate_doc.generate_markdown(catalog)
    assert generate_doc.verify_roundtrip(catalog, markdown) == []
    once = markdown.replace("STATEMENT-DE", "\0", 1).replace("STATEMENT-DE", "").replace("\0", "STATEMENT-DE")
    assert len(generate_doc.verify_roundtrip(catalog, once)) == 1


@pytest.mark.parametrize("old, new", [
    ("| APP-CLASS-A | APP-VALUE-A | APP-REM-A |", "| APP-CLASS-A | CHANGED | APP-REM-A |"),
    ("| APP-CLASS-B | APP-VALUE-B |  |\n", ""),
])
def test_applicability_table_is_checked_against_the_props(old, new):
    catalog = _full_catalog()
    markdown = generate_doc.generate_markdown(catalog)
    assert old in markdown
    findings = generate_doc.verify_roundtrip(catalog, markdown.replace(old, new))
    assert _problems(findings) == ["t-1/t-1.1: applicability table does not match the applicability props"]


def test_applicability_values_with_table_syntax_round_trip():
    catalog = _full_catalog()
    _control(catalog)["props"][1].update(value="a | b", remarks="line 1\nline 2 \\ end")
    markdown = generate_doc.generate_markdown(catalog)
    assert generate_doc.verify_roundtrip(catalog, markdown) == []


def test_changed_title_is_detected():
    catalog = _full_catalog()
    markdown = generate_doc.generate_markdown(catalog).replace("CHILD-TITLE", "OTHER")
    assert _problems(generate_doc.verify_roundtrip(catalog, markdown)) == [
        "t-1/t-1.1/t-1.1.a: title not found verbatim in its own section"]


def test_duplicate_control_id_is_reported():
    catalog = _full_catalog()
    catalog["controls"].append(copy.deepcopy(catalog["controls"][0]))
    findings = generate_doc.verify_roundtrip(catalog, generate_doc.generate_markdown(catalog))
    assert any("rendered more than once" in f["problem"] and f["control_id"] == "t-9" for f in findings)


# --- CLI ----------------------------------------------------------------------

def _cli(*args):
    return subprocess.run([sys.executable, str(REPO / "tools" / "generate_doc.py"), *args],
                          capture_output=True, text=True)


def test_cli_default_output_matches_the_help_text(tmp_path):
    src = tmp_path / "cat.yaml"
    src.write_text(yaml.safe_dump({"catalog": _full_catalog()}, allow_unicode=True), encoding="utf-8")
    result = _cli("--verify", "--quiet", str(src))
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "_rendered" / "cat.md").exists()
    assert "_rendered/<name>.md" in _cli("--help").stdout
    assert "generated.md" not in _cli("--help").stdout


def test_cli_verify_fails_and_names_the_element(tmp_path):
    catalog = _full_catalog()
    catalog["metadata"]["parties"] = [{"uuid": "x", "type": "organization"}]
    src = tmp_path / "cat.yaml"
    src.write_text(yaml.safe_dump({"catalog": catalog}, allow_unicode=True), encoding="utf-8")
    result = _cli("--verify", "--quiet", str(src))
    assert result.returncode == 1
    assert "metadata: `parties` is not rendered" in result.stdout
