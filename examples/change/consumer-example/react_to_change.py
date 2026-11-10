#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Reference sketch: consume an OSCAL4Rail change report and route a reaction.

NOT a product and NOT part of the framework. This is an illustrative sketch of how a
CONSUMER (a CI/merge pipeline, a scheduled job, or an agent) reads the deterministic,
machine-readable change report (an OSCAL `mapping-collection`, ADR-019) and decides what
to do. The framework delivers the report; the reaction and its policy are the consumer's
(ADR-019 D4/D6).

It READS and ROUTES only: it prints the derived reaction and sets an exit code for gating.
It does NOT act (no notification sent, no downstream write, no merge). Replace the
`react()` body with your own policy (open an issue, call a webhook, fail the pipeline, ...).

Boundary (Meaningful Human Control): an agent/pipeline may detect, classify, route and
trigger mechanical follow-ups within the guardrails the using organisation sets. The
governance decision (is the tightening acceptable? approve downstream) stays with the
owner. Consistency/satisfaction is the Assessment layer's (L4) job, not this script's.

Usage:
    python react_to_change.py <change-report.yaml>
Exit codes:
    0  no gating change
    2  a gating change was found (e.g. tightened/inverted) -> fail the pipeline step
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

# Consumer policy (example): which change categories should gate / escalate.
# This is YOUR policy, not the framework's. Tune it to your system.
GATING = {"tightened", "inverted", "added"}
NOTIFY = {"deprecated", "superseded", "withdrawn", "relaxed", "content-changed", "removed"}


def _prop(props, name, default=None):
    return next((p["value"] for p in props or [] if p.get("name") == name), default)


def _gap_ids(mapping: dict, summary: str) -> list[str]:
    """Every control id listed in a NIST gap-summary, across all its entries."""
    entries = mapping.get(summary, {}).get("unmapped-controls", [])
    return [cid for entry in entries for cid in entry.get("with-ids", [])]


def react(control_id: str, category: str, changed_field: str, props: list) -> bool:
    """Derive and PRINT a reaction. Returns True if this change should gate.

    Replace the prints with real actions in a real consumer (issue, webhook, job trigger).
    """
    detail = ""
    if changed_field == "modality.rank":
        detail = f" (rank {_prop(props,'old-rank')} -> {_prop(props,'new-rank')})"
    elif changed_field == "status.lifecycle":
        detail = f" ({_prop(props,'old-lifecycle')} -> {_prop(props,'new-lifecycle')})"
    elif changed_field == "modality.polarity":
        detail = f" ({_prop(props,'old-polarity')} -> {_prop(props,'new-polarity')})"

    if category in GATING:
        print(f"  [GATE]   {control_id}: {category} on {changed_field}{detail}")
        print(f"           -> reaction: require review / re-assessment (L4) before proceeding")
        return True
    if category in NOTIFY:
        print(f"  [NOTIFY] {control_id}: {category} on {changed_field}{detail}")
        print(f"           -> reaction: inform the owner of the affected context")
        return False
    print(f"  [INFO]   {control_id}: {category} on {changed_field}{detail}")
    return False


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: react_to_change.py <change-report.yaml>")
    doc = yaml.safe_load(Path(sys.argv[1]).read_text())
    mc = doc.get("mapping-collection")
    if not mc:
        sys.exit("not an OSCAL4Rail change report (no mapping-collection root)")

    gating = False
    total = 0
    for mapping in mc.get("mappings", []):
        src = mapping.get("source-resource", {}).get("href", "?")
        tgt = mapping.get("target-resource", {}).get("href", "?")
        print(f"Change report: {src} -> {tgt}")
        # existence changes live in the NIST gap-summaries, not in maps
        # (one entry may list several ids in `with-ids`; each id is one change)
        for summary, category in (("source-gap-summary", "removed"),
                                  ("target-gap-summary", "added")):
            for cid in _gap_ids(mapping, summary):
                total += 1
                if react(cid, category, "control-existence", None):
                    gating = True
        # two-sided changes are maps
        for m in mapping.get("maps", []):
            total += 1
            cid = (m.get("targets") or m.get("sources") or [{}])[0].get("id-ref", "?")
            category = m.get("relationship", "?")
            changed_field = _prop(m.get("props"), "changed-field", "?")
            if react(cid, category, changed_field, m.get("props")):
                gating = True

    print(f"\n{total} change(s). Gating: {'yes' if gating else 'no'}.")
    return 2 if gating else 0


if __name__ == "__main__":
    raise SystemExit(main())
