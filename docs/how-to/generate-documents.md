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
# render BS-KI to Markdown (output: catalogs/bs-ki/de/_rendered/bs-ki-de.md)
python3 tools/generate_doc.py catalogs/bs-ki/de/bs-ki-de.yaml

# render + verify round-trip (every prose value appears verbatim in the output)
python3 tools/generate_doc.py --verify catalogs/bs-ki/de/bs-ki-de.yaml

# write to stdout instead of a file
python3 tools/generate_doc.py --stdout catalogs/bs-ki/de/bs-ki-de.yaml

# write to a custom path
python3 tools/generate_doc.py -o /tmp/bs-ki.md catalogs/bs-ki/de/bs-ki-de.yaml
```

**Output location:** by default, the rendered Markdown is written to
`_rendered/<name>.md` inside the catalog directory. This directory is
git-ignored (generated, not versioned; same pattern as `_fetched/`).

**Round-trip verification (`--verify`):** checks that every `prose` value from
the YAML appears 1:1 in the generated Markdown. A mismatch is an error
(non-zero exit). This is the Design-by-Contract guarantee: code equals intent.

## What the output contains

For each control:

- **Heading** with the source chapter reference and title (e.g. `### 2.1 – Aktuelle Uhrzeit`)
- **Statement** prose, verbatim from the catalog (no paraphrasing, no reordering)
- **Guidance** parts as sub-sections (when present)
- **Applicability table** showing obligation level per context (`verbindlich` / `empfohlen`)
- **Source document** references (when present)

Catalog metadata (title, version, country, language, source URL) is rendered as
a header block.

## Example pipelines: Markdown to target format

The rendered Markdown is input for standard tools. Below are recipes; adapt to
your corporate template.

### Markdown → Word (.docx)

```bash
pandoc catalogs/bs-ki/de/_rendered/bs-ki-de.md \
  -o bs-ki-de.docx \
  --reference-doc=corporate-template.docx
```

`pandoc` maps Markdown headings to Word styles. Supply a `--reference-doc` with
your organization's heading/font/margin styles; pandoc applies them
automatically.

### Markdown → HTML

```bash
# simple standalone page
pandoc catalogs/bs-ki/de/_rendered/bs-ki-de.md \
  -o bs-ki-de.html --standalone --css=corporate.css

# or via Hugo (for the project website, see issue #36)
# place the rendered .md in the Hugo content tree; Hugo applies the site theme
```

For DB-internal reports (Project 2): use DB UX v3 Whitelabel styling.
For OSS artifacts (Project 1): use OSRD-UI / osrd-design as reference.

### OSCAL YAML → Excel (.xlsx)

Excel works best when generated directly from the YAML (one row per control),
not from the Markdown intermediate:

```python
import yaml
from openpyxl import Workbook

data = yaml.safe_load(open("catalogs/bs-ki/de/bs-ki-de.yaml"))
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

wb.save("bs-ki-de.xlsx")
```

### Any of the above → PDF

PDF is a print format. Generate it from Word or HTML:

```bash
# from HTML (via weasyprint)
weasyprint bs-ki-de.html bs-ki-de.pdf

# from Word (via LibreOffice)
libreoffice --headless --convert-to pdf bs-ki-de.docx

# from Markdown directly (pandoc + LaTeX or weasyprint)
pandoc bs-ki-de.md -o bs-ki-de.pdf
```

## Traceability: finding the spot in the catalog

The verification loop only works if the owner can act on what they find. When
they spot an error while reading the rendered document, they must know **where
in the catalog** to fix it.

Two mechanisms support this:

1. **Source reference per control.** Every control in the rendered Markdown
   carries a reference line with the catalog path and the control ID:

   ```markdown
   ### 2.1 – Aktuelle Uhrzeit

   > 📍 `catalogs/bs-ki/de/bs-ki-de.yaml` · ID: `bs-ki-2.1`
   ```

   The owner searches the YAML for `id: bs-ki-2.1` and lands on the exact control.

2. **Navigation hints on verification failure.** When `--verify` finds a prose
   mismatch, it reports the control ID, the part, a snippet, and a ready-to-run
   search command:

   ```
   ❌ Round-trip verification failed (1 mismatch(es)):
     - control `bs-ki-2.1` (part: statement) — prose not found verbatim
       at: bs-ki-2/bs-ki-2.1
       snippet: "Bei Haltestellen mit weniger als 800 Ein- und Aussteigern pr..."
       find it in the catalog: grep -n "id: bs-ki-2.1" catalogs/bs-ki/de/bs-ki-de.yaml
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
- Issue #36: project website (Hugo renders the same Markdown for the public site)
- Issue #30: catalog back-generator with styled HTML (distinct scope)
