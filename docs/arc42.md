# OSCAL4Rail – Architecture Documentation (arc42)

> **Version:** 0.3.0 (2026-11-05 – synced with ADR-001…ADR-019)
> **License:** CC0 1.0 Universal (public domain)
> **Inspired by:** Arpad Vasarhelyi
>
> **Maintenance note:** Chapter 9 is the master list of all architecture decisions.
> Every new or accepted ADR under [`docs/adr/`](adr/) MUST be entered in the table in
> §9. A CI check (`tools/check_arc42_adr_sync.py`) enforces that every `ADR-*.md` is
> referenced here, so this document stays current by construction.

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
| TC-1 | Output must be valid NIST OSCAL, pinned to a single version via `schemas/nist/manifest.json` (currently **v1.2.3**) | Interoperability with existing OSCAL tooling; version drift structurally excluded ([ADR-008](adr/ADR-008-reproducible-schema-acquisition.md)) |
| TC-2 | Rule text must be verbatim from source document | Auditability, no paraphrasing |
| TC-3 | Rule IDs derived from chapter numbers, not page numbers | Stability across document versions ([ADR-003](#adr-003-chapter-number-as-stable-identifier)) |
| TC-4 | No LLM required for extraction pipeline | Deterministic, reproducible results ([ADR-002](#adr-002-deterministic-extraction-without-llm)) |
| TC-5 | Source files (PDF, Excel) remain canonical | OSCAL4Rail is derived, not authoritative |
| TC-6 | NIST base schemas fetched reproducibly as release assets + SHA256, never hand-copied | Reproducible, exactly versioned, no drift ([ADR-008](adr/ADR-008-reproducible-schema-acquisition.md)) |
| TC-7 | YAML is the canonical serialization; JSON/XML are generated via official OSCAL tools, never hand-maintained | Single Source of Truth, owner/diff readability ([ADR-012](adr/ADR-012-canonical-serialization.md)) |

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
│  Industry    │──Std──┤    │  Layer 2: Rules (OSCAL-native, ADR-018) │──▶ AI Agents
│  (KKI)       │       │    │  Layer 3: Change Impact (OSCAL Mapping)  │──▶ Compliance Teams
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
| Rule-set (Layer 2) | Output | YAML | OSCAL-native decision logic, separate linked artifact (ADR-018) |
| OSCAL Catalog | Output | YAML | Machine-readable regulation catalog |
| Change Notification | Output | YAML | OSCAL Mapping (mapping-collection) between versions (ADR-019) |
| Assessment Results | Output | YAML | Compliance findings per system |
| NIST JSON Schema | Validation | JSON Schema | Official OSCAL schema v1.2.1 + OSCAL4Rail constraints |
| Git repository | Storage | Git | Version control, cascade hierarchy, diff |

---

## 4. Solution Strategy

### 4.1 Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Base standard | NIST OSCAL, pinned to one version via manifest (currently v1.2.3, all 3 layers) | Mature, public domain, existing tooling; no drift ([ADR-008](adr/ADR-008-reproducible-schema-acquisition.md)) |
| Schema acquisition | Fetch official release assets + SHA256 verify (`tools/fetch_oscal_schemas.py`); `make schemas` as audit fallback | Minimal, portable, reproducible ([ADR-008](adr/ADR-008-reproducible-schema-acquisition.md)) |
| Canonical serialization | YAML leading; JSON/XML generated via official OSCAL tools | SSOT, owner/diff readability ([ADR-012](adr/ADR-012-canonical-serialization.md)) |
| Validation | One consolidated two-pass validator (`tools/validate.py`): NIST base + auto-mapped O4R constraints, report beside the file (MD+JSON) | Single CI pass/fail, coverage gaps observable ([ADR-013](adr/ADR-013-validator-consolidation.md)) |
| Tooling foundation | compliance-trestle + oscal-deep-diff | Profile Resolution, Validation, Diff out-of-the-box ([ADR-007](adr/ADR-007-tooling-foundation.md)) |
| Agent interface | compliance-trestle-mcp (MCP Server) | AI agents can invoke all OSCAL operations via standardized protocol |
| Cascade model | OSCAL Profile chain (not custom schema) | Each cascade level = one Profile selecting from upstream Catalog |
| Cross-framework linking | OSCAL Control Mapping (v1.2.0+) | Built-in coverage + gap-summary, solves multilingual |
| Change detection | VCS-native (Git refs) + OSCAL Mapping output | L3 interprets a Git change; the report is an OSCAL `mapping-collection`, classification from the L2 semantics axis ([ADR-019](adr/ADR-019-change-layer-vcs-native.md)) |
| Railway extensions | OSCAL props with `ns="https://github.com/OpenRailAssociation/oscal4rail/ns"` | Standard extension mechanism, no schema fork |
| Extraction method | Deterministic (markitdown + openpyxl) | Reproducible, auditable, no LLM required |
| Rule identifier | Chapter number (e.g. `bs-ki-2.1`) | Stable across document versions |
| Applicability model | OSCAL `props` with `class` attribute | Schema-compliant, extensible |
| Rules Layer placement | Separate linked logic artifact (`link rel="decision-logic"`), not inline | Catalog stays pure NIST OSCAL; logic format swappable ([ADR-014](adr/ADR-014-rules-layer-placement.md)) |
| Rules/catalog version coupling | Reuse NIST `metadata.version`; related artifacts MUST share the same value; equality enforced by the validator | Deterministic, auditable; no new schema construct ([ADR-014](adr/ADR-014-rules-layer-placement.md)) |
| Rules format selection | Weighted school-grade grid over 9 candidates (format vs. hosted tool kept separate); conclusion "build the own format"; specified OSCAL-native | Traceable evidence base; own format realized ([ADR-016](adr/ADR-016-rules-format-decision-criteria.md), [ADR-018](adr/ADR-018-rules-format-oscal-native.md)) |
| Metadata model | One adaptive schema, 4 orthogonal dimensions (theme, cascade, applicability, lifecycle) | One schema for the whole sector, adaptable per country/company ([ADR-009](adr/ADR-009-adaptive-metadata-model.md)) |
| Authority model | Configurable authority meta-model: parallel streams, typed many-to-many relations, expresses overlap/conflict | Reflects real rail authority; framework prescribes no structure ([ADR-010](adr/ADR-010-configurable-authority-meta-model.md)) |
| Corpus index | Single generated `index.json` (heads only, no controls), derived from catalog metadata | Assessment over the whole corpus without opening every catalog ([ADR-011](adr/ADR-011-generated-catalog-index.md)) |
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
│  NIST OSCAL     │  OSCAL-native    │  OSCAL Mapping │  NIST OSCAL           │
│  Catalog +      │  param/constraint│  Model (NIST)  │  Assessment Results   │
│  Profile +      │  /test (ADR-018) │  VCS-native    │  + Railway Profile    │
│  Mapping        │  (not in NIST)   │  (ADR-019)     │                       │
├─────────────────┼──────────────────┼────────────────┼───────────────────────┤
│  Catalog Model  │  Applicability   │  Git change →  │  Assessment Plan      │
│  Profile Model  │  Rules           │  mapping-coll. │  Assessment Results   │
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
| `tools/fetch_oscal_schemas.py` | Fetch pinned NIST schemas as release assets + SHA256 verify ([ADR-008](adr/ADR-008-reproducible-schema-acquisition.md)) | Python | ✅ Exists |
| `tools/validate.py` | Consolidated two-pass validator: NIST base + auto-mapped O4R constraints, report beside file (MD+JSON) ([ADR-013](adr/ADR-013-validator-consolidation.md)) | Python (`jsonschema`) | ✅ Exists |
| `tools/generate_doc.py` | Round-trip generator: OSCAL YAML → human-readable document for owner verification | Python | ✅ Exists |
| `parse_matrix` | Parse Excel Bewertungsmatrix → applicability per rule | openpyxl | ✅ Exists (extraction) |
| `extract_pdf` | Extract verbatim text per chapter from regulation PDF | markitdown / pdfplumber | ✅ Exists (extraction) |
| `build_catalog` | Merge matrix + PDF texts into OSCAL Catalog YAML | PyYAML | ✅ Exists (extraction) |

> **Note.** The PoC extraction scripts (`parse_matrix`, `extract_pdf`, `build_catalog`)
> live in the DB-internal PoC repository; the framework repo ships the version-controlled
> tooling above. A standalone `oscal4rail` CLI (`validate|diff|assess|rules`) is the
> consolidation target for v1.0.0.

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
2. run extraction (PoC scripts) → verbatim catalog YAML
3. Output: catalogs/bs-ki/de/bs-ki-de.yaml  (YAML is canonical, ADR-012)
4. run: python3 tools/validate.py <file>  →  two-pass (NIST + O4R), report beside file (ADR-013)
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
Input: two states of the catalog (+ optional rule-set), via Git refs or files

1. tools/change reads source and target (git show <ref>:<path>, or --from/--to):
   no diff is re-implemented — Git provides "what changed" (ADR-019 D1/D2).

2. Classify per control-id, from the L2 semantics axis (ADR-019 D3/§4.4):
   - status.lifecycle active → deprecated          → "deprecated" (lifecycle)
   - modality.rank decreased (weaker → stronger)   → "tightened"  (strength)
   - control present in target only                → "added"      (existence)
   precedence lifecycle > strength > existence; no L2 → only added/removed/content-changed.

3. Emit an OSCAL mapping-collection (the change report):
   each control-level change is one map; category on map/@relationship (O4R ns);
   changed-field + old/new values as O4R props. Validates two-pass (NIST + O4R).

4. Consume (consumer side, not the framework): a CI/merge pipeline step, a scheduled
   job, or an agent reads the mapping and triggers a reaction under its own policy
   (ADR-019 D4/D6). The report is both the human-readable report and the agent diff.
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
GitHub (OpenRailAssociation/oscal4rail)   ← migrated from OpenRail-Playground/A38
├── .github/workflows/
│   └── validate.yml        (CI: validate all catalogs on every PR — planned, #14)
├── catalogs/
│   ├── bs-ki/de/           (CH passenger info standard)
│   ├── bs-ki/fr/
│   ├── tsi-tat/            (EU TSI Telematics)
│   └── ...
├── examples/
│   ├── profiles/          (cascade profile examples, ADR cascade spec)
│   ├── mappings/          (cross-framework Control Mapping examples)
│   └── multilingual/      (multilingual model examples, ADR-017)
├── schemas/
│   ├── nist/               (fetched NIST schemas, pinned v1.2.3 + manifest, ADR-008)
│   └── oscal4rail/         (additive O4R constraint schemas, Framework ≠ Content)
├── tools/
│   ├── fetch_oscal_schemas.py   (ADR-008)
│   ├── validate.py              (consolidated two-pass, ADR-013)
│   └── generate_doc.py          (round-trip generator)
└── docs/
    └── arc42.md            (this document)
```

> The repository has been migrated to the standalone **`OpenRailAssociation/oscal4rail`**
> (OpenRail Incubation). The CI validation workflow is planned ([ADR-013](adr/ADR-013-validator-consolidation.md),
> issue #14); a separate docs-consistency check (`tools/check_arc42_adr_sync.py`) keeps this
> document in sync with the ADR set.

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
- **Version coupling across layers:** related artifacts (catalog, rules, assessment)
  MUST carry the same NIST `metadata.version` value. Equality is enforced by the
  validator as an error, not a schema construct, so the layers can never drift apart
  ([ADR-014](adr/ADR-014-rules-layer-placement.md)).

### 8.5 Serialization (YAML canonical)

YAML is the single canonical serialization for all OSCAL4Rail instance artifacts; it is
the SSOT and the only form edited or reviewed by hand. JSON and XML are **generated** on
demand from the YAML via official OSCAL tools (`oscal-cli convert`, `compliance-trestle`),
never hand-maintained. One JSON Schema validates all three serializations because they
share the same model ([ADR-012](adr/ADR-012-canonical-serialization.md)).

### 8.6 Reproducible Schemas (no drift)

NIST base schemas are fetched as official release assets and verified against stored
SHA256 checksums, pinned to one release tag in `schemas/nist/manifest.json` (SSOT). A
version bump is a conscious, traceable commit. NIST base (`schemas/nist/`) and additive
O4R constraints (`schemas/oscal4rail/`) are kept strictly separate (Framework ≠ Content)
([ADR-008](adr/ADR-008-reproducible-schema-acquisition.md)).

### 8.7 Adaptive Metadata and Configurable Authority

The metadata head decomposes into four orthogonal dimensions — theme, cascade level,
applicability, lifecycle/provenance — so one schema serves the whole sector yet adapts
per country, company, and vehicle series without forking
([ADR-009](adr/ADR-009-adaptive-metadata-model.md)). Authority is modeled not as one
ladder but as **parallel streams** (statutory, normative, sectoral, corporate, vendor)
with typed many-to-many relations that can express overlap, redundancy, and conflict —
the framework prescribes no fixed structure ("Framework ≠ Usage")
([ADR-010](adr/ADR-010-configurable-authority-meta-model.md)).

### 8.8 Catalog Index

A single generated `index.json` lists one entry per catalog (heads only, no control
bodies), derived from the catalogs' `metadata`. It lets the Assessment Layer operate over
a large corpus without opening every catalog and is never hand-maintained
([ADR-011](adr/ADR-011-generated-catalog-index.md)).

### 8.9 Multilingual Model

Multiple language versions are the **same** requirement expressed in different languages,
never an additional rule: identity lives in the stable, chapter-based control ID, not in
the text. The framework never translates and never judges equivalence — that is the
owner's editorial act (Meaningful Human Control). When versions can diverge, the owner may
mark which language governs with an optional `reference-language` prop (a single ISO 639
code, or `all` when every version is equally authoritative, e.g. an EU act). Structural
patterns are specified in `docs/reference/catalog-format.md` §8; worked examples live under
`examples/multilingual/` ([ADR-017](adr/ADR-017-multilingual-reference-language.md), [ADR-004](#adr-004-one-catalog-file-per-regulation-per-language)).

---

## 9. Architecture Decisions

All architecture decisions are recorded as ADRs under [`docs/adr/`](adr/). **This table
is the master list** — every ADR file MUST appear here, enforced by
`tools/check_arc42_adr_sync.py` (CI). The embedded summaries below (ADR-001…004, 007)
are kept for readability; the authoritative text is the linked ADR file.

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Use NIST OSCAL as base standard | Accepted | — (embedded below) |
| ADR-002 | Deterministic extraction without LLM | Accepted | — (embedded below) |
| ADR-003 | Chapter number as stable identifier | Accepted | — (embedded below) |
| ADR-004 | One catalog file per regulation per language | Accepted | — (embedded below) |
| [ADR-005](adr/ADR-005-law-as-code-relationship.md) | Relationship to Law-as-Code Initiatives (SPRIND/Rulemapping/OpenCode) | Accepted | 2026-06-25 |
| [ADR-006](adr/ADR-006-oscal4rail-vs-rulemapping.md) | OSCAL4Rail and Rulemapping — Complementarity or Competition? | Accepted (amended by ADR-014) | 2026-06-25 |
| [ADR-007](adr/ADR-007-tooling-foundation.md) | compliance-trestle + oscal-deep-diff as tooling foundation (Framework ≠ Content) | Proposed | 2026-08-03 |
| [ADR-008](adr/ADR-008-reproducible-schema-acquisition.md) | Reproducible Schema Acquisition and OSCAL Version Policy (pinned v1.2.3) | Accepted | 2026-09-29 |
| [ADR-009](adr/ADR-009-adaptive-metadata-model.md) | Adaptive Metadata Model (one schema, 4 orthogonal dimensions) | Proposed (Draft) | 2026-10-01 |
| [ADR-010](adr/ADR-010-configurable-authority-meta-model.md) | Configurable Authority Meta-Model (parallel streams, many-to-many) | Proposed (Draft) | 2026-10-01 |
| [ADR-011](adr/ADR-011-generated-catalog-index.md) | Generated Catalog Index (`index.json`) | Proposed (Draft) | 2026-10-01 |
| [ADR-012](adr/ADR-012-canonical-serialization.md) | Canonical Serialization — YAML leading, JSON/XML generated | Accepted | 2026-10-16 |
| [ADR-013](adr/ADR-013-validator-consolidation.md) | Consolidated Validator (two-pass, auto-mapped O4R constraints, report beside file) | Accepted | 2026-10-20 |
| [ADR-014](adr/ADR-014-rules-layer-placement.md) | Rules-Layer Placement — separate linked logic artifact, version-coupled via `metadata.version` | Accepted | 2026-10-27 |
| [ADR-015](adr/ADR-015-oscal-agent-tooling-landscape.md) | OSCAL AI-Agent Tooling Landscape — Adopt vs. Reference | Proposed | 2026-10-27 |
| [ADR-016](adr/ADR-016-rules-format-decision-criteria.md) | Decision Criteria and Scoring Method for the Rules-Layer Format Selection | Accepted (format decision deferred to a later ADR) | 2026-10-27 / 2026-10-29 |
| [ADR-017](adr/ADR-017-multilingual-reference-language.md) | Multilingual Model: same rule across languages, optional `reference-language` marker | Accepted | 2026-10-27 |
| [ADR-018](adr/ADR-018-rules-format-oscal-native.md) | Rules-Layer Format — OSCAL-native via `parameter/constraint/test` + Control Mapping; fields convention, Metapath Subset v1, status lifecycle axis | Accepted | 2026-11-05 |
| [ADR-019](adr/ADR-019-change-layer-vcs-native.md) | Change Impact Layer (L3) — VCS-native interpretation; the report is an OSCAL artifact (NIST Mapping Model) under the OSCAL4Rail schema; tools validate form not content | Accepted | 2026-11-05 |

> **Note.** The Rules-Layer (Layer 2) format decision is settled: [ADR-016](adr/ADR-016-rules-format-decision-criteria.md)
> fixed the evaluation grid and concluded "build the own format, do not adopt";
> [ADR-018](adr/ADR-018-rules-format-oscal-native.md) is the own-format specification
> (OSCAL-native). The Change Impact Layer (Layer 3) is specified in
> [ADR-019](adr/ADR-019-change-layer-vcs-native.md): a VCS-native interpretation whose
> report is itself an OSCAL artifact (a NIST Mapping Model) under the OSCAL4Rail schema.

### Embedded summaries

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
| R-3 | OSCAL schema version update breaks validation | Low | Medium | Pinned via `schemas/nist/manifest.json` (v1.2.3), conscious bump + checksum update ([ADR-008](adr/ADR-008-reproducible-schema-acquisition.md)) |
| R-4 | Adoption without standards body buy-in | Medium | High | OpenRail Association as sponsor, demonstrate value first |
| TD-1 | No automated cross-language consistency | – | Medium | Future: OSCAL Control Mapping |
| TD-2 | No artifact-validation CI pipeline yet | – | Low | Planned GitHub Actions workflow (issue #14); consolidated validator ready ([ADR-013](adr/ADR-013-validator-consolidation.md)) |
| TD-3 | `oscal-cli convert` YAML↔JSON↔XML roundtrip not yet verified end-to-end in this repo | – | Low | Verify and wire into CI ([ADR-012](adr/ADR-012-canonical-serialization.md), #5/#14) |
| TD-4 | Hard `oscal-version` enforcement deferred; currently reported, not enforced | – | Low | BS-KI (`1.1.3`) to be revised against final Catalog Railway Profile, then enforce ([ADR-013](adr/ADR-013-validator-consolidation.md)) |
| TD-5 | Version-equality check across layers not yet implemented in the validator | – | Medium | Implement in `oscal4rail validate`, enforce in CI as hard failure ([ADR-014](adr/ADR-014-rules-layer-placement.md), #5/#14) |
| TD-6 | Rules-Layer format | – | Resolved | Format selected and specified OSCAL-native ([ADR-016](adr/ADR-016-rules-format-decision-criteria.md) grid, [ADR-018](adr/ADR-018-rules-format-oscal-native.md) spec) |
| TD-7 | ADR-009/010/011 still in Draft (Proposed) | – | Low | Elaborate and move to Accepted as the metadata/authority/index work matures |

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
| Canonical serialization | The single leading, hand-edited form (YAML); JSON/XML are generated ([ADR-012](adr/ADR-012-canonical-serialization.md)) |
| Decision logic | Applicability conditions (AND/OR, thresholds) in a separate linked artifact, not inline ([ADR-014](adr/ADR-014-rules-layer-placement.md)) |
| `metadata.version` | NIST version field reused to couple catalog/rules/assessment to the same version ([ADR-014](adr/ADR-014-rules-layer-placement.md)) |
| Authority stream | A parallel line of regulatory authority (statutory, normative, sectoral, corporate, vendor) ([ADR-010](adr/ADR-010-configurable-authority-meta-model.md)) |
| `index.json` | Generated corpus index (catalog heads only) for the Assessment Layer ([ADR-011](adr/ADR-011-generated-catalog-index.md)) |
| Two-pass validation | NIST base schema pass + additive O4R constraints pass in one validator run ([ADR-013](adr/ADR-013-validator-consolidation.md)) |

---

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
