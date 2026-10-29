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
- **Score per candidate = weighted grade average** — like a **school report where main
  subjects count more**: **⌀ = Σ (weight × grade) / Σ (weight)**. The result stays on the
  **1.0–6.0 grade scale** and the **lowest average wins.** (Σ(weight × grade) is only the
  intermediate numerator; the raw sum must not be read on its own — a medium criterion
  scored 6 would otherwise outweigh a high criterion scored 1. Normalising by Σ(weight)
  removes that distortion and also keeps candidates comparable when the set of scored
  criteria differs, e.g. K4 parked or an n/a.)
- **No knock-out criteria are fixed up front.** A single 6 does **not** auto-fail a
  candidate for now. Whether a 6 (or a specific criterion such as K6/K9) becomes a
  knock-out is decided *after* seeing the results (deliberate, to avoid premature
  hardening; may be hardened later).

> Caveat (Goodhart / Devil's Advocate): even a weighted average can mask a failed
> criterion. Because knock-outs are not pre-set, the final decision ADR must look at the
> per-criterion grades, not only the average.

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

## Candidate scores (work in progress)

> Living section. Each candidate from #14–#22 is scored against the grid above,
> with verbatim evidence. K4 remains **parked** (un-park decision deferred until
> more candidates are scored). Scores use the **weighted grade average**
> ⌀ = Σ(weight × grade) / Σ(weight) over the scored criteria, on the **1.0–6.0 scale**;
> **lower is better**. The final format selection is a **separate, later ADR**; these
> scores inform it.

### Scoreboard (fills up as candidates are analyzed)

Grades per criterion; "–" = parked (K4); **⌀ = weighted grade average** Σ(W×G)/Σ(W) on
the 1.0–6.0 scale (school report, main subjects weigh more); lower is better.

**Rows sorted by ⌀ (ascending; lower is better); assessed-but-not-scored candidates
(n/a) listed last.**

| Candidate (issue) | K1 | K2 | K3 | K4 | K5 | K6 | K7 | K9 | K10 | K11 | K12 | **⌀** | Verdict |
|-------------------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|:---:|:---:|:-----:|---------|
| EuroSCAL / Clouditor (#19) | 3 | 2 | 2 | – | 2 | 1 | 4 | 2 | 6 | 5 | 4 | **3.07** | scored; not an L2 format but close (OSCAL-native); high value as an L4 assessment reference → #26/#27 |
| Catala (#15) | 1 | 4 | 5 | – | 4 | 1 | 6 | 2 | 6 | 2 | 1 | **3.22** | reference-only (format); optional executable upstream |
| Rulemapping / RUML (#14) | 2 | 6 | 4 | – | 6 | 6 | 4 | 4 | 6 | 5 | 5 | **4.78** | scored; **not adopted** — proprietary, commercialised single-vendor SaaS (ToU §6; Product Update 2026-10-23); process-level handover (ADR-006) stays valid |
| GEMARA (#16) | — | — | — | — | — | — | — | — | — | — | — | **n/a** | assessed, **not scored** (not an L2 rules format — see below); reference-only (format) + interop at the audit/evaluation boundary |
| ComplyTime (#17) | — | — | — | — | — | — | — | — | — | — | — | **n/a** | assessed, **not scored** (not a format — an assessment-**execution** tool); documented in the tooling landscape (ADR-015), not here |
| OECD Law-as-Code (#18) | — | — | — | — | — | — | — | — | — | — | — | **n/a** | assessed, **not scored** (not a format or tool — an international reference/positioning frame); the "why" of O4R → motivation / ADR-005 |

### Scored candidates

#### #15 Catala (INRIA) — ⌀ = 3.22 (K4 parked)

Source: `github.com/CatalaLang/catala` (README, repo metadata), issue #15.

| K | Criterion | W | Grade | W×G | Rationale (evidence) |
|---|-----------|:-:|:-----:|:---:|----------------------|
| K1 | Decision-logic power | 3 | 1 | 3 | "the only programming language … embeds **default logic as a first-class feature**" (README); covers nesting, AND/OR, exceptions/overrides natively. |
| K2 | Verbatim separation | 3 | 4 | 12 | Verbatim-faithful ("code-law faithfulness"), but **inverted SSOT** (Catala file is leading, readable text is *generated*) and no ADR-014 structural separation (statement vs. linked logic artifact). |
| K3 | OSCAL attachment | 3 | 5 | 15 | No native OSCAL binding; usable only as an **upstream law** (national cascade level) via a **translation step** to O4R data (#12). Not completely unsuitable — a different approach. |
| K4 | Schema validatability (CI) | 3 | *parked* | – | Un-park decision deferred. |
| K5 | Stable, semantic IDs | 3 | 4 | 12 | Semantic, chapter-near names (scopes/fields), but **no format-native version/lifecycle construct** (predecessor/successor, retired); versioning via modules/Git, not as data in the format. |
| K6 | Openness / license | 2 | 1 | 2 | **Apache-2.0** (OSI-approved, `gh api` + README); open, published standard (Catala book, formal semantics). Same license as O4R. |
| K7 | Agent / machine evaluability | 2 | 6 | 12 | Logic only evaluable via the **Catala compiler** + a subsequent **translator to O4R**; not the OSCAL model, not canonical YAML. |
| K9 | Stewardship & long-term health | 3 | 2 | 6 | **INRIA** (state-funded public research institute), productive use in French tax administration, active maintenance, high adoption (2431★). Caveat: self-declared "**unstable … research project**", no standards steward. |
| K10 | Cascade compatibility | 3 | 6 | 18 | **No vertical cascade model** (no parent/child between norm levels, no versioned `deviates-from`). Module imports are technical composition, not governance specialization. |
| K11 | Norm conflict | 2 | 2 | 4 | Default logic **detects and surfaces** competing rules (compiler flags undecidable exceptions as a conflict). Caveat: resolution is pulled into authoring time; the MHC decision point at application is absent. |
| K12 | Determinism & auditability | 3 | 1 | 3 | "faithful-by-construction"; **formal semantics + partial compiler certification**; no LLM in the path; explainable (which branch/exception fired); lawyer-readable audit output. |

**Profile:** strong in logic substance (K1, K12, K11) and licence/stewardship (K6, K9);
weak in native O4R integration (K3, K7, K10) — **as expected**. We never expected an
O4R-native format; what Catala delivers is a **deterministic, machine-readable result
that is transformable into O4R**. The low integration grades judge *native format fit*,
not *result transformability*.

**Verdict:** **reference-only (as a format)** — not adopted. Twofold role:
(a) **optional executable upstream** for a nation's law already encoded in Catala,
behind the #12 interface via a translation step;
(b) **conceptual template for a later adaptation/elicitation aid** for consuming
companies — many of today's requirements are written in the "definition-under-conditions"
pattern (interpretable text), and Catala's default logic is a model for the transition
*interpretable → deterministic*, under the MHC guardrail (the owner interprets; the tool
structures; sign-off). Tool-agnostic: referenced as a **pattern**, not pulled in as a
dependency (consistent with the minimal/portable tech-stack principle and the
"unstable research project" caveat).

**Feeds:** #12 (interface / upstream) and #8 (Rules Layer spec — elicitation concept as a pattern).

#### #19 EuroSCAL / Clouditor (MEDINA / EMERALD) — ⌀ = 3.07 (K4 parked)

Source: Clouditor (`clouditor/clouditor`, Fraunhofer AISEC — README, metadata,
`api/orchestrator/orchestrator.proto`, `api/assessment/metric.proto`, `policies/rego.go`,
`.gitmodules`); EMERALD (emerald-he.eu; CORDIS 101120688); MEDINA (CORDIS 952633);
NIST OSCAL workshops; issue #19.

**Scored (close enough to the grid):** unlike GEMARA/ComplyTime, Clouditor (the engine
behind MEDINA → EMERALD) has enough **format substance** to score — it follows the OSCAL
catalog/control model and uses a declarative metric format. Its real home is **L4
assessment**, so the grid measures "fitness as an L2 rules format"; the per-criterion
profile (not only the average) carries the message.

| K | Criterion | W | Grade | W×G | Rationale (evidence) |
|---|-----------|:-:|:-----:|:---:|----------------------|
| K1 | Decision-logic power | 3 | 3 | 9 | Typed thresholds strong: `MetricConfiguration.operator` ∈ `^(<\|>\|<=\|>=\|==\|isIn\|allIn)$` + typed `target_value`; `range`/`allowedValues`. But nested logic/exceptions live in external **Rego**, not in the declarative format; no native exception construct. |
| K2 | Verbatim separation | 3 | 2 | 6 | Clean structural separation Control (OSCAL) / Metric (declarative) / Rego (logic) — three artifacts; the logic never overwrites the control text. (Quality of the Rego language itself judged under K7/K12, not here.) |
| K3 | OSCAL attachment | 3 | 2 | 6 | OSCAL-native catalog/control model (verbatim: "a Control in a certification catalog. It follows the **OSCAL model**", "OPS-01, as used in OSCAL"); no NIST fork. Weaker only on the lateral mapping-collection axis (mapping is control→metric). |
| K4 | Schema validatability (CI) | 3 | *parked* | – | Un-park decision deferred. |
| K5 | Stable, semantic IDs | 3 | 2 | 6 | Semantic IDs/paths (`AdminMFAEnabled`, `metrics/<Category>/<Name>/`, OSCAL `OPS-01`); lifecycle via file/Git versioning (not ideal, no native predecessor/successor). uuid `id` field is a weak point but not dominant. |
| K6 | Openness / license | 2 | 1 | 2 | **Apache-2.0** (OSI-approved, `gh` + README badge); open/published (godoc, OpenSSF Best Practices). Same license as O4R. |
| K7 | Agent / machine evaluability | 2 | 4 | 8 | Declarative metric is YAML/JSON (good), but the decision logic is **Rego (OPA)** — a foreign policy language, engine-bound, not the OSCAL model. Better than Catala (compiler) because the "what" (metric) is OSCAL/YAML-near; penalty for the Rego "how". |
| K9 | Stewardship & long-term health | 3 | 2 | 6 | **Fraunhofer AISEC** (not a one-person fork), active (87★, OpenSSF Best Practices, v2 in progress), adopted in EU certification projects (MEDINA→EMERALD), "Friend of OSCAL". Caveat: v2 in flux / no fixed stable date; EU-project-bound; not a standards steward. |
| K10 | Cascade compatibility | 3 | 6 | 18 | No vertical cascade model (no versioned parent/child, no `deviates-from`); catalogs sit side by side (C5/CCM/EUCS), no derivation hierarchy. Own language (Rego) + external toolset would need the cascade built entirely outside. |
| K11 | Norm conflict | 2 | 5 | 10 | No conflict-as-data model; competing requirements are evaluated in isolation (parallel per-metric results). Does not silently resolve, but does not surface the conflict as a relation either. |
| K12 | Determinism & auditability | 3 | 4 | 12 | Technically deterministic (Rego/OPA, no LLM) + OSCAL-auditable output, **but not inherently transparent**: explainability/verifiability is bound to a second language (Rego) + external engine, not readable from the artifact itself nor by the owner without Rego knowledge (MHC limitation). |

**Profile:** mirror image of Catala — **strong on OSCAL integration** (K2/K3/K5 = 2) via
the shared OSCAL catalog/control foundation; **weak on cascade** (K10 = 6) and on the
**foreign, non-inherently-transparent logic language** (K7 = 4, K12 = 4, Rego). ⌀ = 3.07,
just ahead of Catala (3.22).

**Verdict:** **scored; not adopted as an L2 rules format** (K10/K7/K12). **High value on
the L4 assessment side:** an OSCAL-native **metric model** (declarative schema + typed
operators + evaluation scales), the `applicable`/`compliant` split (independently
mirrors O4R's L2-applicability vs. L4-assessment line), and **format + policies in a
separate governance repo** (`Cybersecurity-Certification-Hub/security-metrics` as a
submodule, SSOT, separate from the engine). **Reference / reuse candidate for #26/#27
(Railway Assessment Profile).** EU ecosystem peer + collaboration (Friends of OSCAL;
parallel cloud scope): **register / engage**, explore shared tooling and structures,
without adopting the cloud-specific scope. **Differences:** Rego as a non-inherently-
transparent logic language (MHC caveat); uuid IDs. **Feeds:** ADR-005 addendum (EU
cascade) and #26/#27 (L4 assessment reference).

#### #14 Rulemapping / RUML (Rulemapping Solutions GmbH) — ⌀ = 4.78 (K4 parked)

Source: ADR-006 and the BS-KI 2.1 Builder pilot (2026-06-25, `docs/experiments/rulemapping/`,
verbatim XML export analysis); rulemapping.org (retrieved 2026-10-29); SPRIND Law-as-Code;
OECD-OPSI; `gh search` (no Rulemapping-Group OSS repo / no published schema found); the
provider's **Terms of Use (version 11/2025, valid until 2026-11-12)** and the **Product
Update e-mail of 2026-10-23** (Rulemapping Solutions GmbH), issue #14.

> **Why scored despite ADR-006.** ADR-006 provisionally *adopted* Rulemapping as the
> rules format. [ADR-014](./ADR-014-rules-layer-placement.md) made that adoption no longer
> untouchable, so Rulemapping is re-evaluated **on equal footing** against the K-grid —
> otherwise the evaluation would be a confirmation bias (Devil's Advocate). Two owner-provided
> facts materially changed the picture since the June pilot: the format is **not** the open
> standard ADR-006 anticipated.

| K | Criterion | W | Grade | W×G | Rationale (evidence) |
|---|-----------|:-:|:-----:|:---:|----------------------|
| K1 | Decision-logic power | 3 | 2 | 6 | Full boolean operator set `or/and/xor/nand/nor/n-xor` + negation (`invertlogic`) + arbitrary tree nesting; exceptions ("kann verzichtet werden") representable via `invertlogic` (pilot). But **thresholds only as free text** in the node `title`, not a typed value. Better than EuroSCAL (3, Rego-external logic); below Catala (1, native default logic). |
| K2 | Verbatim separation | 3 | 6 | 18 | **No verbatim model** — rule text only as optional free-text `alttext`; no ADR-014 structural separation; inverted SSOT (Builder file leading). **Compounded by ToU §6** (verbatim): the user grants the provider usage rights over user-generated content ("ein einfaches, nicht übertragbares Nutzungsrecht … analysieren, auszuwerten und zu verwenden") → owner ownership of the verbatim source is contractually broken, not just unmodelled. Full non-fulfilment. |
| K3 | OSCAL attachment | 3 | 4 | 12 | Not OSCAL-native, but the lightweight **XML** export is directly referenceable from a control via `link rel="decision-logic"` / `back-matter` without forking NIST (pilot demonstrated). XML = standardised, machine-readable carrier (not a proprietary blob). No lateral mapping-collection axis. Better than Catala (5, needs a translation step); below EuroSCAL (2, OSCAL-native). |
| K5 | Stable, semantic IDs | 3 | 6 | 18 | IDs are **numeric auto-increment, not semantic** (pilot verbatim); **no version/lifecycle construct** in the format (no predecessor/successor, no retired). Violates the stable-ID invariant (chapter-based, never counter-based). Both K5 sub-criteria fail; below Catala (4, at least semantic names). |
| K6 | Openness / license | 2 | 6 | 12 | RUML spec **not published** (announced only, future tense: "open and *will be* published"). **ToU §6** (verbatim): "Alle Rechte an der Plattform und ihren Bestandteilen stehen ausschließlich dem Anbieter …"; prohibits "Reverse Engineering … Förderung konkurrierender Produkte … Vervielfältigung oder Veröffentlichung von Plattformbestandteilen ohne … Freigabe". No OSI-approved license; actively OSS- and competitor-hostile. Opposite end from Catala/EuroSCAL (1). **Reevaluation possible in future** (see verdict) — but the essential facts for a better grade are not given today. |
| K7 | Agent / machine evaluability | 2 | 4 | 8 | XML boolean tree is programmatically **traversable without a compiler** (pilot ✅), but **not the OSCAL model, not canonical YAML**; part of the semantics is UI-derived and **not persisted** (green derivation), and thresholds live only in free text. Analogous to EuroSCAL (4, Rego): traversable but not in the standard model; better than Catala (6, compiler-bound). |
| K9 | Stewardship & long-term health | 3 | 4 | 12 | Active development (Workspace launch 2026-11-13), productive PoCs (BMF tax law, building permits), SPRIND-funded (€12M, 2025), named management — **not a one-person fork**. But steward = **commercial Rulemapping Solutions GmbH** (single vendor), **no neutral standards steward**; the documented **move to a purely commercial model** (Product Update 2026-10-23: paid plans, usage-rights grant over uploaded rulemaps, entrepreneurs-only §14 BGB) plus the ToU §6/§3 discontinuation reservation ("jederzeit zu ändern, einzuschränken oder einzustellen"; "kein Anspruch … auf bestimmte Funktionen") weigh against longevity/neutrality. Below Catala/EuroSCAL (2, public non-commercial institutions). Mitigating: ToU §12 guarantees machine-readable data export. |
| K10 | Cascade compatibility | 3 | 6 | 18 | **No cascade model** — no parent/child between norm levels, no versioned `deviates-from`. RUML models one single-case decision tree (ADR-006: "interactive single-case decision tree"); tree nesting is case logic, not vertical governance specialization. Same as Catala/EuroSCAL (6). The 4Rail USP is wholly absent. |
| K11 | Norm conflict | 2 | 5 | 10 | **No conflict-as-data model** and no versioned relations between competing norms; a single-case tree evaluates in isolation. Does not silently resolve (there is simply no concept of competing norms), but does not surface the conflict as a relation either. Same as EuroSCAL (5); below Catala (2, detects/flags conflicts). |
| K12 | Determinism & auditability | 3 | 5 | 15 | The boolean tree is locally deterministic and explainable (which branch fires), no LLM in the path. But the audit purpose — sign-off, **diff, stability, re-verification over time** — is substantially undermined because its prerequisites already fail: **no stable/semantic IDs and no versioning (K5 = 6)** and **no verbatim/owner-owned source link (K2 = 6)**; part of the semantics is UI-derived, not persisted. Below EuroSCAL (4, at least OSCAL-auditable output + metric values); far below Catala (1, formal semantics). |
| K4 | Schema validatability (CI) | 3 | *parked* | – | Un-park decision deferred. For the record: no published schema; XML is proprietary (ToU §6), the announced RUML-JSON spec is unpublished. |

**Profile:** strong only on raw decision-logic structure (K1 = 2) and solid traversability
(K3 = 4, K7 = 4); **fails on exactly what makes O4R** — verbatim/owner ownership (K2 = 6),
stable IDs/lifecycle (K5 = 6), openness/license (K6 = 6), cascade (K10 = 6). Four 6s, three
of them in high-weight criteria. ⌀ = 4.78 — clearly the weakest scored candidate
(EuroSCAL 3.07, Catala 3.22).

**Verdict:** **scored; not adopted as the L2 rules format** (K2/K5/K6/K10 = 6). Despite
ADR-006 having provisionally adopted Rulemapping, the equal-footing re-evaluation does
**not** confirm it as the format: as of today it is a **proprietary, commercialised
single-vendor SaaS** (Terms of Use §6, version 11/2025; Product Update 2026-10-23) — no
OSI license, RUML spec unpublished, reverse engineering and "promotion of competing
products" contractually prohibited, provider-claimed usage rights over user content —
**incompatible with the OpenRail OSI-license requirement and with O4R's verbatim /
owner-ownership principle** (SSOT, Meaningful Human Control). **Value retained:**
(a) a conceptual reference for decision-logic *structure* (boolean tree, exceptions) at
the authoring boundary; (b) the legislator → compliance **handover interface** (ADR-006)
remains valid as a *process-level* point of contact, **not** a data-format adoption.
**Reevaluation trigger:** if RUML is published under an OSI-approved license as a genuinely
open standard, re-score K6 (and the dependent K4/K9) — the grades reflect the present facts,
which do not support a better grade today. **Feeds:** the ADR-006 amendment note and #8
(rules spec — as a structural pattern only, not a dependency).

### Assessed but not scored (different problem class)

#### #16 GEMARA (OpenSSF) — assessed, not scored

Source: `gemaraproj/gemara` (README, metadata), `gemara.openssf.org/model`, issue #16.

**Why not scored against K1–K12:** the K-grid measures fitness as an **L2 rules
(decision-logic) format**. GEMARA is not that — it is a **7-layer GRC meta-model**
(CUE schemas + Go/Python SDK) describing categories of compliance activities
(definition layers 1–3, measurement layers 5–7). Forcing a meta-model through a
rules-format grid would produce a misleading total (Goodhart / false precision).
It is therefore assessed qualitatively instead of scored.

- **Scope & format:** machine-readable GRC meta-model; **CUE** schemas per layer
  (control / threat / risk / policy / mapping / evaluation / audit catalogs & logs);
  Go & Python SDKs. 7 layers: 1–3 *definition*, 4 *sensitive activities*,
  5–7 *measurement*.
- **Stewardship:** **OpenSSF / "a Series of LF Projects, LLC"** (Linux Foundation);
  active (biweekly meetings); adopted in production (FINOS Common Cloud Controls L2,
  OpenSSF Security Baseline L2, Privateer L5). License **Apache-2.0**.
- **Relationship to O4R:** **peer meta-model, not a cascade framework.** No Regulatory
  Cascade (vertical, versioned norm derivation; cross-border). It overlaps O4R only in
  the middle (catalog / mapping / assessment) and brings a broader **horizontal GRC
  activity cycle** (policy → evaluation → enforcement → audit) that is **outside** O4R's
  framework scope — that cycle is the operations / consumer side (L4 Assessment
  consumption, GovernanceAgent), not the O4R framework core (L1/L2/L3).
- **OSCAL interaction:** bridges (names OSCAL as prior work; a `gemara2oscal`
  transpiler exists but is **archived**).

**Verdict:** **reference-only as a format** — the meta-model is currently unsuitable to
adopt for O4R (no cascade, foreign CUE taxonomy, broader different scope).
**Interop gain, not scope:** GEMARA's audit/evaluation layers (L5–L7) are a **coupling
point** — O4R catalogs can feed GEMARA evaluation/audit schemas *downstream*.
**Non-goal:** O4R does **not** extend its scope to audit / enforcement /
continuous-monitoring (Framework ≠ operations).
**Feeds:** #26 (Assessment boundary) as an interop option; **not** #8 (rules format).
Optional follow-up: exchange with the GEMARA project (OpenSSF) at the audit/evaluation
boundary, marking auditability as a shared interop gain rather than an O4R scope extension.

**Interop condition (to verify):** the coupling holds **as long as GEMARA can read
OSCAL** (consume O4R/OSCAL catalogs downstream). The only known connector,
`gemara2oscal`, is **archived and one-directional (GEMARA→OSCAL)**; OSCAL→GEMARA
readability is **not yet verified** and is an open point for the #26 interop exploration.

#### #17 ComplyTime (complyctl) — assessed, not scored (tooling, not a format)

Source: `complytime/complyctl` (README, metadata), `complytime.dev`, issue #17.

**Why not scored against K1–K12:** like GEMARA, ComplyTime is not an L2 rules format.
It is an **assessment-*execution* tool** — a "lightweight compliance runtime that pulls
Gemara policies from an OCI registry and executes scans via providers, producing
compliance reports in multiple formats (EvaluationLog, **OSCAL**, SARIF, Markdown)"
(complyctl README). It belongs to the **tooling landscape** (same class as the
NIST-OSCAL-native tools, OpenSCAP/OPA/AMPEL), i.e. [ADR-015](./ADR-015-oscal-agent-tooling-landscape.md),
**not** this rules-format grid. Recorded here only so the evaluation is traceable.

- **Scope & format:** OSCAL-**native** runtime; `complyctl` (Go CLI), evaluator plugins
  via gRPC (OpenSCAP/OPA/AMPEL), OCI policy distribution; produces **OSCAL
  assessment-results**. Apache-2.0; Red Hat origin; OpenSSF Best Practices + Scorecard; active.
- **Layer / role:** **L4 assessment *execution*** (not L4 *specification* — that is O4R's
  Railway Assessment Profile #26). It is the OSCAL-native tool a **GovernanceAgent
  (Project 3)** would invoke and whose deterministic result it receives back (MCP/tool
  pattern: pre-condition = which policy applies, action = scan, post-condition = OSCAL
  evidence; the human derives/decides — MHC preserved).
- **Needs at both ends:** input = an applicability decision ("which rule/policy") = O4R
  **L2 (#8)**, which ComplyTime does **not** make itself (it makes the O4R L2 need
  explicit); output processing (issue / report / quality-gate) = Project 3 / operations.
- **Makes the GEMARA↔OSCAL bridge real:** ComplyTime pulls Gemara policies and emits
  OSCAL assessment-results — a live path for the #16 interop condition.

**Verdict:** **not a format — an assessment-execution tool.** **Adopt-candidate** as the
L4 assessment runtime/backend for the GovernanceAgent (Project 3); **documented in the
tooling landscape (ADR-015)**, feeds #26/#27 and Project 3. **Non-goal:** O4R builds
neither the scan runtime nor the result processing. Full tool entry belongs in ADR-015 (PR #47).

#### #18 OECD Law-as-Code (reference framework) — assessed, not scored (positioning, the "why")

Source: OECD consultation 2026 "Towards a shared reference framework for law as code"
(oecd.org); OECD-OPSI "Cracking the Code" / Rules as Code (oecd-opsi.org); issue #18.

**Why not scored against K1–K12:** OECD Law-as-Code is neither a format nor a tool — it
is an **international reference and positioning frame** / terminology. The K-grid does not
apply. Recorded for traceability.

- **Scope:** OECD (2026, verbatim): "**Law as Code** refines the broader practice of
  **Rules as Code** … the **state-authorised provision of authoritative law in force,
  transformed into machine-executable representations and made available as shared public
  digital infrastructure**." OECD-OPSI (verbatim): an "**official, machine-consumable
  version** of some types of government rules, **to exist alongside the existing natural
  language counterpart**."
- **Stewardship:** OECD (intergovernmental); public consultation 2026. Highest
  institutional legitimacy, but **no software artifact / no license** to adopt.
- **Relationship to O4R:** O4R **fits inside this frame** — it is a **sectoral (railway)
  instantiation** of the OECD vision. It is the **"why we build O4R at all"**, not the
  "how". O4R is **not** Law-as-Code itself (it does not produce state-authorised law); it
  is sectoral governance that **consumes** Law-as-Code upstreams. The OECD "alongside the
  natural-language counterpart" principle independently validates O4R's code-first +
  verbatim approach. Links to Rulemapping (#14) / SPRIND via OECD-OPSI.

**Verdict:** **reference-only (positioning / the "why").** Provides the international
reference frame and vocabulary (Law as Code vs. Rules as Code) that underpins O4R's
**motivation and existence**. **Feeds:** `docs/motivation.md` (the why) and ADR-005
(Law-as-Code relationship / positioning) — anchor the terminology there.
**Non-goal:** nothing to adopt as an artifact or tool.
*(Follow-up: reflect the OECD reference in `motivation.md`.)*

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
