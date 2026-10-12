# Getting Started with OSCAL4Rail

This tutorial walks you through extracting your first OSCAL4Rail catalog from a regulation document.

**Time:** ~30 minutes
**Prerequisites:** Python 3.10+, pip

## Step 1: Install dependencies

```bash
pip install pyyaml jsonschema openpyxl
pip install markitdown  # PDF text extraction
```

## Step 2: Get the source documents

For this tutorial we use the Swiss BS-KI standard (publicly available):

```bash
mkdir -p my-catalog/source
curl -o my-catalog/source/BS-KI_DE.pdf \
  https://www.oev-info.ch/sites/default/files/2026-01/BS-KI_DE.pdf
curl -o my-catalog/source/Matrix_BS-KI_DE.xlsx \
  https://www.oev-info.ch/sites/default/files/2025-12/Matrix_BS-KI_DE.xlsx
```

## Step 3: Extract the PDF text

```bash
markitdown my-catalog/source/BS-KI_DE.pdf > my-catalog/source/bs-ki-fulltext.txt
```

You now have the full text. Identify the chapter structure:

```bash
grep -n "^[0-9]\.[0-9]  " my-catalog/source/bs-ki-fulltext.txt | head -20
```

Output:
```
758:2.1  Aktuelle Uhrzeit
773:2.2  Name der Haltestelle
807:2.4  Wegweisung
...
```

## Step 4: Create your first control manually

Create `my-catalog/my-first-catalog.yaml`:

```yaml
catalog:
  uuid: "YOUR-UUID-HERE"  # python3 -c "import uuid; print(uuid.uuid4())"
  metadata:
    title: "My First OSCAL4Rail Catalog"
    version: "1.0"
    oscal-version: "1.1.3"
    props:
      - name: source-document
        value: "BS-KI_DE.pdf"
  groups:
    - id: bs-ki-2
      title: "Allgemeine Informationsinhalte der Kundeninformation"
      controls:
        - id: bs-ki-2.1
          title: "Aktuelle Uhrzeit"
          parts:
            - name: statement
              prose: |
                Bei Haltestellen mit weniger als 800 Ein- und Aussteigern pro Tag kann auf die Angabe der
                Uhrzeit verzichtet werden.

                Die aktuelle Uhrzeit ist für die Kundschaft ein zentrales Element zur Orientierung.
          props:
            - name: source-chapter
              value: "2.1"
            - name: applicability
              value: "verbindlich"
              class: "haltestelle.bahn"
            - name: applicability
              value: "empfohlen"
              class: "haltestelle.bus-tram-metro"
```

## Step 5: Validate

```bash
python3 tools/validate.py my-catalog/my-first-catalog.yaml
# ✅ my-catalog/my-first-catalog.yaml: Valid OSCAL4Rail Catalog
```

## Step 6: Use the automated extraction

For all 42 BS-KI rules:

```bash
python3 tools/extract.py \
  --pdf my-catalog/source/BS-KI_DE.pdf \
  --matrix my-catalog/source/Matrix_BS-KI_DE.xlsx \
  --output my-catalog/bs-ki-de.yaml

python3 tools/validate.py my-catalog/bs-ki-de.yaml
# ✅ my-catalog/bs-ki-de.yaml: Valid OSCAL4Rail Catalog (42 controls)
```

## Next Steps

- [How-to: Migrate your existing governance](../how-to/migrate-existing-governance.md)
- [How-to: Integrate into AI agents](../how-to/integrate-agents.md)
- [Reference: OSCAL4Rail format](../reference/format.md)
