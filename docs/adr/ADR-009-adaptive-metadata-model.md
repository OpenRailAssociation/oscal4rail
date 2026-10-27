# ADR-009: Adaptive Metadata Model — One Schema, Rail-Sector Specific, Jurisdiction- and Organization-Adaptable

**Status:** Proposed (Draft)

**Date:** 2026-10-01

**Deciders:** Jens Grote

**Technical Story:** How to model the metadata (document head) of a regulatory document so that
one schema serves the whole rail sector while adapting per country, per company, and per vehicle
series. Motivated by the build IT Hackathon Berlin 2026 "Governance-as-Code" challenge. A
concrete instantiation against a real corporate rule database is maintained privately by the
adopting organization and is deliberately **not** part of this framework document
(Framework ≠ Content, ADR-007).

---

## Context and Problem Statement

OSCAL4Rail must express the metadata (document head) of a regulatory document — who issued it,
which version, where it applies, which thematic area it belongs to, and where it sits in the
regulatory hierarchy. A naive approach would define one metadata schema per issuing body (one
per railway undertaking, one per infrastructure manager, one per national safety authority).
This does not scale and breaks the Single Source of Truth principle: every border crossing and
every company would fork the schema.

**The central question:** How do we model regulatory metadata so that **a single schema** serves
the entire rail sector, yet can be **used differently** per country, per company, and per vehicle
series — without forking the schema and without contradicting the parent rule?

This question is not generic. It arises **because this is the rail sector.** The adaptivity
requirement is a direct consequence of how railway regulation actually works (see "Why This Is
Rail-Specific" below). A model built "for XYZ" — any domain — would miss the structural features
that make rail governance hard. We are building for Rail.

### Trigger and Empirical Basis

- The build IT Hackathon challenge asked how non-IT authors publish their rules as code and
  verify the result themselves. A key observation: **the document head alone already carries
  most of the governance signal** — issuer, scope, legal space, thematic classification,
  lifecycle — and is typically available in a *field-structured* form, not free text.
- Established corporate rule databases in the sector already solve "one schema, used differently"
  — but as databases and word-processor templates, not as code. Such a system is empirical
  evidence for the pattern OSCAL4Rail formalizes here. The concrete analysis of one such database
  (its field schema, controlled vocabularies, and native "addendum" specialization mechanism) is
  owner-specific content and is kept in the adopting organization's private repository, not here.

### The Four Orthogonal Dimensions

A regulatory document head decomposes into four **independent** axes. The same document carries
one value on each axis, and each axis varies independently of the others. This orthogonality is
the core of the design:

```
Dimension 1  THEME (taxonomy)         thematic classification     SSOT: owner-provided (enum)
Dimension 2  CASCADE (norm hierarchy) cascade-level               SSOT: OSCAL4Rail (enum)
Dimension 3  APPLICABILITY            scope, legal-space, audience  variable per document
Dimension 4  LIFECYCLE / PROVENANCE   version, status, valid-from, change record
```

Worked example (neutral) — an operating directive issued by an infrastructure manager:

| Dimension | Example value |
|---|---|
| Theme | main group "rail operations" / subgroup "operating rules" (from the owner's taxonomy) |
| Cascade | industry / company (a national rail-operations rulebook) |
| Applicability | scope: one infrastructure manager; legal-space: no restriction |
| Lifecycle | a specific version, a valid-from date, status "in force" |

The theme taxonomy is typically a **controlled, machine-readable list** maintained by the issuing
organization. OSCAL4Rail does not author such a list; where one exists, the framework *generates*
an `enum` from the owner's single source of truth. This keeps Framework ≠ Content intact.

---

## Decision Drivers

1. **One schema, not N** — a single metadata schema for the whole rail sector; no per-issuer fork.
2. **Rail-sector fit** — the model must express the structural features of railway regulation,
   not a lowest-common-denominator generic metadata set.
3. **Adaptivity without contradiction** — country/company/vehicle-series specializations must
   only concretize, never contradict the parent (Cascade property (a)).
4. **Orthogonality (MECE)** — theme, cascade, applicability and lifecycle must not be conflated
   into one field.
5. **Framework ≠ Content (ADR-007)** — OSCAL4Rail defines structure; issuing organizations own
   the vocabularies and the rule text. We generate enums from owner SSOTs, we do not author them.
6. **NIST base, unchanged (ADR-008)** — reuse the NIST OSCAL `metadata` assembly; extend only via
   `prop`/`ns`, never fork the base schema.
7. **Verifiability by design** — the head must round-trip back to the form the owner recognizes
   (lossless reconstruction), including local fields.
8. **Data protection** — real rule inventories carry author name/email (PII). The model places
   these in `parties`/`responsible-party`, and any bulk import must honor an anonymized/full split.

---

## Why This Is Rail-Specific (not a generic metadata model)

The adaptivity requirement is **caused** by properties of the rail sector. Each driver below maps
to a concrete modeling consequence, and to a Regulatory Cascade property from ADR-006.

| Rail-sector property | Why generic models fail | Modeling consequence |
|---|---|---|
| **Cross-border operation** — a vehicle must simultaneously satisfy several national implementations of the same EU directive/TSI | A single "jurisdiction" field cannot hold multiple concurrent legal spaces | Applicability is a *dimension* (multi-valued legal-space + scope), not a scalar — Cascade (d) |
| **National safety-authority regimes** — national transpositions of EU law under distinct agencies | A flat issuer field loses the EU→national→agency→industry→company chain | `cascade-level` as a controlled enum representing the norm hierarchy — Cascade (b)/(c) |
| **Vehicle-series specialization** — the same operating rule differs per series | Generic metadata has no notion of "specialize for a delimited technical area" | Org/variant profile = OSCAL profile over the catalog; a native "addendum" mechanism is the analogue — Cascade (a) |
| **Multimodal, multi-domain** — rail, bus, tram, cableway, ferry; vehicles, infrastructure, procurement, maintenance | A single security-only taxonomy (e.g. NIST default) does not fit | Theme taxonomy pluggable per owner, as a generated enum |
| **Deep regulatory cascade** — ISO/EN → TSI → national → agency → industry → company → system | Generic compliance tools model one or two levels | Cascade is a first-class, enumerated axis orthogonal to theme |

The claim is therefore explicit: **OSCAL4Rail's metadata model is adaptive because rail is
cross-border, multi-regime, multimodal and vehicle-series-specialized.** Any single corporate rule
database is one instance; the framework abstracts the *pattern*, so that a Swiss BS-KI catalog, an
infrastructure manager's rulebook, or a vendor specification all use the same schema with a
different jurisdiction/org profile.

---

## Related Work in the European OSCAL Ecosystem

Checked whether a comparable adaptive, jurisdiction-/organization-specific OSCAL metadata model
already exists in Europe, to avoid reinventing it.

**[EUROSCAL — "The EU Friends of OSCAL"](https://euroscal.eu/)** is the most visible EU-level
OSCAL initiative. Finding: **it is an adoption/community hub, not a sectoral profile, and its
domain is cloud cybersecurity certification — not rail.** It grew out of the EU-funded MEDINA
(952633) and EMERALD (101120688) projects ("automating the cybersecurity certification of cloud
services"), references NIST OSCAL and ETSI TR 103 305-4, but publishes **no sector profile, no
multi-jurisdiction metadata model, and nothing specific to railway regulation, cross-border
operation, or vehicle-series specialization.**

**Consequence for OSCAL4Rail:** no overlap, no duplication. EUROSCAL is a relevant *alignment
contact* (the natural EU venue to socialize a rail OSCAL profile), not a competitor. That the one
European OSCAL initiative is explicitly *not* sectoral and *not* rail strengthens the
rail-specific rationale: this model is net-new and needed.

---

## Considered Alternatives

### Alternative A: One metadata schema per issuing body

- (−) Explodes with every border and every company; no SSOT.
- (−) Cross-border documents (Cascade (d)) have no single valid schema.
- (−) Forking contradicts ADR-008 (NIST base unchanged) and the SSOT principle.

### Alternative B: One flat generic schema with free-text fields

- (+) Trivially "one schema".
- (−) Free text invites drift and Goodhart effects (uncontrolled casing/spelling of the same value).
- (−) No machine-checkable applicability → cannot drive the Assessment layer.
- (−) Conflates the four orthogonal dimensions; not MECE; not rail-aware.

### Alternative C: One schema, layered profiles over the unchanged NIST base (chosen)

The NIST `metadata` assembly stays untouched. Additive profiles sit above it, selected per
document; railway-specific vocabularies are generated from owner SSOTs.

- (+) One schema; adaptivity via profile selection, not schema forks.
- (+) Controlled enums where OSCAL4Rail owns the vocabulary (cascade), owner-generated enums where
  the owner owns it (theme taxonomy) — honors Framework ≠ Content.
- (+) Orthogonal dimensions preserved; rail-specific by construction.
- (−) Requires a sync mechanism when an owner SSOT changes (vocabulary version bump).
- (−) Validator must load NIST base + core + the applicable jurisdiction/org profile set.

---

## Decision

**Adopt Alternative C.** OSCAL4Rail defines **one** rail-sector metadata model as additive layers
over the unchanged NIST OSCAL `metadata` assembly (ADR-008), extended solely through `prop` with
an organizational `ns` (the NIST-sanctioned extension point).

```
┌─ NIST OSCAL metadata (unchanged)   title, version, parties, roles, props[], links
│
├─ CORE profile            ns: https://oscal4rail.openrail.org/ns
│    ALWAYS mandatory, jurisdiction-neutral, rail-sector-wide:
│    cascade-level (enum), rule-format, lifecycle-status, provenance-ref
│
├─ JURISDICTION profile    ns e.g.: .../ns/jurisdiction/<country-code>
│    country/regime-specific mandatory props + enums:
│    theme-maingroup, theme-subgroup (enum generated from the owner's taxonomy SSOT),
│    legal-space, scope-structure
│
└─ ORG / VARIANT profile   ns e.g.: .../ns/org/<org-id>
     company- or vehicle-series-specific props (the home of a native "addendum" mechanism):
     deviates-from, exception-for, vehicle-series
```

**Rules of the model:**

1. **One schema.** There is exactly one OSCAL4Rail metadata schema. "Adaptation" means *selecting
   and layering profiles*, never editing or forking the schema.
2. **Cascade is a first-class, controlled enum** owned by OSCAL4Rail (the rail norm hierarchy:
   international → EU → national → agency → industry → company → system/team).
3. **Theme taxonomy is owner-generated.** Where an issuing organization maintains a controlled
   list, the jurisdiction enums are **generated** from that owner SSOT — not hand-authored by the
   framework. Governance of the list stays with the owner.
4. **Applicability is multi-valued** (scope + legal-space + audience) to support cross-border
   concurrency; it is the bridge from L1 (catalog) via L2 (rules/applicability) to L4 (assessment).
5. **A native "addendum" specialization maps to an OSCAL profile** — a specialization that imports
   and concretizes a parent catalog and may carry local deviations; conformance flows downward
   (ADR-006 (a)).
6. **PII stays controlled.** Author identity goes to `parties`/`responsible-party`; any bulk
   importer of a rule inventory must provide an anonymized/full split.

---

## Consequences

### Positive
- A single rail-sector schema serves undertakings, infrastructure managers and authorities;
  cross-border documents remain valid under one model (Cascade (d) honored).
- Adaptivity is explicit and rail-aware: profile selection encodes jurisdiction, organization and
  vehicle series.
- Theme and cascade are machine-checkable enums → the Assessment layer can decide which controls
  apply where, deterministically.
- NIST base untouched; every OSCAL4Rail document is also valid NIST OSCAL (ADR-008 preserved).
- Framework ≠ Content preserved: OSCAL4Rail owns cascade; owners own their taxonomies and text.
- The head round-trips back to the owner-recognizable form, including local fields.

### Negative / Risks
- A vocabulary-sync mechanism is required when an owner SSOT changes (version bump → regenerate
  enum, record the change).
- The validator grows a profile-resolution step (NIST base + core + jurisdiction/org).
- Governance boundary must stay sharp: OSCAL4Rail must not silently extend an owner's taxonomy.
- PII handling in rule inventories must be enforced in tooling, not left to convention.

---

## Actions

1. Specify the CORE profile prop set (`cascade-level` enum = the rail cascade levels,
   `rule-format`, `lifecycle-status`, `provenance-ref`) as an OSCAL4Rail constraints document
   (`schemas/oscal4rail/`), separate from NIST (ADR-008).
2. Provide a **generator pattern** that emits jurisdiction theme enums from an owner's taxonomy
   SSOT, recording the source version for sync. (Owner-specific inputs stay with the owner.)
3. Define the ORG/variant profile convention and map a native "addendum" to an OSCAL profile that
   imports a parent catalog (specialization, not contradiction).
4. Add a round-trip reference that reconstructs a document head (incl. local props) for owner
   verification; verify verbatim against a public example (e.g. BS-KI).
5. Enforce the PII anonymized/full split in any rule-inventory importer.

---

## References

- [NIST OSCAL Model Overview](https://pages.nist.gov/OSCAL/learn/concepts/layer/overview/) —
  metadata assembly, extension via `prop`/`ns`
- [NIST OSCAL Assessment Layer](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/)
- [EUROSCAL — The EU Friends of OSCAL](https://euroscal.eu/) — EU OSCAL adoption community
  (cloud cybersecurity, MEDINA/EMERALD); checked as related work, no rail/sectoral overlap
- Related: [ADR-006](./ADR-006-oscal4rail-vs-rulemapping.md) (Regulatory Cascade),
  [ADR-007](./ADR-007-tooling-foundation.md) (Framework ≠ Content),
  [ADR-008](./ADR-008-reproducible-schema-acquisition.md) (NIST base unchanged),
  [ADR-010](./ADR-010-configurable-authority-meta-model.md) (configurable authority meta-model —
  generalizes the cascade dimension of this ADR)

---

> 🤖 This document was created with AI assistance (Art. 50(4) EU AI Act). Content is subject to
> review and sign-off by a named maintainer before it changes status from Proposed to Accepted.
