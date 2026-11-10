# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Consumer example: every id of a gap-summary entry is routed and counted (#64)."""
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "examples" / "change" / "consumer-example" / "react_to_change.py"


def _report(source_ids, target_ids):
    mapping = {"source-resource": {"href": "old"}, "target-resource": {"href": "new"}, "maps": []}
    if source_ids:
        mapping["source-gap-summary"] = {"unmapped-controls": [{"with-ids": source_ids}]}
    if target_ids:
        mapping["target-gap-summary"] = {"unmapped-controls": [{"with-ids": target_ids}]}
    return {"mapping-collection": {"mappings": [mapping]}}


def _run(tmp_path, report):
    path = tmp_path / "report.yaml"
    path.write_text(yaml.safe_dump(report), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)


def test_every_id_of_a_gap_entry_is_routed_and_counted(tmp_path):
    result = _run(tmp_path, _report(["a-1", "a-2"], ["b-1", "b-2", "b-3"]))
    for cid in ("a-1", "a-2", "b-1", "b-2", "b-3"):
        assert f"{cid}:" in result.stdout
    assert "5 change(s)." in result.stdout
    assert result.returncode == 2  # "added" gates in the example policy


def test_removed_only_does_not_gate(tmp_path):
    result = _run(tmp_path, _report(["a-1", "a-2"], []))
    assert "2 change(s). Gating: no." in result.stdout
    assert result.returncode == 0
