# Motivation – Why OSCAL4Rail?

## The Problem

### Regulations are stuck in PDFs

European railway operations are governed by hundreds of regulations: EU Technical Specifications for Interoperability (TSIs), national standards (BS-KI, Ril 420), company guidelines, and local agreements. Almost all of them live as PDF or Word documents.

This creates a fundamental problem: **regulations are human-readable but not machine-readable.**

### Rules are interpreted, not enforced

When a regulation says "the line number must be displayed at the station", every organisation interprets this individually:
- What exactly is a "line number"?
- Which stations? All of them? Only those with more than X passengers?
- What if the station has no display?

Because rules are free text, they are filtered through the **personal context** of the reader. Two engineers at different companies reading the same paragraph will implement different things. The result is inconsistent passenger information across borders and operators — despite theoretically following the same standard.

### Change is invisible

When a new version of a regulation is published, nobody knows exactly what changed. The only option is to read the entire document again, or rely on a change log (if one exists). There is no way to automatically detect: "Rule 2.1 now says X instead of Y."

At the rule level, version management does not exist.

### The scale of the problem

- SBB alone manages 10,000+ infrastructure contracts spanning 150 years
- The Swiss BS-KI standard covers 42 distinct rules across 6 channels and 4 transport modes
- The EU TSI Telematics regulation applies to all 27 member states
- DB, ÖBB, SBB, SNCF, and dozens of other operators must all comply — each interpreting the same text

## The Solution: OSCAL4Rail

### A 4-layer framework for railway governance

OSCAL4Rail extends the [NIST OSCAL](https://pages.nist.gov/OSCAL/) standard with a railway-specific profile and two entirely new layers:

| Layer | Based on | Purpose |
|-------|----------|---------|
| **(1) Catalog** | NIST OSCAL Control Layer (Catalog + Profile) | Machine-readable regulations with railway-specific extensions (ID conventions, applicability model, multilingual) |
| **(2) Rules** | Rulemapping format | Applicability logic: which controls apply in which context? **Not part of NIST OSCAL.** |
| **(3) Change Impact** | — | Structured change notifications at control level. **Not part of NIST OSCAL.** |
| **(4) Assessment** | NIST OSCAL Assessment Layer (Plan, Results, POA&M) | Compliance verification by AI agents and human reviewers. Existing governance documents do not yet contain assessment information — this layer adds it. |

### Primary use case: internal IT governance

The first step is not external regulation — it's making **internal IT governance** of railway companies machine-readable:
- DB Konzernrichtlinien
- DB Systel Foundations (OSS technology standards)
- DB UX Design System guidelines
- SBB internal standards, ÖBB Vorgaben

These company-level adaptations of legal requirements are today scattered across PDFs — interpreted individually, applied inconsistently, invisible to automated systems. OSCAL4Rail makes them deterministic and AI-agent-ready.

### What makes it "4Rail" — the Regulatory Cascade

The defining railway-specific innovation is not the generic layers (Rules, Change Impact — those are reusable for any regulated sector). It's the **regulatory cascade with conformance constraints and impact propagation** across 5–6 hierarchy levels:

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
- **Changes cascade**: when a TSI changes → all downstream levels must adapt
- **Impact propagates**: "TSI 4.2.1 changed" → which national rules? → which company standards? → which IT systems?
- **Cross-border operations**: trains cross national boundaries — a single vehicle must comply with multiple national implementations of the same EU directive simultaneously
- **Multimodal and multi-domain**: regulations cover rail, bus, tram, cable cars, ships — as well as technical specifications for vehicles, infrastructure, procurement, maintenance, and passenger information
- **6–7 levels deep**: significantly deeper than most other regulated industries

### Why NIST OSCAL as base?

OSCAL was chosen because:
1. **Public domain (CC0)** — no license restrictions
2. **Formal JSON Schema** — validated, not just well-formed
3. **Existing tooling ecosystem** — IBM Trestle, OSCAL-CLI, and many more
4. **Layered model** — Catalog → Profile → Assessment matches the regulation hierarchy
5. **Proven at scale** — used across US federal agencies for FedRAMP compliance

### Deterministic, not AI-generated

The extraction pipeline is **fully deterministic**: PDF text extraction + Excel matrix parsing → OSCAL YAML. No LLM is used in the extraction itself. This means:
- Same input always produces same output
- Results are auditable
- No hallucination risk in the regulation content

LLMs can then *query* the resulting machine-readable catalog — but they do not *create* it.

### Semantic diff across versions

When a new version of BS-KI is published, OSCAL4Rail can automatically detect:
- Which rules changed their text (content change)
- Which rules changed their applicability (obligation tightened or relaxed)
- Which rules are new (added)
- Which rules were removed (deleted)

This gives compliance teams a precise, actionable changelog — not "the document was updated".

## Regulatory Context: Law-as-Code and the Railway Sector

OSCAL4Rail does not exist in isolation. Across Europe, a fundamental shift is underway: regulations should no longer be published only as text, but simultaneously as machine-readable, executable code.

### SPRIND "Law as Code" Initiative

The German Federal Agency for Disruptive Innovation (SPRIND) has launched a strategic initiative to make all German legislation hybrid-publishable (text + code) by 2028. The initiative defines five foundational elements: a legal code format definition, open-source editors, AI-assisted translation, a central repository, and training programs.

OSCAL4Rail is a **sectoral implementation of this vision** — applied specifically to railway regulations. Where SPRIND works top-down (legislator publishes code), OSCAL4Rail works bottom-up (railway companies extract and validate existing regulations). Both approaches converge toward the same goal: deterministic, machine-verifiable rules.

### Rulemapping as the Rules Format

The Rulemapping Group provides the format for expressing applicability logic: "Under which conditions does this rule apply? What exceptions exist?" OSCAL4Rail **adopts the Rulemapping format** for Layer 2 (Rules), making it the standard way to express which controls apply in which context.

### Layered Relationship

```
Law-as-Code (SPRIND)          = political framework, format standardization
  └── Rulemapping format      = rules format for decision/applicability logic
        └── OSCAL4Rail        = 4-layer governance framework for railways
              └── AI Agents   = consume catalogs for compliance verification
```

### Future Convergence

Railway regulation bodies (ERA, EBA, BAV) currently publish regulations as PDF only. Once the SPRIND Law-as-Code initiative delivers a machine-readable publication format, OSCAL4Rail is designed to consume it as authoritative upstream — replacing the current PDF extraction pipeline. Until then, OSCAL4Rail provides railway companies with machine-readable governance *today*, without waiting for institutional change.

See [ADR-005](adr/ADR-005-law-as-code-relationship.md) for detailed technical alignment.

---

## Vision

OSCAL4Rail should become the **open standard for machine-readable railway governance** under the OpenRail Association — enabling:

1. **Railway companies** to publish internal IT governance (Konzernrichtlinien, Foundations, Design System guidelines) as machine-readable, deterministic catalogs
2. **AI agents** to query regulations and verify IT system compliance (Meaningful Human Control)
3. **Cross-border interoperability** through a shared, validated format
4. **Regulatory change management** as a standard engineering practice
5. **Standards bodies** (future) to publish regulations directly in OSCAL4Rail format once Law-as-Code infrastructure is established
