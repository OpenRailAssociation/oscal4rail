# ADR-016: Decision Criteria and Scoring Method for the Rules-Layer Format Selection

**Status:** Proposed (work in progress)

**Date:** 2026-10-27

**Deciders:** Jens Grote

> **Living document.** This ADR is intentionally **not** Accepted. It defines the
> **evaluation grid and scoring method** used to analyze candidate rules-layer
> formats. It is the **template** against which each candidate analysis issue
> (#14–#22) is scored. The final format decision will be a **separate** ADR, taken
> after the analyses are complete. Criteria may still be sharpened as analyses reveal
> gaps (agreed: approximate now, refine later).

## Context

The Rules Layer (Layer 2) answers "under which conditions does a control apply, and
with which obligation?". [ADR-014](./ADR-014-rules-layer-placement.md) already fixed
the structural questions (separate linked logic artifact, version coupling via
`metadata.version`). What remains is choosing the **format** of that logic.

Before analyzing candidates (Rulemapping/RUML #14, Catala #15, GEMARA #16,
ComplyTime #17, OECD #18, EuroSCAL #19, Blawx #20, OpenFisca #21, EASA AMC #22), we
fix a common, weighted evaluation grid so every analysis is comparable and the final
decision is traceable (Definition of Done, Pugh-style structured comparison, but with
an explicit school-grade scale rather than relative +/−).

This separates two things we must never conflate (confirmed with the owner):

- **Format / standard** (e.g. a logic schema) is scored by the grid below.
- **Hosted tool / SaaS** (e.g. an authoring workspace) belongs to the separate
  tool/verification story (same class as
  [ADR-015](./ADR-015-oscal-agent-tooling-landscape.md)), **not** this grid.

## Overarching principle (not a criterion)

Meaningful Human Control is the framework's overarching, untouchable principle and is
**not** a scored criterion and **not** a per-step gate: the tools and verifiers
deliver *deterministic, documented, prepared* data (conditions visible, conflicts
surfaced as data); the human decides what to derive from it and bears responsibility,
including if they automate that derivation downstream.

## Scoring method

- Each criterion is graded on the German **school-grade scale 1–6**: **1 = very good**
  (fully met) … **6 = insufficient** (not met). **Lower is better.**
- Each criterion carries a **weight**: **high = 3**, **medium = 2**.
- **Total score per candidate = Σ (weight × grade)**. The **lowest total wins.**
- **No knock-out criteria are fixed up front.** Whether a 6 (or a specific criterion
  such as K6/K9) becomes a knock-out is decided *after* seeing the results (deliberate,
  to avoid premature hardening; may be hardened later).

> Caveat (Goodhart / Devil's Advocate): a weighted sum can mask a failed criterion.
> Because knock-outs are not pre-set, the final decision ADR must look at the
> per-criterion grades, not only the total.

## Criteria

> K4 is **parked** until the tool evaluation is done (decision 2026-10-27): whether a
> candidate's schema is actually published and CI-usable depends on findings the tool
> evaluation must establish first. K8 (owner feasibility) was **dropped**: format
> readability is already guaranteed by YAML as canonical format
> ([ADR-012](./ADR-012-canonical-serialization.md)), and the framework is deliberately
> tool-agnostic about how an owner authors catalogs/rules.

| # | Criterion | Weight | What it measures (measurement points) |
|---|-----------|:------:|----------------------------------------|
| **K1** | Decision-logic power | 3 | Arbitrary **nesting**; boolean **AND/OR** (and XOR); **negation**; **thresholds as a typed value** (not free text); **exceptions / overrides** (permission vs. prohibition). Reference cases: vASE criteria (nested AND/OR + exceptions), BS-KI 2.1 (threshold ≥ 800 + "kann verzichtet werden"). |
| **K2** | Verbatim separation under co-location | 3 | Logic and verbatim rule text are **structurally separate** (logic never duplicates/overwrites the `statement`), yet the logic **may be co-located at the same control** (not forced into a separate external file only). Verbatim invariant ([catalog-format.md §3](../reference/catalog-format.md)) stays intact. |
| **K3** | OSCAL attachment | 3 | Referenceable from a control (`link`/`back-matter`) without forking NIST. Includes the **lateral (non-conflicting) relation axis** (equivalent-to / subset-of / depends-on / complements) via the NIST **Mapping Collection** ([cascade-as-profiles.md §6](../reference/cascade-as-profiles.md)). |
| **K4** | Schema validatability (CI) | *(parked)* | Published, machine-readable schema (JSON Schema/XSD); CI-capable; covers the K1 constructs. **Parked until the tool evaluation.** |
| **K5** | Stable, semantic IDs (temporal axis) | 3 | **Stability** across versions (same ID for the same requirement); **no re-use** of IDs (not even after retirement); **lifecycle** new / changed / replaced / retired: changed = same ID + version bump; replaced = **predecessor/successor** chain referencing **ID + version** of the old/new control; retired = explicit status + from which version/date, **no** successor. **Semantic** (chapter-based, not page/counter). References valid only on equal ID **and** version (per ADR-014). |
| **K6** | Openness / license | 2 | **OSI-approved** license (verbatim OpenRail guideline: "Use a license which is approved by the Open Source Initiative (OSI)"); open, published standard. O4R compatibility (Apache-2.0) only relevant on code/asset adoption, not on format reference. |
| **K7** | Agent / machine evaluability | 2 | Logic lives in the **OSCAL model** (not a foreign/proprietary format); **canonically YAML** (ADR-012), losslessly machine-processable; **programmatically traversable** without interpreting free text (no prose-only rules). Distinct from K12 (K7 = processable in the standard; K12 = result is deterministic/auditable). |
| **K9** | Stewardship & long-term health | 3 | Org/foundation-backed (not a one-person fork); an official standard steward (NIST, OSI, SPRIND, OpenSSF, …); active maintenance; adoption. Lesson from ADR-015 (archived repo, one-person fork). |
| **K10** | Cascade compatibility (vertical axis) | 3 | Same pattern as K5, on the hierarchical axis: a directed, **versioned** parent/child relation referencing the **parent control's ID + version**; specialization, where a deliberate deviation is **explicit and versioned** (`deviates-from` with parent ID + version), never silent; stability/lifecycle over levels per K5. |
| **K11** | Norm conflict (horizontal axis) | 2 | Conflicts between **competing** requirements are **representable as data**, versioned (ID + version), same pattern as K5/K10, not silently resolved. The format only **surfaces** the conflict; "which applies when" is the **Assessment layer (L4)**, and the human decides. |
| **K12** | Determinism & auditability | 3 | Same input yields reproducibly the same result (no LLM interpretation in the path); **explainable** (which branch/condition fired); conflicts **surfaced as data**; result **documentable/auditable** (for sign-off, diff, re-verification). This is the layer's reason to exist: "here you have deterministic results." |

### The four relation axes (completeness check, MECE)

Relations between requirements are covered on four axes, all using the **same pattern**
(directed, versioned reference carrying ID + version, as data in YAML/OSCAL):

| Axis | Relation | Where |
|------|----------|-------|
| temporal | predecessor / successor | K5 |
| vertical | parent / child, `deviates-from` | K10 |
| horizontal (conflicting) | competing requirements | K11 (surface only; resolution in L4) |
| lateral (non-conflicting) | equivalent-to / subset-of / depends-on / complements | NIST Mapping Collection, via K3 |

## Open points (to settle as analyses proceed)

- Un-park **K4** after the tool evaluation.
- Decide whether **K6/K9** (or a grade of 6) act as knock-outs, after seeing results.
- Sharpen K10/K11 relation semantics if the candidate analyses expose gaps.

## Decision

Adopt the **scoring method** (school grades 1–6, lower is better; weights 3/2;
total = Σ(weight × grade); no pre-set knock-outs) and the **criteria K1–K12** above
(K4 parked, K8 dropped) as the common grid for the rules-format candidate analyses
(#14–#22). The grid is a **living template**; the format selection itself is a
separate, later ADR.

## Consequences

### Positive
- Every candidate analysis is scored against one comparable, weighted grid, so the
  final decision is traceable (Definition of Done).
- Format vs. tool are kept on separate axes, preventing a strong format from being
  disqualified by a tool's licensing (and vice versa).
- The four relation axes give an explicit completeness check (MECE).

### Negative / Risks
- A weighted sum can mask a failed criterion (Goodhart). Mitigation: the final ADR
  reviews per-criterion grades, not only totals; knock-outs can be added later.
- Grades carry subjectivity. Mitigation: each criterion has explicit measurement
  points, and each analysis must cite verbatim evidence for its grade.
- K4 parked means a candidate's CI-validatability is not yet in the total; the final
  ADR must re-score once K4 is un-parked.

## References

- [ADR-012: Canonical Serialization](./ADR-012-canonical-serialization.md) (YAML canonical)
- [ADR-014: Rules-Layer Placement](./ADR-014-rules-layer-placement.md) (separate linked artifact, version coupling)
- [ADR-015: OSCAL AI-Agent Tooling Landscape](./ADR-015-oscal-agent-tooling-landscape.md) (tool vs. reference axis)
- [catalog-format.md](../reference/catalog-format.md) §3 (verbatim), §6 (applicability)
- [cascade-as-profiles.md](../reference/cascade-as-profiles.md) §6 (mapping collection)
- OpenRail open-sourcing practice (OSI-approved license requirement)
- Candidate analysis issues: #14–#22; Rules Layer spec issue #8

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
