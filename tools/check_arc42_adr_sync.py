# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Check that every ADR under docs/adr/ is referenced in docs/arc42.md.

Keeps the arc42 architecture documentation in sync with the ADR set
(Single Source of Truth: the ADR files; arc42 §9 is the master index).

Usage:
    python3 tools/check_arc42_adr_sync.py

Exit code 0 = all ADRs referenced; non-zero = at least one ADR missing.
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


def main() -> int:
    if not ADR_DIR.is_dir():
        print(f"ERROR: ADR directory not found: {ADR_DIR}", file=sys.stderr)
        return 2
    if not ARC42.is_file():
        print(f"ERROR: arc42 not found: {ARC42}", file=sys.stderr)
        return 2

    arc42_text = ARC42.read_text(encoding="utf-8")

    missing: list[str] = []
    checked: list[str] = []
    for path in sorted(ADR_DIR.glob("ADR-*.md")):
        num = adr_number(path.name)
        if num is None:
            continue
        checked.append(path.name)
        # Reference counts if either the exact filename is linked, or the
        # canonical token "ADR-<num>" appears in the arc42 text.
        token = f"ADR-{num}"
        if path.name in arc42_text or re.search(rf"\b{re.escape(token)}\b", arc42_text):
            continue
        missing.append(path.name)

    print(f"Checked {len(checked)} ADR file(s) against {ARC42.relative_to(REPO_ROOT)}")
    if missing:
        print("FAIL: the following ADRs are NOT referenced in arc42.md:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        print(
            "\nAdd each missing ADR to the master table in arc42.md §9 "
            "(Architecture Decisions).",
            file=sys.stderr,
        )
        return 1

    print("OK: every ADR is referenced in arc42.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
