#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Company-specific renderer TEMPLATE — copy me, do not rely on me directly.

Setup (once):

    cp tools/custom_renderer.example.py tools/custom_renderer.py

Then edit `tools/custom_renderer.py` (NOT this template). The real file is
git-ignored, so framework updates never overwrite your customization; this
template is versioned and may be refreshed by updates for you to compare against.

The core (`tools/generate_doc.py`) imports `custom_renderer` and calls
`render()` for every control. The core itself is never edited, so it stays
upgradeable as the OSCAL4Rail schema evolves. Put all company-specific output
in your copy.

By default this renders nothing extra: props the core does not know are already
shown in a generic properties table, so nothing is ever silently dropped. Only
add code when you want a *dedicated* layout for a specific prop.
"""

from __future__ import annotations

# Prop names you render yourself below. Listing them here removes them from the
# core's generic properties table (so they are not shown twice). Leave empty if
# you only add free-form output.
CLAIMED_PROPS: set[str] = set()


def render(ctrl: dict, depth: int) -> list[str]:
    """Return Markdown lines for one control (empty = render nothing).

    `ctrl`  = the OSCAL control dict (has "id", "title", "props", "parts").
    `depth` = current heading depth, if you want to emit sub-headings.

    ### EDIT BELOW — this is the one place to customize ###

    Example (uncomment and adapt):

        lines = []
        owner = next((p["value"] for p in ctrl.get("props", [])
                      if p.get("name") == "internal-owner"), None)
        if owner:
            lines.append(f"> Owner: {owner}")
            lines.append("")
        return lines
    """
    lines: list[str] = []

    return lines
