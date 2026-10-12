# OSCAL4Rail – Foundation Plan

> **Purpose:** Sequenced workflow to deliver the first viable **Foundation for Governance-as-Code** (pitch-ready). Extends the
> [`ISSUES-PLAN.md`](./ISSUES-PLAN.md) (backlog template) with the concrete
> implementation sequence with work packages WP0–WP4.
>
> **Status:** Draft · **Date:** 2026-09-28
> **Scope:** Framework (Project 1, OSS). DB adaptation remains in Project 2 (Governance-as-Code).

---

## Objective (BLUF)

A reproducible, multi-layer capable Governance-as-Code Foundation:
the **Base Schema is always retrieved from the current NIST-OSCAL versions**
(not hand-copied), layered with an additive OSCAL4Rail-Constraints layer, a
**Validation Engine**, a **Regenerator** (OSCAL → human-readable document) and
a **Change Engine** (structured diff with Railway classification).

## Guiding Principles

1. **Import/generate NIST models and express them as Railway profiles — do not rebuild.**
   `L1 Catalog` / `L4 Assessment` = NIST profile; `L2 Rules` = adopt Rulemapping;
   `L3 Change` = new specification (no NIST equivalent).
2. **Schema reproducible from OSCAL release tag** (NIST's metaschema approach) — SSOT + Docs-as-Code.
3. **Framework ≠ Content** ([ADR-007](./adr/ADR-007-tooling-foundation.md)) — no organization-specific
   content in the framework.
4. **Verifiability by design** — the owner verifies the regenerated document, not the YAML.

## Confirmed Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | OSCAL Version | Rolling against **Release Tag** (Default: current stable, currently v1.2.3), no pinned hand copy | Schema always reproducible (core goal) |
| 2 | Engine Line | **Python Core** (jsonschema, minimal/portable); `oscal-cli`/`compliance-trestle` as optional reference | Tech stack principle: minimal, portable, inspectable |
| 3 | Order | Regenerator (WP3) **before** Change Engine (WP4) | Stronger pitch story: "Owner verifies in familiar format" |
| 4 | Start | **WP0** (document-based, no code) | First Principles: Secure foundation factually |

---

## Work Packages

| WP | Title | Result (Definition of Done) | Related Issues |
|----|-------|-------------------------------|----------------|
| **WP0** | Foundation & Research | Metaschema toolchain practically verified; OSCAL version policy documented; EuroSCAL/Law-as-Code landscape mapped | #32; ADR-005/007-update |
| **WP1** | Base Schema reproducible + multi-layer | `tools/fetch-oscal-schemas` retrieves NIST schemas from release tag; `oscal4rail-*-constraints.schema.json` as additive layer; Catalog+Profile+Mapping+Assessment over common NIST base | #23, #26, #27, #32 |
| **WP1b** | Applicability slot (generic) | `docs/reference/applicability-sources.md`: which source-*types* enable "when does what apply" / "what applies to me" / assessment; interface to Rulemapping/OpenCode — **without** org instances | #5 |
| **WP2** | Validation Engine | A consolidated validator (NIST schema **+** O4R constraints), `--strict`, CI-capable exit code; green against real catalogs | #24 |
| **WP3** | Regenerator | OSCAL-Catalog → human-readable document (Markdown, then HTML in DB-UX); roundtrip as contract (Design by Contract) | new |
| **WP4** | Change Engine | Diff based on `oscal-deep-diff` + Railway classification (added/removed/tightened/relaxed/content-changed); `oscal4rail-change.schema.json` only for semantic interpretation | #29, #6, #7 |

## Critical Path

```
WP0 ──▶ WP1 ──▶ WP2 ──▶ WP3 ──▶ WP4
              └──▶ WP1b (parallel after WP1)
```

Without reproducible Base Schema (WP1) no reliable Validation (WP2);
without Validation no trustworthy Regenerator (WP3); the Change Engine (WP4)
builds on validated, versioned catalogs.

---

## Demarcation: "When Does What Apply" / "What Applies to Me" (Framework vs. Content)

The **Framework** defines only the **generic slot** and the **interfaces** — it knows
**no** organization-specific sources. It points to *where* an organization
hooks in sources that enable applicability and assessment.

| Question | Framework provides (generic) | External/organization-specific source (content, NOT in framework) |
|----------|-------------------------------|-------------------------------------------------------------------|
| **When does what apply?** (Applicability) | Rules layer (L2) + interface to external decision logic | Rulemapping/OpenCode; organization-specific process/trigger sources |
| **What applies to me?** (Selection) | Profile resolution (NIST) + rules filter | organization-specific context profile |
| **How do I fulfill it?** (AMC) | AMC schema (L2) | organization-specific evidence / implementation libraries |
| **Do I fulfill it?** (Assessment) | Assessment profile via NIST (L4) | organization-specific verification/evaluation sources |

---

## Note (Project 2 – DB internal, NOT in framework)

> Documented, but intentionally positioned outside the OSS framework (Framework ≠ Content).
> Belongs in `~/work/beta/governance-as-code` according to project map.

- **DB Applicability/Assessment sources** as instantiation of the generic slot from WP1b:
  Proclib processes (trigger "when"), AMCs, Control Story Library (evidence/Assessment).
  → These fill the generic slots; the framework only points to the slot types.

---

## Ecosystem Mapping: EuroSCAL

[EuroSCAL – "The EU Friends of OSCAL"](https://euroscal.eu/) (driven by the
EU projects [MEDINA](https://medina-project.eu/) and [EMERALD](https://www.emerald-he.eu),
Horizon), focus: **automated cybersecurity certification of cloud services**
(e.g. EUCS; ETSI TR 103 305-4 serializes Critical Security Controls as OSCAL).

- **Connection point:** EU community using OSCAL for EU security catalogs — potential
  alliance partner for the EU level of the Regulatory Cascade and for the OpenRail incubation.
- **Demarcation (Devil's Advocate):** EuroSCAL makes **no** sectoral Railway profile and
  **no** Rules/Change layer. It is an **Ecosystem Peer/Consumer**, not a replacement for OSCAL4Rail's USP (4-layer, Regulatory Cascade, Rules, Change, verbatim regenerator).
- **Action:** Include in Law-as-Code landscape ([ADR-005](./adr/ADR-005-law-as-code-relationship.md)-update).

---

## SSOT Note

This directory is the **Single Point of Truth** for OSCAL4Rail (Framework).
Origin: Copy from hackathon stand (`OpenRail-Playground/A38`, subfolder `OSCAL4Rail`).
Target: Initial population of **`OpenRailAssociation/oscal4rail`** (GitHub) after
the OpenRail incubation. Repo conventions initially DB-compliant; adaptation to OpenRail policies
upon migration.

---

> 🤖 This document was created with AI assistance (Art. 50(4) EU AI Act).
