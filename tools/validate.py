#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Consolidated OSCAL4Rail validator (ADR-013).

Two-pass validation of an OSCAL4Rail artifact:

  Pass 1 (always)   NIST OSCAL base schema, selected by detected model.
  Pass 2 (--strict) additive OSCAL4Rail constraints, auto-mapped by model
                    (catalog -> catalog constraints, profile -> cascade
                    constraints). Models without an O4R schema are SKIPPED
                    and the skip is recorded in the report (no silent drift).

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
import sys
from pathlib import Path

import jsonschema
import jsonschema._keywords
import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).parent.parent
NIST_DIR = REPO_ROOT / "schemas" / "nist"
O4R_DIR = REPO_ROOT / "schemas" / "oscal4rail"
MANIFEST = NIST_DIR / "manifest.json"

# OSCAL root element -> NIST schema file
NIST_SCHEMA_MAP = {
    "catalog": "oscal-catalog.json",
    "profile": "oscal-profile.json",
    "assessment-results": "oscal-assessment-results.json",
    "component-definition": "oscal-component-definition.json",
    "mapping-collection": "oscal-mapping.json",
}

# OSCAL model -> additive OSCAL4Rail constraint schema (two-pass, ADR-013).
# Models absent from this map have no O4R schema yet -> skip + report.
O4R_SCHEMA_MAP = {
    "catalog": "oscal4rail-catalog-constraints.schema.json",
    "profile": "oscal4rail-profile-cascade-constraints.schema.json",
}


def _safe_pattern(validator, patrn, instance, schema):
    """Skip Unicode regex patterns (\\p{L}) not supported by Python re."""
    if r"\p{" in patrn:
        return
    yield from jsonschema._keywords.pattern(validator, patrn, instance, schema)


_Validator = jsonschema.validators.extend(Draft7Validator, {"pattern": _safe_pattern})


def load_data(path: Path) -> dict:
    with open(path) as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        return json.load(f)


def detect_model(data: dict) -> str | None:
    for key in NIST_SCHEMA_MAP:
        if key in data:
            return key
    return None


def pinned_oscal_version() -> str | None:
    try:
        return json.load(open(MANIFEST)).get("oscal_version")
    except (OSError, ValueError):
        return None


def artifact_oscal_version(data: dict, model: str) -> str | None:
    root = data.get(model)
    if isinstance(root, dict):
        meta = root.get("metadata")
        if isinstance(meta, dict):
            v = meta.get("oscal-version")
            return str(v) if v is not None else None
    return None


def _run_schema(schema_path: Path, data: dict) -> list[str]:
    schema = json.load(open(schema_path))
    errors = sorted(_Validator(schema).iter_errors(data), key=lambda e: list(e.absolute_path))
    out = []
    for e in errors:
        loc = ".".join(str(p) for p in e.absolute_path) or "(root)"
        out.append(f"[{loc}] {e.message}")
    return out


def validate_file(path: Path, strict: bool) -> dict:
    """Validate one file, return a structured result (the report record)."""
    result: dict = {
        "file": str(path),
        "model": None,
        "nist_pass": {"status": "error", "schema": None, "errors": []},
        "o4r_pass": {"status": "skipped", "schema": None, "errors": [], "reason": None},
        "oscal_version": {"artifact": None, "pinned": pinned_oscal_version(), "match": None, "note": None},
        "ok": False,
    }

    data = load_data(path)
    model = detect_model(data)
    result["model"] = model

    if model is None:
        result["nist_pass"]["status"] = "error"
        result["nist_pass"]["errors"] = [f"cannot detect OSCAL model (root keys: {list(data.keys())[:5]})"]
        return result

    # --- Pass 1: NIST ---
    nist_schema = NIST_DIR / NIST_SCHEMA_MAP[model]
    result["nist_pass"]["schema"] = NIST_SCHEMA_MAP[model]
    if not nist_schema.exists():
        result["nist_pass"]["status"] = "error"
        result["nist_pass"]["errors"] = [f"NIST schema not found: {nist_schema}"]
        return result
    nist_errors = _run_schema(nist_schema, data)
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
    elif model not in O4R_SCHEMA_MAP:
        result["o4r_pass"]["status"] = "skipped"
        result["o4r_pass"]["reason"] = f"no O4R constraint schema for model '{model}'"
    else:
        o4r_schema = O4R_DIR / O4R_SCHEMA_MAP[model]
        result["o4r_pass"]["schema"] = O4R_SCHEMA_MAP[model]
        if not o4r_schema.exists():
            result["o4r_pass"]["status"] = "skipped"
            result["o4r_pass"]["reason"] = f"O4R schema file missing: {o4r_schema}"
        else:
            o4r_errors = _run_schema(o4r_schema, data)
            result["o4r_pass"]["status"] = "pass" if not o4r_errors else "fail"
            result["o4r_pass"]["errors"] = o4r_errors

    # --- overall pass/fail (ADR-013): NIST must pass; O4R must pass only if it ran ---
    ok = result["nist_pass"]["status"] == "pass"
    if strict and result["o4r_pass"]["status"] == "fail":
        ok = False
    result["ok"] = ok
    return result


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_report(result: dict, strict: bool) -> dict:
    return {
        "generated": _now(),
        "validator": "tools/validate.py",
        "mode": {"strict": strict, "require_o4r": False},
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

    lines = [
        f"# Validation report — `{Path(r['file']).name}`",
        "",
        f"- **Generated:** {report['generated']}",
        f"- **Mode:** strict={report['mode']['strict']} · require-o4r={report['mode']['require_o4r']} (deferred, #42)",
        f"- **Model:** `{r['model']}`",
        f"- **Overall:** {'✅ PASS' if r['ok'] else '❌ FAIL'}",
        "",
        "## NIST base schema (pass 1)",
        f"- Schema: `{nist['schema']}`",
        f"- Status: {_status(nist['status'])}",
    ]
    if nist["errors"]:
        lines.append("- Errors:")
        lines += [f"  - `{e}`" for e in nist["errors"][:50]]

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


def write_reports(result: dict, strict: bool) -> tuple[Path, Path]:
    report = build_report(result, strict)
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
    suffix = f"  [{'; '.join(extra)}]" if extra else ""
    print(f"{tag} {f}  (nist={nist}, o4r={o4r}){suffix}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Consolidated OSCAL4Rail validator (two-pass; NIST + O4R constraints). See ADR-013.",
    )
    ap.add_argument("files", nargs="+", help="OSCAL artifact(s) (YAML or JSON)")
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
        result = validate_file(path, strict=args.strict)
        if args.report == "file":
            md, js = write_reports(result, strict=args.strict)
            if not args.quiet:
                print(f"   report: {md}  |  {js}")
        _print_summary(result, args.quiet)
        all_ok = all_ok and result["ok"]

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
