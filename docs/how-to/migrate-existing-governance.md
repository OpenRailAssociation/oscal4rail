# How-To: Migrate Existing Governance to OSCAL4Rail

This guide explains how to convert your organisation's existing regulation documents into OSCAL4Rail catalogs.

## Overview

```
Existing governance                →    OSCAL4Rail
─────────────────                       ──────────
PDF regulation document            →    OSCAL Catalog (one .yaml file)
Chapter / section                  →    Group + Control
Rule text (verbatim)               →    control.parts[statement]
Implementing regulation (AB)       →    control.parts[guidance]
Applicability table                →    control.props[applicability]
Transition document                →    catalog.back-matter.resources
Version number                     →    catalog.metadata.version
```

## Decision: What becomes a Control?

A control is **one atomic rule** — the smallest unit that can change independently. Use this checklist:

- [ ] Can this rule be complied with or violated independently of other rules? → **separate control**
- [ ] Is this rule always applicable together with another rule? → **consider merging or guidance part**
- [ ] Does this rule have its own chapter number in the source document? → **use that as control ID**

## Step-by-Step Migration

### 1. Inventory your sources

List all relevant documents:

| Document | Type | Version | URL / Storage |
|----------|------|---------|---------------|
| Main standard | PDF | v1.0 | ... |
| Implementing regs (ABs) | PDF | 2025-12 | ... |
| Applicability matrix | XLSX | 2025-12 | ... |
| Transition document | PDF | 2024-06 | ... |

### 2. Define your catalog prefix

Choose a short, unique, lowercase prefix:

| Standard | Prefix | Example control ID |
|----------|--------|-------------------|
| BS-KI (CH) | `bs-ki` | `bs-ki-2.1` |
| TSI TAT (EU) | `tsi-tat` | `tsi-tat-4.2.1` |
| Ril 420 (DB) | `ril-420` | `ril-420-3.1` |

Rule: `<organisation/country>-<standard>-<chapter.section>`

### 3. Extract chapter structure

```bash
markitdown your-regulation.pdf > fulltext.txt
grep -n "^[0-9]\+\.[0-9]\+  " fulltext.txt
```

### 4. Decide integration strategy per document type

| Document type | Integration |
|---------------|-------------|
| Main regulation | `statement` part (verbatim) |
| Implementing regulation (AB) | `guidance` part in the relevant control |
| Annex with examples/templates | `guidance` part |
| Transition document | `back-matter` resource |
| Cross-reference to other standards | `back-matter` resource |

### 5. Handle applicability

If your regulation has an applicability matrix (who must comply with what):

```yaml
props:
  - name: applicability
    value: verbindlich   # or: empfohlen, nicht-relevant
    class: "<channel>.<transport-mode>"
    remarks: "optional: distinction between mandatory/recommended contexts"
```

If there is no formal matrix, derive applicability from the regulation text:
- "must" / "shall" → `verbindlich`
- "should" / "recommended" → `empfohlen`
- Not mentioned → omit the prop

### 6. Archive before updating

Before overwriting a catalog with a new regulation version:

```bash
cp catalogs/my-catalog.yaml catalogs/history/my-catalog_v1.0.yaml
git add catalogs/history/my-catalog_v1.0.yaml
git commit -m "chore: archive my-catalog v1.0 before update"
```

### 7. Generate diff after update

```bash
python3 tools/diff.py \
  catalogs/history/my-catalog_v1.0.yaml \
  catalogs/my-catalog.yaml
```

Output:
```
CHANGED: my-catalog-2.1 (statement modified)
NEW:     my-catalog-4.5 (added in v2.0)
REMOVED: my-catalog-3.8 (deleted in v2.0)
APPLICABILITY CHANGED: my-catalog-2.5 haltestelle.seilbahn: empfohlen → verbindlich
```

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Paraphrasing rule text | Always use verbatim quotes in `statement` |
| Using page numbers as IDs | Use chapter numbers — they are stable |
| One control for multiple rules | Split into separate controls |
| Losing sub-section detail | Use nested `parts` for sub-sections |
| Forgetting annexes | Integrate as `guidance` or `back-matter` |
