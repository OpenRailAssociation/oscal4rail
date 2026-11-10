#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Consolidated OSCAL4Rail validator (ADR-013).

Two-pass validation of an OSCAL4Rail artifact:

  Pass 1 (always)   NIST OSCAL base schema, selected by detected model.
  Pass 2 (--strict) additive OSCAL4Rail constraints, auto-mapped by artifact
                    subtype (catalog -> catalog constraints, profile -> cascade
                    constraints, rule-set -> rules, change report -> change
                    constraints). A mapping-collection is a change report only
                    if it carries the `o4r-artifact: change-report` marker;
                    an ordinary control mapping has no O4R schema. Subtypes
                    without an O4R schema are SKIPPED and the skip is recorded
                    in the report (no silent drift). --foreign declares OSCAL
                    that is not an OSCAL4Rail artifact (e.g. an upstream
                    catalog): NIST pass only, O4R skip reported.

Both passes evaluate patterns with Unicode property classes (the OSCAL token
datatype: ids, prop names) and the formats uri, uri-reference, date-time, date
and email. This needs the declared dependencies (pyproject.toml). A constraint
that cannot be evaluated because a module is missing is counted and shown in
the summary and the report; it is never skipped silently.

Additionally compares the artifact's `oscal-version` against the pinned tag
(schemas/nist/manifest.json, ADR-008). Per ADR-013 this is REPORTED, not
enforced: a mismatch is a report finding and does not fail the run.

A full run report is written beside the validated file in both Markdown
(human-readable) and JSON (machine-/agent-readable):
  <file>.validation.md  and  <file>.validation.json

Exit code: 0 if every file passes; non-zero if any NIST pass fails, or any
O4R pass fails while --strict is set. Skips and oscal-version mismatches do
NOT fail the run (see ADR-013; --require-o4r is deferred, issue #42).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft7Validator

from o4r_common import NIST_DIR, REPO_ROOT, iter_controls, pinned_oscal_version
from o4r_common import load_document as load_data

O4R_DIR = REPO_ROOT / "schemas" / "oscal4rail"

# OSCAL root element -> NIST schema file
NIST_SCHEMA_MAP = {
    "catalog": "oscal-catalog.json",
    "profile": "oscal-profile.json",
    "assessment-results": "oscal-assessment-results.json",
    "component-definition": "oscal-component-definition.json",
    "mapping-collection": "oscal-mapping.json",
}

# Artifact subtype -> additive OSCAL4Rail constraint schema (two-pass, ADR-013).
# The subtype is the detected model, refined where one NIST model carries more
# than one kind of OSCAL4Rail artifact (see `detect_subtype`). Subtypes absent
# from this map have no O4R schema yet -> skip + report.
O4R_SCHEMA_MAP = {
    "catalog": "oscal4rail-catalog-constraints.schema.json",
    "profile": "oscal4rail-profile-cascade-constraints.schema.json",
    "rule-set": "oscal4rail-rules.schema.json",
    "change-report": "oscal4rail-change.schema.json",
}

# A NIST mapping-collection is an OSCAL4Rail change report (ADR-019) if one of its
# mappings carries this marker prop; otherwise it is an ordinary control mapping.
CHANGE_REPORT_MARKER = {"name": "o4r-artifact", "value": "change-report"}

# OSCAL4Rail-native roots that have NO NIST base schema (NIST pass 1 is skipped
# for them; they are validated by the O4R schema alone). ADR-014/ADR-018.
O4R_NATIVE_ROOTS = {"rule-set"}


# Patterns with Unicode property classes (\p{L}, \p{N}) are not supported by the
# standard `re` module. In the pinned NIST schemas that is the OSCAL token
# datatype, i.e. every id, prop name and token. They are evaluated with the
# third-party `regex` module. If it is missing, the constraint cannot be checked:
# it is counted and reported, never skipped silently (ADR-013).
try:
    import regex as _regex
except ImportError:  # pragma: no cover - exercised via monkeypatch in the tests
    _regex = None


def _make_validator(skipped: dict[str, int]):
    """Build the validator class for one schema run.

    `skipped` collects every constraint that could not be evaluated, keyed by a
    readable reason, with the number of values it would have applied to.
    """
    def _skip(reason: str) -> None:
        skipped[reason] = skipped.get(reason, 0) + 1

    def _pattern(validator, patrn, instance, schema):
        if not validator.is_type(instance, "string"):
            return
        if r"\p{" in patrn:
            if _regex is None:
                _skip("Unicode-class pattern not evaluated (Python module 'regex' is not installed)")
                return
            matched = _regex.search(patrn, instance)
        else:
            matched = re.search(patrn, instance)
        if not matched:
            yield jsonschema.ValidationError(f"{instance!r} does not match {patrn!r}")

    def _format(validator, fmt, instance, schema):
        checker = validator.format_checker
        if fmt not in checker.checkers:
            _skip(f"format '{fmt}' not checked (no checker installed)")
            return
        try:
            checker.check(instance, fmt)
        except jsonschema.exceptions.FormatError as exc:
            yield jsonschema.ValidationError(exc.message, cause=exc.cause)

    return jsonschema.validators.extend(Draft7Validator, {"pattern": _pattern, "format": _format})


def detect_model(data: dict) -> str | None:
    for key in NIST_SCHEMA_MAP:
        if key in data:
            return key
    for key in O4R_NATIVE_ROOTS:
        if key in data:
            return key
    return None


def detect_subtype(data: dict, model: str) -> str:
    """Refine the model to the artifact subtype that selects the O4R constraints.

    mapping-collection: `change-report` if any mapping carries the marker prop
    (`o4r-artifact: change-report`), else `control-mapping`. Every other model is
    its own subtype.
    """
    if model != "mapping-collection":
        return model
    root = data.get(model)
    mappings = root.get("mappings") if isinstance(root, dict) else None
    for mapping in mappings if isinstance(mappings, list) else []:
        props = mapping.get("props") if isinstance(mapping, dict) else None
        for prop in props if isinstance(props, list) else []:
            if isinstance(prop, dict) and all(prop.get(k) == v for k, v in CHANGE_REPORT_MARKER.items()):
                return "change-report"
    return "control-mapping"


def separation_violation(data: dict) -> str | None:
    """ADR-018 §10: a document must not mix a catalog/profile and a rule-set."""
    nist_roots = [k for k in NIST_SCHEMA_MAP if k in data]
    native_roots = [k for k in O4R_NATIVE_ROOTS if k in data]
    if nist_roots and native_roots:
        return (
            f"document mixes NIST root(s) {nist_roots} with O4R-native root(s) "
            f"{native_roots}; catalog and rule-set MUST be separate files (ADR-018 §10)"
        )
    return None


def artifact_oscal_version(data: dict, model: str) -> str | None:
    root = data.get(model)
    if isinstance(root, dict):
        meta = root.get("metadata")
        if isinstance(meta, dict):
            v = meta.get("oscal-version")
            return str(v) if v is not None else None
    return None


def _load_catalog_controls(catalog_path: Path) -> tuple[set[str], str | None, str | None]:
    """Return (set of control ids, catalog version, catalog uuid) for referential checks."""
    data = load_data(catalog_path)
    cat = data.get("catalog", {})
    version = (cat.get("metadata") or {}).get("version")
    cat_uuid = cat.get("uuid")
    ids = {c["id"] for c in iter_controls(data) if "id" in c}
    return ids, (str(version) if version is not None else None), (str(cat_uuid) if cat_uuid is not None else None)


def catalog_consistency(data: dict) -> list[str]:
    """Catalog invariants that JSON Schema cannot express (catalog-format.md section 2).

    - Control ids are unique across the whole catalog, at any depth. The id is
      the stable identity every diff, rule and mapping refers to.
    - The chapter encoded in a control id equals the `source-chapter` prop of the
      same control: `<regulation>-<source-chapter>[-<context>]`. This is the
      cross-check that ids were derived from chapters, not from pages or by hand.
    """
    errors: list[str] = []
    seen: set[str] = set()
    reported: set[str] = set()
    for control in iter_controls(data):
        cid = control.get("id")
        if not isinstance(cid, str):
            continue  # missing/invalid id is a schema error
        if cid in seen and cid not in reported:
            errors.append(f"[control {cid}] duplicate control id; ids MUST be unique within a catalog")
            reported.add(cid)
        seen.add(cid)
        props = control.get("props")
        for prop in props if isinstance(props, list) else []:
            if not isinstance(prop, dict) or prop.get("name") != "source-chapter":
                continue
            chapter = str(prop.get("value", ""))
            encoded = re.fullmatch(
                rf"[a-z0-9]+(?:-[a-z0-9]+)*-{re.escape(chapter)}(?:-[a-z0-9-]+)?", cid)
            if not chapter or not encoded:
                errors.append(
                    f"[control {cid}] id does not encode source-chapter '{chapter}'; expected "
                    f"'<regulation>-{chapter}[-<context>]' (catalog-format.md section 2)")
    return errors


# A well-formed ISO 639 language code: two letters (639-1) or three (639-2/-3).
_ISO_639_SHAPE = re.compile(r"[a-z]{2,3}")


def reference_language_violations(data: dict) -> list[str]:
    """Value range of the optional `reference-language` metadata prop (ADR-017, points 3 and 4).

    Each value is a well-formed ISO 639 code or the sentinel `all`; `all` is not
    mixed with codes. The check is on the form of the code: whether a well-formed
    code is assigned, and whether the regulation exists in that language, is the
    owner's declaration and is not decided here.
    """
    catalog = data.get("catalog")
    meta = catalog.get("metadata") if isinstance(catalog, dict) else None
    props = meta.get("props") if isinstance(meta, dict) else None
    values = [p.get("value") for p in props if isinstance(p, dict) and p.get("name") == "reference-language"] \
        if isinstance(props, list) else []
    errors = []
    for value in values:
        if value != "all" and not (isinstance(value, str) and _ISO_639_SHAPE.fullmatch(value)):
            errors.append(
                f"[catalog.metadata.props] reference-language '{value}' is neither a well-formed "
                "ISO 639 code (two or three lowercase letters) nor 'all' (ADR-017)")
    if "all" in values and len(values) > 1:
        errors.append(
            "[catalog.metadata.props] reference-language 'all' MUST NOT be combined with other "
            f"reference-language values (found: {', '.join(repr(v) for v in values)}) (ADR-017)")
    return errors


def ruleset_consistency(data: dict, rule_set_path: Path) -> list[str]:
    """ADR-018 §10 cross-artifact contract, enforced as errors."""
    errs: list[str] = []
    rs = data.get("rule-set", {})
    meta = rs.get("metadata", {}) or {}
    voc = rs.get("vocabularies", {}) or {}
    mod, st = set(voc.get("modality", {})), set(voc.get("status", {}))
    enf = set(voc.get("enforcement", {}))
    rule_ids = {r.get("rule-id") for r in rs.get("rules", []) or []}

    # vocab + group-member referential integrity (within the rule-set)
    for r in rs.get("rules", []) or []:
        rid = r.get("rule-id", "?")
        if r.get("modality") not in mod:
            errs.append(f"rule {rid}: modality '{r.get('modality')}' not declared in vocabularies.modality")
        if r.get("status") not in st:
            errs.append(f"rule {rid}: status '{r.get('status')}' not declared in vocabularies.status")
        for e in r.get("enforcement", []) or []:
            if e not in enf:
                errs.append(f"rule {rid}: enforcement '{e}' not declared in vocabularies.enforcement")
    for g in rs.get("rule-groups", []) or []:
        for m in g.get("members", []) or []:
            if m not in rule_ids:
                errs.append(f"rule-group {g.get('id','?')}: member '{m}' is not a rule-id")

    # cross-artifact: resolve catalog-ref, identity, control-id integrity, version equality
    cref = rs.get("catalog-ref", {}) or {}
    href = cref.get("href")
    if not href:
        errs.append("catalog-ref.href missing; cannot verify control-id integrity or version equality")
        return errs
    cat_path = (rule_set_path.parent / href).resolve()
    if not cat_path.exists():
        errs.append(f"catalog-ref.href does not resolve to a file: {href}")
        return errs
    try:
        control_ids, cat_version, cat_uuid = _load_catalog_controls(cat_path)
    except Exception as exc:  # noqa: BLE001 - report, do not crash
        errs.append(f"cannot read catalog '{href}': {exc}")
        return errs
    # identity: catalog-ref.catalog-uuid must match the catalog's own uuid
    ref_uuid = cref.get("catalog-uuid")
    if ref_uuid and cat_uuid and str(ref_uuid) != str(cat_uuid):
        errs.append(
            f"catalog-ref.catalog-uuid '{ref_uuid}' != catalog uuid '{cat_uuid}' "
            "(identity mismatch — the rule-set points at a different catalog than it resolves)"
        )
    for r in rs.get("rules", []) or []:
        cid = r.get("control-id")
        if cid not in control_ids:
            errs.append(f"rule {r.get('rule-id','?')}: control-id '{cid}' not found in catalog '{href}'")
    rs_version = meta.get("version")
    if cat_version is not None and str(rs_version) != str(cat_version):
        errs.append(
            f"version mismatch: rule-set {rs_version} != catalog {cat_version} "
            "(must be equal — ADR-014/ADR-018 §10)"
        )
    return errs


def _run_schema(schema_path: Path, data: dict) -> tuple[list[str], dict[str, int]]:
    """Validate `data` against one schema.

    Returns (error messages, constraints that could not be evaluated). The second
    value maps a reason to the number of values the constraint applied to.
    """
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    skipped: dict[str, int] = {}
    validator = _make_validator(skipped)(schema, format_checker=Draft7Validator.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path])
    out = []
    for e in errors:
        # An anyOf/oneOf failure only says "not valid under any of the given
        # schemas" about a whole subtree. Report the most relevant underlying
        # error instead, so the message names the offending value.
        cause = jsonschema.exceptions.best_match([e]) if e.context else e
        loc = ".".join(str(p) for p in cause.absolute_path) or "(root)"
        out.append(f"[{loc}] {cause.message}")
    return out, skipped


def validate_file(path: Path, strict: bool, foreign: bool = False) -> dict:
    """Validate one file, return a structured result (the report record).

    `foreign` declares the artifact as OSCAL that is not an OSCAL4Rail artifact
    (e.g. an upstream catalog the cascade references). It is then validated
    against the NIST schema only; the O4R pass is skipped and the skip reported.
    It has no effect on OSCAL4Rail-native roots (rule-set).
    """
    result: dict = {
        "file": str(path),
        "model": None,
        "subtype": None,
        "nist_pass": {"status": "error", "schema": None, "errors": [], "skipped_constraints": {}},
        "o4r_pass": {"status": "skipped", "schema": None, "errors": [], "reason": None,
                     "skipped_constraints": {}},
        "oscal_version": {"artifact": None, "pinned": pinned_oscal_version(), "match": None, "note": None},
        "ok": False,
    }

    data = load_data(path)

    # ADR-018 §10: a document must not mix a catalog/profile and a rule-set.
    sep = separation_violation(data)
    if sep is not None:
        result["nist_pass"]["status"] = "error"
        result["nist_pass"]["errors"] = [sep]
        return result

    model = detect_model(data)
    result["model"] = model
    subtype = detect_subtype(data, model) if model is not None else None
    result["subtype"] = subtype

    if model is None:
        result["nist_pass"]["status"] = "error"
        result["nist_pass"]["errors"] = [f"cannot detect OSCAL model (root keys: {list(data.keys())[:5]})"]
        return result

    # --- Pass 1: NIST (skipped for O4R-native roots that have no NIST schema) ---
    if model in O4R_NATIVE_ROOTS:
        result["nist_pass"]["status"] = "skipped"
        result["nist_pass"]["schema"] = None
        result["nist_pass"]["reason"] = f"'{model}' is OSCAL4Rail-native; no NIST base schema (ADR-018)"
    else:
        nist_schema = NIST_DIR / NIST_SCHEMA_MAP[model]
        result["nist_pass"]["schema"] = NIST_SCHEMA_MAP[model]
        if not nist_schema.exists():
            result["nist_pass"]["status"] = "error"
            result["nist_pass"]["errors"] = [f"NIST schema not found: {nist_schema}"]
            return result
        nist_errors, result["nist_pass"]["skipped_constraints"] = _run_schema(nist_schema, data)
        result["nist_pass"]["status"] = "pass" if not nist_errors else "fail"
        result["nist_pass"]["errors"] = nist_errors

    # --- oscal-version (report-only, ADR-013) ---
    av = artifact_oscal_version(data, model)
    pv = result["oscal_version"]["pinned"]
    result["oscal_version"]["artifact"] = av
    if av is None:
        result["oscal_version"]["match"] = None
        result["oscal_version"]["note"] = "artifact declares no oscal-version"
    else:
        match = (pv is not None and av == pv)
        result["oscal_version"]["match"] = match
        if not match:
            result["oscal_version"]["note"] = (
                f"oscal-version mismatch: artifact {av} != pinned {pv} "
                "(reported, not enforced — ADR-013)"
            )

    # --- Pass 2: O4R (only with --strict) ---
    if not strict:
        result["o4r_pass"]["status"] = "not-run"
        result["o4r_pass"]["reason"] = "O4R pass runs only with --strict"
    elif foreign and model not in O4R_NATIVE_ROOTS:
        result["o4r_pass"]["status"] = "skipped"
        result["o4r_pass"]["reason"] = (
            "declared as foreign (non-OSCAL4Rail) OSCAL with --foreign; "
            "only the NIST base schema was applied")
    elif subtype not in O4R_SCHEMA_MAP:
        result["o4r_pass"]["status"] = "skipped"
        result["o4r_pass"]["reason"] = f"no O4R constraint schema for subtype '{subtype}'"
    else:
        o4r_schema = O4R_DIR / O4R_SCHEMA_MAP[subtype]
        result["o4r_pass"]["schema"] = O4R_SCHEMA_MAP[subtype]
        if not o4r_schema.exists():
            result["o4r_pass"]["status"] = "skipped"
            result["o4r_pass"]["reason"] = f"O4R schema file missing: {o4r_schema}"
        else:
            o4r_errors, result["o4r_pass"]["skipped_constraints"] = _run_schema(o4r_schema, data)
            # catalog: invariants JSON Schema cannot express (catalog-format.md §2)
            if subtype == "catalog":
                o4r_errors = o4r_errors + catalog_consistency(data)
                o4r_errors = o4r_errors + reference_language_violations(data)
            # rule-set: add the ADR-018 §10 cross-artifact consistency checks
            if model == "rule-set":
                o4r_errors = o4r_errors + ruleset_consistency(data, path)
            result["o4r_pass"]["status"] = "pass" if not o4r_errors else "fail"
            result["o4r_pass"]["errors"] = o4r_errors

    # --- overall pass/fail ---
    # NIST must pass when it ran; "skipped" (O4R-native root) is not a failure.
    ok = result["nist_pass"]["status"] in ("pass", "skipped")
    if strict and result["o4r_pass"]["status"] == "fail":
        ok = False
    # An O4R-native root that was NOT validated against its O4R schema (no --strict)
    # is inconclusive, not a pass: require --strict to assert a rule-set is valid.
    if model in O4R_NATIVE_ROOTS and result["o4r_pass"]["status"] != "pass":
        ok = False
    result["ok"] = ok
    return result


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_report(result: dict, strict: bool, foreign: bool = False) -> dict:
    return {
        "generated": _now(),
        "validator": "tools/validate.py",
        "mode": {"strict": strict, "foreign": foreign, "require_o4r": False},
        "result": result,
    }


def render_markdown(report: dict) -> str:
    r = report["result"]
    nist = r["nist_pass"]
    o4r = r["o4r_pass"]
    ov = r["oscal_version"]

    def _status(s: str) -> str:
        return {"pass": "✅ pass", "fail": "❌ fail", "skipped": "⏭️ skipped",
                "not-run": "— not run", "error": "⚠️ error"}.get(s, s)

    def _skipped(pass_result: dict) -> list[str]:
        skipped = pass_result.get("skipped_constraints") or {}
        if not skipped:
            return []
        out = ["- Constraints NOT evaluated (a pass here does not cover them):"]
        return out + [f"  - {reason}: {count} value(s)" for reason, count in sorted(skipped.items())]

    lines = [
        f"# Validation report — `{Path(r['file']).name}`",
        "",
        f"- **Generated:** {report['generated']}",
        f"- **Mode:** strict={report['mode']['strict']} · foreign={report['mode'].get('foreign', False)} "
        f"· require-o4r={report['mode']['require_o4r']} (deferred, #42)",
        f"- **Model:** `{r['model']}`",
        f"- **Subtype:** `{r.get('subtype')}`",
        f"- **Overall:** {'✅ PASS' if r['ok'] else '❌ FAIL'}",
        "",
        "## NIST base schema (pass 1)",
        f"- Schema: `{nist['schema']}`",
        f"- Status: {_status(nist['status'])}",
    ]
    if nist["errors"]:
        lines.append("- Errors:")
        lines += [f"  - `{e}`" for e in nist["errors"][:50]]
    lines += _skipped(nist)

    lines += [
        "",
        "## OSCAL4Rail constraints (pass 2)",
        f"- Schema: `{o4r['schema']}`" if o4r["schema"] else "- Schema: —",
        f"- Status: {_status(o4r['status'])}",
    ]
    if o4r.get("reason"):
        lines.append(f"- Reason: {o4r['reason']}")
    if o4r["errors"]:
        lines.append("- Errors:")
        lines += [f"  - `{e}`" for e in o4r["errors"][:50]]
    lines += _skipped(o4r)

    lines += [
        "",
        "## oscal-version (reported, not enforced — ADR-013)",
        f"- Artifact: `{ov['artifact']}`",
        f"- Pinned: `{ov['pinned']}`",
        f"- Match: {ov['match']}",
    ]
    if ov.get("note"):
        lines.append(f"- Note: {ov['note']}")
    lines.append("")
    return "\n".join(lines)


def write_reports(result: dict, strict: bool, foreign: bool = False) -> tuple[Path, Path]:
    report = build_report(result, strict, foreign)
    src = Path(result["file"])
    json_path = src.parent / f"{src.stem}.validation.json"
    md_path = src.parent / f"{src.stem}.validation.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    md_path.write_text(render_markdown(report))
    return md_path, json_path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _print_summary(result: dict, quiet: bool) -> None:
    if quiet:
        return
    f = result["file"]
    nist = result["nist_pass"]["status"]
    o4r = result["o4r_pass"]["status"]
    tag = "✅" if result["ok"] else "❌"
    extra = []
    if result["oscal_version"]["match"] is False:
        extra.append("oscal-version mismatch (reported)")
    if o4r == "skipped":
        extra.append(f"O4R skipped: {result['o4r_pass']['reason']}")
    not_evaluated = sum(
        sum((result[p].get("skipped_constraints") or {}).values()) for p in ("nist_pass", "o4r_pass"))
    if not_evaluated:
        extra.append(f"{not_evaluated} constraint check(s) NOT evaluated (see report)")
    suffix = f"  [{'; '.join(extra)}]" if extra else ""
    print(f"{tag} {f}  (nist={nist}, o4r={o4r}){suffix}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Consolidated OSCAL4Rail validator (two-pass; NIST + O4R constraints). See ADR-013.",
    )
    ap.add_argument("files", nargs="+", help="OSCAL artifact(s) (YAML or JSON)")
    ap.add_argument("--foreign", action="store_true",
                    help="the file(s) are OSCAL but not OSCAL4Rail artifacts (e.g. an upstream "
                         "catalog): NIST pass only; the O4R pass is skipped and the skip reported")
    ap.add_argument("--strict", action="store_true",
                    help="also run the additive OSCAL4Rail constraint pass (auto-mapped by model)")
    ap.add_argument("--report", choices=["none", "file"], default="file",
                    help="write a per-file report (Markdown + JSON) beside the artifact (default: file)")
    ap.add_argument("--quiet", action="store_true", help="suppress per-file stdout summary")
    args = ap.parse_args(argv)

    all_ok = True
    for fp in args.files:
        path = Path(fp)
        if not path.exists():
            print(f"⚠️  {fp}: file not found", file=sys.stderr)
            all_ok = False
            continue
        result = validate_file(path, strict=args.strict, foreign=args.foreign)
        if args.report == "file":
            md, js = write_reports(result, strict=args.strict, foreign=args.foreign)
            if not args.quiet:
                print(f"   report: {md}  |  {js}")
        _print_summary(result, args.quiet)
        all_ok = all_ok and result["ok"]

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
