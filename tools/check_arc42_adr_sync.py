# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Check that docs/arc42.md and the ADR files under docs/adr/ agree.

Keeps the arc42 architecture documentation in sync with the ADR set
(Single Source of Truth: the ADR files; arc42 §9 is the master index).

For every ADR file it checks that

- the ADR has a row in the master table of arc42 §9 (a mention elsewhere in the
  text does not count), and
- the status in that row is the status the ADR file declares. Compared is the
  status keyword (Proposed, Accepted, Rejected, Deprecated, Superseded); notes in
  parentheses may differ.

Usage:
    python3 tools/check_arc42_adr_sync.py

Exit code 0 = in sync; 1 = at least one finding; 2 = files not found.
No external dependencies (tech-stack principle: minimal, portable, inspectable).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = REPO_ROOT / "docs" / "adr"
ARC42 = REPO_ROOT / "docs" / "arc42.md"

ADR_FILE_RE = re.compile(r"^ADR-(\d+)-.*\.md$")


def adr_number(filename: str) -> str | None:
    m = ADR_FILE_RE.match(filename)
    return m.group(1) if m else None


# A row of the master table: "| ADR-007 | Title | Status | Date |", the first cell
# optionally a Markdown link.
TABLE_ROW_RE = re.compile(r"^\|\s*\[?ADR-(\d+)\]?(?:\([^)]*\))?\s*\|[^|]*\|\s*([^|]*?)\s*\|")
STATUS_LINE_RE = re.compile(r"^\*\*Status:\*\*\s*(.+?)\s*$", re.MULTILINE)


def status_keyword(status: str) -> str:
    """The leading word of a status ("Accepted (amended ...)" -> "accepted")."""
    match = re.match(r"[A-Za-z]+", status.strip())
    return match.group(0).lower() if match else ""


def table_statuses(arc42_text: str) -> dict[str, str]:
    """ADR number -> status cell, from the master table rows."""
    rows: dict[str, str] = {}
    for line in arc42_text.splitlines():
        match = TABLE_ROW_RE.match(line)
        if match:
            rows.setdefault(match.group(1), match.group(2))
    return rows


def find_problems(adr_dir: Path, arc42_text: str) -> tuple[list[str], list[str]]:
    """Return (checked ADR file names, findings)."""
    rows = table_statuses(arc42_text)
    checked: list[str] = []
    problems: list[str] = []
    for path in sorted(adr_dir.glob("ADR-*.md")):
        num = adr_number(path.name)
        if num is None:
            continue
        checked.append(path.name)
        if num not in rows:
            problems.append(f"{path.name}: no row in the master table of arc42.md §9")
            continue
        declared = STATUS_LINE_RE.search(path.read_text(encoding="utf-8"))
        if declared is None:
            problems.append(f"{path.name}: no '**Status:**' line in the ADR file")
            continue
        if status_keyword(declared.group(1)) != status_keyword(rows[num]):
            problems.append(
                f"{path.name}: status differs: ADR file says '{declared.group(1)}', "
                f"arc42.md table says '{rows[num]}'")
    return checked, problems


def main() -> int:
    if not ADR_DIR.is_dir():
        print(f"ERROR: ADR directory not found: {ADR_DIR}", file=sys.stderr)
        return 2
    if not ARC42.is_file():
        print(f"ERROR: arc42 not found: {ARC42}", file=sys.stderr)
        return 2

    checked, problems = find_problems(ADR_DIR, ARC42.read_text(encoding="utf-8"))

    print(f"Checked {len(checked)} ADR file(s) against {ARC42.relative_to(REPO_ROOT)}")
    if problems:
        print("FAIL: arc42.md and the ADR files disagree:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nThe ADR files are the source of truth: update the master table in "
            "arc42.md §9 (Architecture Decisions).",
            file=sys.stderr,
        )
        return 1

    print("OK: every ADR has a row in the arc42.md master table with a matching status.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
