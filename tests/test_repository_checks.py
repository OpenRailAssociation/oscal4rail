# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Repository-level checks that already exist as scripts (ADR-008, arc42/ADR sync)."""
import subprocess
import sys


def _run(repo, *args):
    return subprocess.run([sys.executable, *args], cwd=repo, capture_output=True, text=True)


def test_committed_nist_schemas_match_the_manifest(repo):
    result = _run(repo, "tools/fetch_oscal_schemas.py", "--verify-only")
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_adr_is_referenced_in_arc42(repo):
    result = _run(repo, "tools/check_arc42_adr_sync.py")
    assert result.returncode == 0, result.stdout + result.stderr


def test_change_cli_file_mode_prints_a_summary(repo):
    catalog = "examples/rules/example-catalog.yaml"
    result = _run(repo, "tools/change.py", "--from", catalog, "--to", catalog, "--summary")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0 change(s):"
