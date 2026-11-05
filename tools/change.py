#!/usr/bin/env python3
"""OSCAL4Rail Change Impact — reference CLI (MVP).

Compares two states of the same rule catalog and emits an OSCAL `mapping-collection`
(the change report, ADR-019) that validates both against the NIST OSCAL Mapping schema
and the OSCAL4Rail change constraints.

This is the executable reference / MVP proof that the method is deterministic. It
INTERPRETS (classifies per the documented method) and SELF-VALIDATES the format. It does
NOT act: no notification, no downstream write, no agent trigger (ADR-019 D4/D6). The
systemic meaning of a change ("what does it mean for MY system") is the consumer's, not
the framework's.

Input (ADR-019 D2, Git core + file fallback):
  tools/change <base-ref> <head-ref> <catalog-path>      # Git-native (git show)
  tools/change --from <file> --to <file>                 # file fallback (VCS-less)
Optional L2 (enables tightened/relaxed/inverted/deprecated/superseded/withdrawn):
  --rules-from <file|ref:path> --rules-to <file|ref:path>

Classification (ADR-019 D3): added/removed from control existence; strength and lifecycle
from the L2 semantics axis where a rule-set is present; content-changed otherwise. No
guessing without L2 (honest degradation). Precedence lifecycle > strength > existence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

O4R_CHANGE_NS = "https://oscal4rail.openrail.org/ns/change"
PINNED_OSCAL = "1.2.3"


# --- loading: git ref or file ---------------------------------------------------------

def _load_source(spec: str, git_ref: str | None, git_path: str | None) -> dict:
    """Load a YAML/JSON OSCAL doc either from a file (spec) or from git (ref:path)."""
    if git_ref is not None:
        raw = subprocess.run(
            ["git", "show", f"{git_ref}:{git_path}"],
            capture_output=True, text=True,
        )
        if raw.returncode != 0:
            sys.exit(f"git show {git_ref}:{git_path} failed: {raw.stderr.strip()}")
        return yaml.safe_load(raw.stdout)
    return yaml.safe_load(Path(spec).read_text())


# --- model access ---------------------------------------------------------------------

def _controls(catalog_doc: dict) -> dict[str, dict]:
    cat = catalog_doc.get("catalog", {})
    out = {}
    for g in cat.get("groups", []):
        for c in g.get("controls", []):
            out[c["id"]] = c
    return out


def _statement(control: dict) -> str | None:
    for p in control.get("parts", []):
        if p.get("name") == "statement":
            return p.get("prose")
    return None


def _rules(ruleset_doc: dict | None):
    """Return (rules_by_control_id, modality_vocab, status_vocab) or (None, None, None)."""
    if not ruleset_doc:
        return None, None, None
    rs = ruleset_doc.get("rule-set", {})
    by_cid = {r["control-id"]: r for r in rs.get("rules", [])}
    vocab = rs.get("vocabularies", {})
    return by_cid, vocab.get("modality", {}), vocab.get("status", {})


def _axis(label, vocab):
    """Resolve an owner label to its fixed semantics axis dict, or {} if unknown."""
    return vocab.get(label, {}) if label is not None else {}


# --- classification (ADR-019 D3) ------------------------------------------------------

def classify(cid, old_ctrl, new_ctrl, old_rule, new_rule, mod_o, mod_n, st_o, st_n):
    """Return (category, dimension, props) for one control-level change.

    Precedence: lifecycle > strength > existence/content.
    Honest degradation: without L2, only added/removed/content-changed.
    """
    props: list[dict] = []

    # existence
    if old_ctrl is None and new_ctrl is not None:
        props.append({"name": "changed-field", "value": "control-existence"})
        return "added", "existence", props
    if old_ctrl is not None and new_ctrl is None:
        props.append({"name": "changed-field", "value": "control-existence"})
        return "removed", "existence", props

    have_l2 = old_rule is not None and new_rule is not None

    # lifecycle (highest precedence) — needs L2 status axis
    if have_l2:
        lo = _axis(old_rule.get("status"), st_o).get("lifecycle")
        ln = _axis(new_rule.get("status"), st_n).get("lifecycle")
        if lo != ln and ln is not None:
            props += [{"name": "changed-field", "value": "status.lifecycle"},
                      {"name": "old-lifecycle", "value": str(lo)},
                      {"name": "new-lifecycle", "value": str(ln)}]
            if ln == "deprecated":
                return "deprecated", "lifecycle", props
            if ln == "superseded":
                sb = new_rule.get("superseded-by", "")
                if sb:
                    props.append({"name": "superseded-by", "value": sb})
                return "superseded", "lifecycle", props
            if ln == "withdrawn":
                return "withdrawn", "lifecycle", props

    # strength — needs L2 modality axis
    if have_l2:
        ao = _axis(old_rule.get("modality"), mod_o)
        an = _axis(new_rule.get("modality"), mod_n)
        if ao and an:
            if ao.get("polarity") != an.get("polarity"):
                props += [{"name": "changed-field", "value": "modality.polarity"},
                          {"name": "old-polarity", "value": str(ao.get("polarity"))},
                          {"name": "new-polarity", "value": str(an.get("polarity"))}]
                return "inverted", "strength", props
            ro, rn = ao.get("rank"), an.get("rank")
            if ro is not None and rn is not None and ro != rn:
                props += [{"name": "changed-field", "value": "modality.rank"},
                          {"name": "old-rank", "value": str(ro)},
                          {"name": "new-rank", "value": str(rn)}]
                # lower rank = stronger
                return ("tightened" if rn < ro else "relaxed"), "strength", props

    # content fallback (statement changed, or no L2 to decide strength/lifecycle)
    so = _statement(old_ctrl) if old_ctrl else None
    sn = _statement(new_ctrl) if new_ctrl else None
    if so != sn:
        props.append({"name": "changed-field", "value": "statement"})
        return "content-changed", "content", props
    # no detectable change
    return None, None, props


# --- build the OSCAL mapping-collection -----------------------------------------------

def build_mapping(old_cat, new_cat, old_rs, new_rs, src_label, tgt_label,
                  src_ver, tgt_ver):
    old_ctrls, new_ctrls = _controls(old_cat), _controls(new_cat)
    old_rules, mod_o, st_o = _rules(old_rs)
    new_rules, mod_n, st_n = _rules(new_rs)
    old_rules = old_rules or {}
    new_rules = new_rules or {}

    maps = []
    removed_ids: list[str] = []   # in source only  -> source-gap-summary
    added_ids: list[str] = []     # in target only  -> target-gap-summary
    for cid in sorted(set(old_ctrls) | set(new_ctrls)):
        cat_c, dim, props = classify(
            cid, old_ctrls.get(cid), new_ctrls.get(cid),
            old_rules.get(cid), new_rules.get(cid),
            mod_o or {}, mod_n or {}, st_o or {}, st_n or {},
        )
        if cat_c is None:
            continue
        # existence changes are NIST gaps, not maps: a map requires sources AND targets
        # (both minItems:1). "added"/"removed" have only one side, so they go into the
        # NIST source-/target-gap-summary (OSCAL-native, keeps the artifact upgradeable).
        if cat_c == "added":
            added_ids.append(cid)
            continue
        if cat_c == "removed":
            removed_ids.append(cid)
            continue
        m = {
            "uuid": str(_uuid.uuid4()),
            "ns": O4R_CHANGE_NS,
            "relationship": cat_c,
            "sources": [{"type": "control", "id-ref": cid}],
            "targets": [{"type": "control", "id-ref": cid}],
            "props": [{"name": "dimension", "value": dim}] + props,
        }
        maps.append(m)

    def _gap(ids):
        return {
            "uuid": str(_uuid.uuid4()),
            "unmapped-controls": [{"with-ids": [cid]} for cid in ids],
        }

    return {
        "mapping-collection": {
            "uuid": str(_uuid.uuid4()),
            "metadata": {
                "title": f"Change report: {src_label} -> {tgt_label}",
                "last-modified": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "version": "1.0.0",
                "oscal-version": PINNED_OSCAL,
            },
            "provenance": {
                "method": "automation",
                "matching-rationale": "semantic",
                "status": "complete",
                "mapping-description": (
                    "Change report between two versions of the rule catalog, classified "
                    "deterministically from the OSCAL4Rail L2 semantics axis (ADR-019). "
                    "Derived artifact; the catalog is the source of truth."
                ),
            },
            "mappings": [_build_single_mapping(
                src_label, tgt_label, src_ver, tgt_ver, maps,
                _gap(removed_ids) if removed_ids else None,
                _gap(added_ids) if added_ids else None,
            )],
        }
    }


def _build_single_mapping(src_label, tgt_label, src_ver, tgt_ver, maps,
                          source_gap, target_gap):
    mapping = {
        "uuid": str(_uuid.uuid4()),
        "source-resource": {
            "type": "catalog", "href": src_label,
            "props": [{"name": "catalog-version", "value": src_ver or "unknown"}],
        },
        "target-resource": {
            "type": "catalog", "href": tgt_label,
            "props": [{"name": "catalog-version", "value": tgt_ver or "unknown"}],
        },
        "props": [{"name": "o4r-artifact", "value": "change-report"}],
        "maps": maps,
    }
    # NIST source-/target-gap-summary carry removed/added controls (one-sided existence).
    if source_gap is not None:
        mapping["source-gap-summary"] = source_gap
    if target_gap is not None:
        mapping["target-gap-summary"] = target_gap
    return mapping


def _catalog_version(doc: dict) -> str | None:
    return doc.get("catalog", {}).get("metadata", {}).get("version")


def _summary(mapping: dict) -> str:
    m0 = mapping["mapping-collection"]["mappings"][0]
    maps = m0.get("maps", [])
    added = [c["with-ids"][0] for c in m0.get("target-gap-summary", {}).get("unmapped-controls", [])]
    removed = [c["with-ids"][0] for c in m0.get("source-gap-summary", {}).get("unmapped-controls", [])]
    total = len(maps) + len(added) + len(removed)
    lines = [f"{total} change(s):"]
    for cid in removed:
        lines.append(f"  {cid}: removed (changed: control-existence)")
    for cid in added:
        lines.append(f"  {cid}: added (changed: control-existence)")
    for m in maps:
        cid = (m["targets"] or m["sources"])[0]["id-ref"]
        field = next((p["value"] for p in m.get("props", []) if p["name"] == "changed-field"), "?")
        lines.append(f"  {cid}: {m['relationship']} (changed: {field})")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="OSCAL4Rail Change Impact reference CLI (MVP).")
    ap.add_argument("base", nargs="?", help="base git ref (Git-native mode)")
    ap.add_argument("head", nargs="?", help="head git ref (Git-native mode)")
    ap.add_argument("catalog_path", nargs="?", help="catalog path within the repo (Git-native mode)")
    ap.add_argument("--from", dest="from_file", help="old catalog file (file-fallback mode)")
    ap.add_argument("--to", dest="to_file", help="new catalog file (file-fallback mode)")
    ap.add_argument("--rules-from", help="old rule-set (file, or ref:path in Git mode)")
    ap.add_argument("--rules-to", help="new rule-set (file, or ref:path in Git mode)")
    ap.add_argument("-o", "--output", help="write YAML here (default: stdout)")
    ap.add_argument("--summary", action="store_true", help="human-readable summary instead of OSCAL")
    args = ap.parse_args()

    git_mode = bool(args.base and args.head and args.catalog_path)
    file_mode = bool(args.from_file and args.to_file)
    if not (git_mode or file_mode):
        ap.error("provide either '<base> <head> <catalog-path>' (Git) or '--from --to' (file)")

    if git_mode:
        old_cat = _load_source(None, args.base, args.catalog_path)
        new_cat = _load_source(None, args.head, args.catalog_path)
        src_label, tgt_label = f"{args.catalog_path}@{args.base}", f"{args.catalog_path}@{args.head}"
    else:
        old_cat = _load_source(args.from_file, None, None)
        new_cat = _load_source(args.to_file, None, None)
        src_label, tgt_label = args.from_file, args.to_file

    def _load_rules(spec):
        if not spec:
            return None
        if git_mode and ":" in spec:
            ref, path = spec.split(":", 1)
            return _load_source(None, ref, path)
        return _load_source(spec, None, None)

    old_rs = _load_rules(args.rules_from)
    new_rs = _load_rules(args.rules_to)

    mapping = build_mapping(
        old_cat, new_cat, old_rs, new_rs, src_label, tgt_label,
        _catalog_version(old_cat), _catalog_version(new_cat),
    )

    if args.summary:
        print(_summary(mapping))
        return 0

    out = yaml.safe_dump(mapping, allow_unicode=True, sort_keys=False)
    if args.output:
        Path(args.output).write_text(out)
        print(f"written {args.output}")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
