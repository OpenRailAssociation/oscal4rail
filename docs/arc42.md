# OSCAL4Rail – Architecture Documentation (arc42)

> **Version:** 0.1.0 (Hack4Rail 2026 – initial draft)
> **License:** CC0 1.0 Universal (public domain)
> **Inspired by:** Arpad Vasarhelyi (Arpad.Vasarhelyi@deutschebahn.com)

---

## Table of Contents

1. [Introduction and Goals](#1-introduction-and-goals)
2. [Architecture Constraints](#2-architecture-constraints)
3. [System Scope and Context](#3-system-scope-and-context)
4. [Solution Strategy](#4-solution-strategy)
5. [Building Block View](#5-building-block-view)
6. [Runtime View](#6-runtime-view)
7. [Deployment View](#7-deployment-view)
8. [Cross-cutting Concepts](#8-cross-cutting-concepts)
9. [Architecture Decisions](#9-architecture-decisions)
10. [Quality Requirements](#10-quality-requirements)
11. [Risks and Technical Debt](#11-risks-and-technical-debt)
12. [Glossary](#12-glossary)

---

## 1. Introduction and Goals

### 1.1 Purpose

OSCAL4Rail is a 4-layer framework extending [NIST OSCAL](https://pages.nist.gov/OSCAL/) for railway governance and regulations.

Railway companies translate legal requirements into internal IT governance (Konzernrichtlinien, internal standards). These company-level adaptations are today scattered across PDFs and Word documents — interpreted individually, applied inconsistently, invisible to automated systems.

OSCAL4Rail makes railway governance **machine-readable, deterministic, and AI-agent-ready** through four layers:

1. **Catalog** — railway profile over [NIST OSCAL Control Layer](https://pages.nist.gov/OSCAL/learn/concepts/layer/control/) (Catalog + Profile). Extended with ID conventions, applicability model, multilingual support.
2. **Rules** — applicability logic using the [Rulemapping](https://rulemapping.org/) format: which controls apply in which context? *Generic layer — reusable beyond railway. Not part of NIST OSCAL.*
3. **Change Impact** — structured, machine-readable change notifications when regulations are updated. *Generic layer — reusable beyond railway. Not part of NIST OSCAL.*
4. **Assessment** — railway profile over [NIST OSCAL Assessment Layer](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/) (Assessment Plan, Assessment Results, POA&M). Adds assessment structure that existing governance documents do not yet contain.

**What makes it "4Rail" — the Regulatory Cascade Model:**

The defining railway-specific innovation is the regulatory cascade with conformance constraints and impact propagation across 5–6 hierarchy levels:

```
International   ISO, EN standards (e.g. ISO 27001, EN 50126)   ← ISO, CEN/CENELEC
                    │ referenced by
EU              TSI, EU Directives (e.g. EU 2026/253)          ← ERA, EU Commission
                    │ specializes (must not contradict)
National        e.g. EBO, AEG (DE) / LEisenbG (CH)            ← EBA / BAV
                    │ concretizes
Agency          e.g. EBA-Verfügungen, BAV-Rundschreiben        ← Federal agency
                    │ adapts
Industry        e.g. BS-KI (CH), Ril 420 (DE), DIN norms      ← Industry bodies, DIN
                    │ implements
Company         e.g. Internal standards, guidelines            ← CIO, EA
                    │ operationalizes
System/Team     e.g. Architecture decisions, ADRs              ← Dev teams
```

Key properties:
- **Conformance flows downward**: each level may only specialize, never contradict its parent
- **Changes cascade**: when a TSI changes → national law adapts → industry standard adapts → company guidelines adapt → systems must update
- **Impact propagates**: "TSI 4.2.1 changed" → which national rules affected? → which company standards? → which IT systems?
- **Cross-border operations**: trains cross national boundaries — a single vehicle must comply with multiple national implementations of the same EU directive simultaneously
- **Multimodal and multi-domain**: regulations cover rail, bus, tram, cable cars, ships — as well as technical specifications for vehicles, infrastructure, procurement, maintenance, and passenger information
- **6–7 levels deep**: significantly deeper than most other regulated industries

Layers 2 (Rules) and 3 (Change Impact) are generic and reusable for other sectors (automotive, energy, banking). The cascade model with its conformance constraints is the railway-specific USP.

### 1.2 Goals

| Priority | Goal |
|----------|------|
| G-1 | Make internal IT governance of railway companies machine-readable and deterministic |
| G-2 | Model the regulatory cascade (EU → National → Agency → Industry → Company) with conformance constraints |
| G-3 | Support cross-border operations: one system complying with multiple national implementations simultaneously |
| G-4 | Verbatim quoting of every rule from its source document |
| G-5 | Schema validation against NIST OSCAL JSON Schema + railway-specific constraints |
| G-6 | Stable identifiers for rules to enable diff and change tracking across versions |
| G-7 | Applicability logic (Rules Layer): determine which controls apply in which context |
| G-8 | Change Impact: structured notifications when regulations are updated, with impact propagation across cascade levels |
| G-9 | Assessment: compliance verification by AI agents and human reviewers |
| G-10 | Extensibility across domains: vehicles, infrastructure, procurement, maintenance, passenger information |
| G-11 | Multimodal: rail, bus, tram, cable cars, ships |
| G-12 | Multilingual support (DE/FR/IT/EN) |

### 1.3 Stakeholders

| Role | Organisation | Interest |
|------|-------------|----------|
| Railway companies | SBB, DB, ÖBB, SNCF, ... | Publish internal governance as machine-readable catalogs; manage regulatory cascade |
| IT & Engineering departments | All railways | Comply with regulations across vehicles, infrastructure, procurement, maintenance, passenger info |
| Compliance teams | All railways | Track regulatory changes across cascade levels; cross-border conformance |
| Standards bodies | KKI, BAV (CH), EBA (DE), ERA (EU) | Potential future upstream: publish regulations in machine-readable format |
| AI agent developers | All railways | Consume catalogs for automated compliance verification |
| OpenRail Association | OpenRail | Host and maintain as OSS project |

---

## 2. Architecture Constraints

### 2.1 Technical Constraints

| ID | Constraint | Rationale |
|----|-----------|-----------|
| TC-1 | Output must be valid NIST OSCAL (JSON Schema v1.2.1) | Interoperability with existing OSCAL tooling |
| TC-2 | Rule text must be verbatim from source document | Auditability, no paraphrasing |
| TC-3 | Rule IDs derived from chapter numbers, not page numbers | Stability across document versions |
| TC-4 | No LLM required for extraction pipeline | Deterministic, reproducible results |
| TC-5 | Source files (PDF, Excel) remain canonical | OSCAL4Rail is derived, not authoritative |

### 2.2 Organisational Constraints

| ID | Constraint | Rationale |
|----|-----------|-----------|
| OC-1 | License: Apache 2.0 | OpenRail Association OSS standard |
| OC-2 | NIST OSCAL base: CC0 1.0 (public domain) | No license conflict |
| OC-3 | Language of catalogs follows source document | DE/FR/IT separate catalogs |

### 2.3 Conventions

- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- Semantic Versioning for catalog releases (Major.Minor.Patch)
- GitHub Flow (feature branch → PR → merge to main)

---

## 3. System Scope and Context

### 3.1 Business Context

```
                    REGULATORY CASCADE
                    ==================
┌──────────────┐
│  EU (ERA)    │──TSI──┐
└──────────────┘       │
┌──────────────┐       ▼
│  National    │──Law──┐    ┌─────────────────────────────────────────┐
│  (EBA/BAV)   │       │    │            OSCAL4Rail Framework          │
└──────────────┘       ▼    │                                         │
┌──────────────┐       ┌───▶│  Layer 1: Catalog (NIST OSCAL Profile)  │
│  Industry    │──Std──┤    │  Layer 2: Rules (Rulemapping format)    │──▶ AI Agents
│  (KKI)       │       │    │  Layer 3: Change Impact (diff/notify)   │──▶ Compliance Teams
└──────────────┘       │    │  Layer 4: Assessment (Plan/Results)      │──▶ IT Systems
┌──────────────┐       │    │                                         │
│  Company     │──Ril──┘    │  Cascade: conformance ↓ / impact ↑      │──▶ Change Notifications
│  (DB, SBB)   │            └─────────────────────────────────────────┘
└──────────────┘
```

Cross-border: A train operating DE↔CH↔AT must comply with all three national implementations of the same EU directive simultaneously. OSCAL4Rail models this as parallel cascade branches sharing a common EU parent.

### 3.2 Technical Context

| Interface | Direction | Format | Description |
|-----------|-----------|--------|-------------|
| PDF regulations | Input | PDF | Source regulation documents (until upstream publishes machine-readable) |
| Excel matrix | Input | XLSX | Applicability matrix (v/e/–) |
| Rulemapping artifacts | Input | RUML/XML | Applicability rules (Layer 2) |
| OSCAL Catalog | Output | YAML | Machine-readable regulation catalog |
| Change Notification | Output | YAML | Structured diff between versions |
| Assessment Results | Output | YAML | Compliance findings per system |
| NIST JSON Schema | Validation | JSON Schema | Official OSCAL schema v1.2.1 + OSCAL4Rail constraints |
| Git repository | Storage | Git | Version control, cascade hierarchy, diff |

---

## 4. Solution Strategy

### 4.1 Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Base standard | NIST OSCAL v1.2.1 (all 3 layers) | Mature, public domain, existing tooling ecosystem |
| Tooling foundation | compliance-trestle + oscal-deep-diff | Profile Resolution, Validation, Diff out-of-the-box ([ADR-007](adr/ADR-007-tooling-foundation.md)) |
| Agent interface | compliance-trestle-mcp (MCP Server) | AI agents can invoke all OSCAL operations via standardized protocol |
| Cascade model | OSCAL Profile chain (not custom schema) | Each cascade level = one Profile selecting from upstream Catalog |
| Cross-framework linking | OSCAL Control Mapping (v1.2.0+) | Built-in coverage + gap-summary, solves multilingual |
| Change detection | oscal-deep-diff + railway semantics | NIST tool for structural diff, own layer for tightened/relaxed classification |
| Railway extensions | OSCAL props with `ns="https://github.com/OpenRailAssociation/oscal4rail/ns"` | Standard extension mechanism, no schema fork |
| Extraction method | Deterministic (markitdown + openpyxl) | Reproducible, auditable, no LLM required |
| Rule identifier | Chapter number (e.g. `bs-ki-2.1`) | Stable across document versions |
| Applicability model | OSCAL `props` with `class` attribute | Schema-compliant, extensible |
| Version strategy | One file per regulation, Git history for diffs | Leverages existing tooling |

### 4.2 Quality Approach

- **Correctness:** Verbatim quotes, no paraphrasing
- **Completeness:** All matrix rows covered
- **Validity:** Continuous validation against NIST JSON Schema (via trestle)
- **Traceability:** Every rule references source chapter and document
- **Assessability:** Every control can be verified by agent or human reviewer

---

## 5. Building Block View

### 5.1 Level 1 – 4-Layer Architecture + Tooling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OSCAL4Rail Framework                                │
├─────────────────┬──────────────────┬────────────────┬───────────────────────┤
│  Layer 1        │  Layer 2         │  Layer 3       │  Layer 4              │
│  CATALOG        │  RULES           │  CHANGE IMPACT │  ASSESSMENT           │
│                 │                  │                │                       │
│  NIST OSCAL     │  Rulemapping     │  oscal-deep-   │  NIST OSCAL           │
│  Catalog +      │  format          │  diff + railway│  Assessment Results   │
│  Profile +      │  (not in NIST)   │  semantics     │  + Railway Profile    │
│  Mapping        │                  │  (NIST + own)  │                       │
├─────────────────┼──────────────────┼────────────────┼───────────────────────┤
│  Catalog Model  │  Applicability   │  Structural    │  Assessment Plan      │
│  Profile Model  │  Rules           │  Diff (NIST)   │  Assessment Results   │
│  Control Mapping│  Context Filters │  Semantic      │  POA&M                │
│  Component Def. │  AMC Refs        │  Classification│  Component Definition │
└─────────────────┴──────────────────┴────────────────┴───────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ compliance-     │  │ oscal-deep-diff  │  │ trestle-mcp      │
│ trestle         │  │ (NIST, Node.js)  │  │ (MCP Server)     │
│ (Python)        │  │                  │  │                  │
│ - Import        │  │ - JSON diff      │  │ - AI Agent API   │
│ - Validate      │  │ - JSON Pointers  │  │ - All trestle    │
│ - Profile Res.  │  │ - Matcher config │  │   operations     │
│ - Split/Merge   │  │                  │  │   via MCP        │
│ - Plugin host   │  │                  │  │                  │
└─────────────────┘  └──────────────────┘  └──────────────────┘
         │
         ▼
┌─────────────────┐
│ trestle-        │
│ oscal4rail      │
│ (Railway Plugin)│
│                 │
│ - cascade       │
│ - semantic diff │
│ - assess        │
│ - rail-validate │
└─────────────────┘
```

### 5.2 Level 2 – Tooling Components

| Component | Responsibility | Technology | Status |
|-----------|---------------|-----------|--------|
| `compliance-trestle` | OSCAL workspace, validation, profile resolution | Python (pip) | ✅ Evaluated |
| `oscal-deep-diff` | Structural diff between OSCAL documents | Node.js (GitHub) | ✅ Evaluated |
| `trestle-mcp` | MCP Server for AI agent integration | Python | 🔜 To evaluate |
| `trestle-oscal4rail` | Railway-specific plugin (cascade, semantic diff, assessment) | Python | 🔜 To build |
| `parse_matrix` | Parse Excel Bewertungsmatrix → applicability per rule | openpyxl | ✅ Exists |
| `extract_pdf` | Extract verbatim text per chapter from regulation PDF | markitdown / pdfplumber | ✅ Exists |
| `build_catalog` | Merge matrix + PDF texts into OSCAL Catalog YAML | PyYAML | ✅ Exists |

### 5.3 Level 2 – Agentic Assessment Flow

```
┌──────────┐    ┌───────────────┐    ┌──────────────┐    ┌─────────────────┐
│ AI Agent │───▶│ trestle-mcp   │───▶│ compliance-  │───▶│ OSCAL Workspace │
│ (Claude, │    │ (MCP Server)  │    │ trestle      │    │                 │
│  GPT,    │    │               │    │              │    │ catalogs/       │
│  custom) │    │ resolve_prof  │    │ profile-     │    │ profiles/       │
│          │◀───│ assess        │◀───│ resolve      │◀───│ assessment-     │
│          │    │ validate      │    │ validate     │    │   results/      │
└──────────┘    └───────────────┘    └──────────────┘    └─────────────────┘
     │                                                           │
     │  Agent produces:                                          │
     │  - Assessment Results (findings per control)              │
     │  - Evidence references                                    │
     │  - Railway scale (vollständig/teilweise/nicht erfüllt)    │
     └───────────────────────────────────────────────────────────┘
```

### 5.4 Catalog Structure

```
catalog:
  metadata:        # Regulation metadata (title, version, source)
  groups:          # Chapter hierarchy
    - group:       # e.g. "Allgemeine Informationsinhalte"
      controls:    # One control per regulation rule
        - control:
          parts:   # statement (verbatim), guidance (AB/Anhang)
          props:   # source-chapter, applicability per channel×transport
  back-matter:     # Linked resources (transition documents, supplements)
    resources:
```

---

## 6. Runtime View

### 6.1 Extraction Pipeline (new catalog version)

```
1. Download new PDF + XLSX from standards body
2. run: python3 extract.py --pdf BS-KI_DE.pdf --matrix Matrix_BS-KI_DE.xlsx
3. Output: catalogs/bs-ki/de/bs-ki-de.yaml
4. run: trestle validate -a  →  ✅ VALID
5. git diff  →  shows changed rules at control level
6. run: oscal-deep-diff --config diff-config.yaml  →  structured change notification
7. git commit -m "feat(bs-ki): update to v2.0"
8. git tag bs-ki/v2.0
```

### 6.2 Agentic Assessment (primary use case)

```
Agent receives task: "Assess system X against BS-KI"

1. Agent calls MCP: trestle.import_profile("sbb-subset-bs-ki")
2. Agent calls MCP: trestle.profile_resolve("sbb-subset") → resolved catalog (5 controls)
3. For each control in resolved catalog:
   a. Agent reads control statement + applicability props
   b. Agent queries system evidence (config, docs, APIs)
   c. Agent determines: vollständig | teilweise | nicht erfüllt | nicht relevant
   d. Agent records finding with evidence reference
4. Agent calls MCP: trestle.write_assessment_results(findings)
5. Output: assessment-results/system-x-bs-ki.yaml (valid OSCAL Assessment Results)

Human reviewer:
- Reviews agent findings
- Approves, adjusts, or rejects
- Final assessment = human-approved + agent-assisted
```

### 6.3 Change Impact Detection (Layer 3)

```
Input: bs-ki-v1.yaml, bs-ki-v2.yaml

1. oscal-deep-diff produces structural diff:
   {
     "changes": [
       {"change": "property_changed", "leftPointer": ".../prose", "leftElement": "800", "rightElement": "500"},
       {"change": "property_changed", "leftPointer": ".../props/2/value", "leftElement": "empfohlen", "rightElement": "verbindlich"},
       {"change": "array_changed", "rightOnly": [{"id": "bs-ki-2.99", ...}]}
     ]
   }

2. trestle-oscal4rail classifies each change:
   - prose changed + threshold lowered → "tightened"
   - applicability empfohlen → verbindlich → "tightened"
   - new control → "added"

3. Impact propagation:
   - Which Profiles reference this Catalog? → resolve downstream
   - Which systems have Assessment Results against affected controls? → notify

4. Output: change-notification.yaml (Layer 3 format)
```

### 6.4 Profile Resolution (Cascade)

```
Input: EU TSI Catalog + National Profile

1. trestle import -f tsi-tat-en.yaml -o tsi-tat
2. trestle import -f ch-national-profile.yaml -o ch-national
3. trestle author profile-resolve -n ch-national -o ch-resolved
4. Result: catalogs/ch-resolved/catalog.json
   - Contains only controls selected by CH national law
   - Props from upstream preserved
   - Link rel="resolution-source" to TSI catalog
   - Railway props: cascade-level=national, conformance-constraint=specializes
```

---

## 7. Deployment View

### 7.1 Current (Hack4Rail 2026)

```
Developer machine
├── catalogs/bs-ki/de/bs-ki-de.yaml  (OSCAL4Rail Catalog)
├── schemas/*.json                   (NIST OSCAL v1.2.1 Schemas)
├── tools/validate.py                (multi-model validator)
└── GitHub repository                (version control + collaboration)
```

### 7.2 Target (OSS project)

```
GitHub (OpenRail-Playground/OSCAL4Rail)
├── .github/workflows/
│   └── validate.yml        (CI: validate all catalogs on every PR)
├── catalogs/
│   ├── bs-ki/de/           (CH passenger info standard)
│   ├── bs-ki/fr/
│   ├── tsi-tat/            (EU TSI Telematics)
│   └── ...
├── schema/
│   └── oscal-catalog.json  (NIST schema, pinned version)
├── tools/
│   ├── extract.py
│   ├── validate.py
│   └── diff.py
└── docs/
    └── arc42.md            (this document)
```

---

## 8. Cross-cutting Concepts

### 8.1 Verbatim Quoting

Every `statement` part in every control contains the **exact text** from the source document. No paraphrasing, no summarisation. This is a hard invariant.

### 8.2 Stable Identifiers

Control IDs are derived from the chapter number of the source document:

```
<regulation-prefix>-<chapter.section>[-<context>]

Examples:
  bs-ki-2.1                    # Aktuelle Uhrzeit (all contexts)
  bs-ki-3.6-fahrt              # Liniennummer in "Informationen zur Fahrt" context
```

Page numbers are NOT used as identifiers – they change with every reformatting.

### 8.3 Applicability Model

Every rule specifies its obligation per channel × transport mode as OSCAL `props`:

```yaml
- name: applicability
  value: verbindlich | empfohlen | nicht-relevant
  class: <channel>.<transport-mode>
  remarks: "optional: v e distinction abgeltungsberechtigt vs. eigenwirtschaftlich"
```

Channels: `haltestelle`, `fahrzeug-aussen.front/seite/heck`, `fahrzeug-innen`, `daten.einlieferung`
Transport modes: `bahn`, `bus-tram-metro`, `schiff`, `seilbahn`

### 8.4 Versioning

- One YAML file per regulation per language
- Old versions archived in `history/` before update
- Git diff shows changes at control level
- Tags: `<regulation>/<version>` (e.g. `bs-ki/v1.0`)

---

## 9. Architecture Decisions

### ADR-001: Use NIST OSCAL as base standard

**Status:** Accepted

**Context:** We need a machine-readable format for railway regulations that is interoperable, validatable, and extensible.

**Decision:** Use NIST OSCAL Catalog model as the base format.

**Consequences:** (+) Public domain, existing tooling, formal JSON Schema. (-) Originally designed for IT security controls, requires railway-specific extensions via `props`.

---

### ADR-002: Deterministic extraction without LLM

**Status:** Accepted

**Context:** Extraction of rules must be reproducible and auditable.

**Decision:** Use deterministic tools only: markitdown (PDF → text), openpyxl (Excel), regex (chapter detection). No LLM in the core pipeline.

**Consequences:** (+) Reproducible, auditable, no API costs. (-) Chapter structure detection requires manual mapping for edge cases.

---

### ADR-003: Chapter number as stable identifier

**Status:** Accepted

**Context:** Rule IDs must remain stable across document versions to enable semantic diff.

**Decision:** Derive control IDs from chapter numbers, not page numbers or document-internal IDs.

**Consequences:** (+) Stable across reformatting and minor updates. (-) Breaks if regulation authors renumber chapters (rare, but possible).

---

### ADR-004: One catalog file per regulation per language

**Status:** Accepted

**Context:** BS-KI exists in DE/FR/IT. TSI in EN + translations.

**Decision:** Separate YAML files per language. Cross-language linking via OSCAL Control Mapping (future).

**Consequences:** (+) Simple, independent validation per language. (-) No automatic cross-language consistency check yet.

---

### ADR-007: compliance-trestle + oscal-deep-diff as tooling foundation

**Status:** Proposed

**Context:** OSCAL4Rail needs tooling for validation, profile resolution, change detection, and AI agent integration. Building everything from scratch is expensive and duplicates existing work.

**Decision:** Use compliance-trestle (Python, Apache 2.0) as primary tooling platform with plugin architecture. Use oscal-deep-diff (NIST, public domain) for structural diff. Railway-specific logic as trestle plugin (`trestle-oscal4rail`).

**Consequences:** (+) Profile Resolution, Validation, MCP Server work out-of-the-box. Plugin architecture proven (FedRAMP). (-) Two runtimes (Python + Node.js). Dependency on external project governance.

Full ADR: [docs/adr/ADR-007-tooling-foundation.md](adr/ADR-007-tooling-foundation.md)

---

## 10. Quality Requirements

### 10.1 Quality Tree

| Quality | Scenario | Measure |
|---------|----------|---------|
| Correctness | Every statement matches source PDF | Manual spot-check + verbatim quote |
| Completeness | All matrix rows covered | Automated: control count = matrix row count |
| Validity | Every catalog passes NIST schema | CI validation on every commit |
| Stability | IDs survive document reformatting | Chapter-based IDs, not page-based |
| Traceability | Every rule links to source | `source-chapter` + `source-document` props |
| Extensibility | New regulations added without breaking existing | Independent files, shared schema |

---

## 11. Risks and Technical Debt

| ID | Risk | Probability | Impact | Mitigation |
|----|------|------------|--------|------------|
| R-1 | Standards bodies renumber chapters | Low | High | Monitor chapter structure on each update |
| R-2 | PDF formatting breaks extraction | Medium | Medium | Manual review of extracted text |
| R-3 | OSCAL schema version update breaks validation | Low | Medium | Pin schema version, migrate on major OSCAL releases |
| R-4 | Adoption without standards body buy-in | Medium | High | OpenRail Association as sponsor, demonstrate value first |
| TD-1 | No automated cross-language consistency | – | Medium | Future: OSCAL Control Mapping |
| TD-2 | No CI/CD pipeline yet | – | Low | Add GitHub Actions workflow |

---

## 12. Glossary

| Term | Definition |
|------|-----------|
| OSCAL | Open Security Controls Assessment Language (NIST standard) |
| OSCAL4Rail | Lightweight OSCAL Catalog profile for railway regulations |
| Control | A single regulation rule in OSCAL terminology |
| Group | A chapter or section grouping controls |
| Statement | The verbatim rule text (primary content of a control) |
| Guidance | Supplementary text (Ausführungsbestimmungen, Anhänge) |
| Back-matter | Linked resources (transition documents, supplements) |
| Applicability | Obligation level (verbindlich/empfohlen) per channel × transport mode |
| BS-KI | Branchenstandard Kundeninformation (Swiss passenger info standard) |
| TSI | Technical Specification for Interoperability (EU railway standard) |
| KKI | Nationale Kommission Kundeninformation (CH standards body) |
| BAV | Bundesamt für Verkehr (Swiss Federal Office of Transport) |
| ERA | European Union Agency for Railways |
| AB | Ausführungsbestimmung (implementing regulation) |
| Control Mapping | OSCAL model for cross-referencing between catalogs |
