# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Shared helpers: manifest reading, document loading, control traversal."""
import json

import o4r_common


def test_pinned_version_is_read_from_the_manifest(repo):
    manifest = json.loads((repo / "schemas" / "nist" / "manifest.json").read_text(encoding="utf-8"))
    assert o4r_common.pinned_oscal_version() == manifest["oscal_version"]


def test_pinned_version_is_none_when_the_manifest_is_unreadable(monkeypatch, tmp_path):
    monkeypatch.setattr(o4r_common, "MANIFEST", tmp_path / "missing.json")
    assert o4r_common.pinned_oscal_version() is None


def test_load_document_reads_yaml_and_json_as_utf8(tmp_path):
    doc = {"catalog": {"metadata": {"title": "Prüfung"}}}
    (tmp_path / "a.yaml").write_text("catalog:\n  metadata:\n    title: Prüfung\n", encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    assert o4r_common.load_document(tmp_path / "a.yaml") == doc
    assert o4r_common.load_document(tmp_path / "a.json") == doc


def test_iter_controls_walks_every_level_in_document_order():
    doc = {"catalog": {
        "groups": [{
            "controls": [{"id": "g-1", "controls": [{"id": "g-1.a"}]}],
            "groups": [{"controls": [{"id": "g-sub-1"}]}],
        }],
        "controls": [{"id": "root-1"}],
    }}
    assert [c["id"] for c in o4r_common.iter_controls(doc)] == ["g-1", "g-1.a", "g-sub-1", "root-1"]


def test_iter_controls_tolerates_empty_and_missing_sections():
    assert list(o4r_common.iter_controls({})) == []
    assert list(o4r_common.iter_controls({"catalog": {"groups": None, "controls": None}})) == []


def test_reference_catalog_controls_in_nested_groups_are_found(repo):
    doc = o4r_common.load_document(repo / "catalogs" / "bs-ki" / "de" / "bs-ki-de.yaml")
    assert len(list(o4r_common.iter_controls(doc))) == 42
