# How-To: Generate Human-Readable Documents from an OSCAL Catalog

Render a machine-readable OSCAL4Rail catalog back into a human-readable
document that a governance owner can verify against the original. This is the
core of "verifiability by design" (Meaningful Human Control).

## Concept

The tool `tools/generate_doc.py` is a **renderer**: it translates the OSCAL
YAML into structured Markdown, control by control, verbatim. The Markdown is the
universal intermediate; consumers turn it into their target format with standard
open-source tools:

```
OSCAL YAML (SSOT)
      │
      ▼
tools/generate_doc.py  →  Markdown (_rendered/)
      │
      ├─→  pandoc            →  Word (.docx)
      ├─→  Hugo / template   →  HTML (corporate-styled)
      ├─→  openpyxl / XML    →  Excel (.xlsx)
      └─→  print from above  →  PDF
```

We build the **translation logic**, not the final-format generator. The owner or
the organization chooses the output format and applies their corporate template.

## Usage

```bash
# render a catalog to Markdown (output: <dir>/_rendered/<name>.md)
python3 tools/generate_doc.py path/to/catalog.yaml

# render + verify round-trip (every prose value appears verbatim in the output)
python3 tools/generate_doc.py --verify path/to/catalog.yaml

# write to stdout instead of a file
python3 tools/generate_doc.py --stdout path/to/catalog.yaml

# write to a custom path
python3 tools/generate_doc.py -o out.md path/to/catalog.yaml
```

**Output location:** by default, the rendered Markdown is written to
`_rendered/<name>.md` inside the catalog directory. This directory is
git-ignored (generated, not versioned; same pattern as `_fetched/`).

**Round-trip verification (`--verify`):** checks that every `prose` value from
the YAML appears 1:1 in the generated Markdown. A mismatch is an error
(non-zero exit). This is the Design-by-Contract guarantee: code equals intent.

## What the output contains

For each control:

- **Heading** with the source chapter reference and title (e.g. `### 2.1 – Control title`)
- **Statement** prose, verbatim from the catalog (no paraphrasing, no reordering)
- **Guidance** parts as sub-sections (when present)
- **Applicability table** showing obligation level per context
- **Source document** references (when present)
- **Additional properties** table for every other prop (see below)

Catalog metadata (title, version, country, language, source URL) is rendered as
a header block; any other metadata prop appears in a generic table too.

## Custom properties and company-specific renderers

The renderer knows the OSCAL4Rail meta-schema props structurally
(`statement`, `applicability`, `source-chapter`, `country`, `language`,
`source-document`). **Every other prop is rendered generically**, in a
"Weitere Eigenschaften" / "Weitere Metadaten" table showing `name`, `value`,
`ns`, `class`, and `remarks`.

This means two things:

1. **Custom / company-specific props are never silently dropped.** A prop under
   your own namespace, for example:

   ```yaml
   props:
     - name: internal-owner
       ns: https://company.example/ns
       value: Department XY
       remarks: internal only
   ```

   appears in the generic table automatically; you do **not** need to modify
   the generator for your props to show up. This protects against silent drift:
   if a field exists in the catalog, the owner sees it in the rendered document.

2. **The schema will evolve.** As later milestones extend the OSCAL4Rail schema
   (new layers, new props), any new prop at least falls into the generic table.
   When a new prop deserves a *dedicated* layout, extend the renderer
   explicitly (see below). Keep the generator in sync with the schema it renders.

### Building a company-specific renderer

Company-specific rendering lives in a **separate file**, `tools/custom_renderer.py`.
You edit that file only; the core (`tools/generate_doc.py`) is never touched, so
it stays upgradeable as the schema and the core evolve. The core imports
`custom_renderer` and calls its `render()` for every control. If the file is
missing, the core still runs (unknown props keep appearing in the generic table).

`tools/custom_renderer.py` ships empty (renders nothing extra). To give a custom
prop a dedicated layout:

1. Implement the layout in `render(ctrl, depth)`:

   ```python
   def render(ctrl, depth):
       lines = []
       owner = next((p["value"] for p in ctrl.get("props", [])
                     if p.get("name") == "internal-owner"), None)
       if owner:
           lines.append(f"> Owner: {owner}")
           lines.append("")
       return lines
   ```

2. Add the prop name to `CLAIMED_PROPS` in the same file so it is removed from
   the generic table and not shown twice:

   ```python
   CLAIMED_PROPS = {"internal-owner"}
   ```

Everything you do **not** claim this way keeps appearing in the generic table,
so the output stays complete. This is the toolkit approach: one neutral core
renderer plus a separate company file, with the OSCAL YAML always the single
source of truth.

## Example pipelines: Markdown to target format

The rendered Markdown is input for standard tools. Below are recipes; adapt to
your corporate template.

### Markdown → Word (.docx)

```bash
pandoc path/to/_rendered/catalog.md \
  -o catalog.docx \
  --reference-doc=corporate-template.docx
```

`pandoc` maps Markdown headings to Word styles. Supply a `--reference-doc` with
your organization's heading/font/margin styles; pandoc applies them
automatically.

### Markdown → HTML

```bash
# simple standalone page
pandoc path/to/_rendered/catalog.md \
  -o catalog.html --standalone --css=corporate.css

# or feed the rendered .md into a static-site generator (e.g. Hugo)
# that applies your site theme
```

### OSCAL YAML → Excel (.xlsx)

Excel works best when generated directly from the YAML (one row per control),
not from the Markdown intermediate:

```python
import yaml
from openpyxl import Workbook

data = yaml.safe_load(open("path/to/catalog.yaml"))
wb = Workbook()
ws = wb.active
ws.append(["ID", "Chapter", "Title", "Statement", "Applicability", "Obligation"])

def walk(obj):
    for ctrl in obj.get("controls", []):
        props = ctrl.get("props", [])
        chapter = next((p["value"] for p in props if p["name"] == "source-chapter"), "")
        prose = next((p["prose"] for p in ctrl.get("parts", []) if p["name"] == "statement"), "")
        for p in props:
            if p["name"] == "applicability":
                ws.append([ctrl["id"], chapter, ctrl["title"], prose, p.get("class",""), p["value"]])
    for sub in obj.get("groups", []):
        walk(sub)

for g in data["catalog"]["groups"]:
    walk(g)

wb.save("catalog.xlsx")
```

### Any of the above → PDF

PDF is a print format. Generate it from Word or HTML:

```bash
# from HTML (via weasyprint)
weasyprint catalog.html catalog.pdf

# from Word (via LibreOffice)
libreoffice --headless --convert-to pdf catalog.docx

# from Markdown directly (pandoc + LaTeX or weasyprint)
pandoc catalog.md -o catalog.pdf
```

## Traceability: finding the spot in the catalog

The verification loop only works if the owner can act on what they find. When
they spot an error while reading the rendered document, they must know **where
in the catalog** to fix it.

Two mechanisms support this:

1. **Source reference per control.** Every control in the rendered Markdown
   carries a reference line with the catalog path and the control ID:

   ```markdown
   ### 2.1 – Control title

   > 📍 `path/to/catalog.yaml` · ID: `<regulation>-2.1`
   ```

   The owner searches the YAML for `id: <regulation>-2.1` and lands on the exact control.

2. **Navigation hints on verification failure.** When `--verify` finds a prose
   mismatch, it reports the control ID, the part, a snippet, and a ready-to-run
   search command:

   ```
   ❌ Round-trip verification failed (1 mismatch(es)):
     - control `<regulation>-2.1` (part: statement) — prose not found verbatim
       at: <regulation>-2/<regulation>-2.1
       snippet: "First characters of the affected prose..."
       find it in the catalog: grep -n "id: <regulation>-2.1" path/to/catalog.yaml
   ```

The control ID is the stable, chapter-based key (never page-based), so it
survives reformatting and is the reliable anchor between the readable document
and the source of truth.

## Round-trip contract

The invariant: **the prose in the generated document must be identical to the
prose in the YAML.** No paraphrasing, no summarizing, no reordering within a
control. The governance owner reads the generated document and must recognize
their own text word for word.

`--verify` enforces this automatically. Run it in CI to catch regressions.

## Related

- [ADR-013](../adr/ADR-013-validator-consolidation.md): validator (validates the input)
- Issue #6: this tool
