# ADR-016: Decision Criteria and Scoring Method for the Rules-Layer Format Selection

**Status:** Accepted (grid + candidate analyses complete, 2026-10-29)

**Date:** 2026-10-27 (grid) · 2026-10-29 (analyses complete, K4 un-parked)

**Deciders:** Jens Grote

> **Scope of this ADR.** It defines the **evaluation grid and scoring method** and records
> the **completed analyses** of candidate rules-layer formats (#14–#22). It is now
> **Accepted**: the grid is fixed, all nine candidates are assessed, K4 is un-parked, and the
> **review outcome** is recorded below (see *Review outcome*). It remains **not** the final
> format decision — per the separation agreed with the owner, the **format selection and the
> own-format specification are a separate, later ADR** (rules-layer spec, #8). This ADR is the
> traceable evidence base that decision will cite.

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

## Candidate scores (complete — 9/9)

> All nine candidates (#14–#22) are scored/assessed against the grid above,
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
| OpenFisca (#21) | 1 | 4 | 5 | – | 3 | 2 | 5 | 1 | 6 | 5 | 3 | **3.44** | scored; **not adopted** — RaC hybrid (date-versioned parameter YAML + Python logic); best stewardship (K9), AGPL caveat; parameter/temporal-value reference for L2 |
| Blawx (#20) | 1 | 4 | 5 | – | 4 | 1 | 6 | 6 | 6 | 2 | 2 | **3.78** | scored; **not adopted** — Catala-class RaC logic but foreign engine (s(CASP)) + single-person fork (K9); owner-friendly authoring + explainability reference |
| Rulemapping / RUML (#14) | 2 | 6 | 4 | – | 6 | 6 | 4 | 4 | 6 | 5 | 5 | **4.78** | scored; **not adopted** — proprietary, commercialised single-vendor SaaS (ToU §6; Product Update 2026-10-23); process-level handover (ADR-006) stays valid |
| GEMARA (#16) | — | — | — | — | — | — | — | — | — | — | — | **n/a** | assessed, **not scored** (not an L2 rules format — see below); reference-only (format) + interop at the audit/evaluation boundary |
| ComplyTime (#17) | — | — | — | — | — | — | — | — | — | — | — | **n/a** | assessed, **not scored** (not a format — an assessment-**execution** tool); documented in the tooling landscape (ADR-015), not here |
| OECD Law-as-Code (#18) | — | — | — | — | — | — | — | — | — | — | — | **n/a** | assessed, **not scored** (not a format or tool — an international reference/positioning frame); the "why" of O4R → motivation / ADR-005 |
| EASA AMC / AltMoC (#22) | — | — | — | — | — | — | — | — | — | — | — | **n/a** | assessed, **not scored** (a regulatory means-of-compliance construct, not an L2 format); **adopt the semantics** for L2 obligation + L4 presumption/AltMoC → #10/#8/#26 |

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

#### #20 Blawx (Lexpedite / Jason Morris) — ⌀ = 3.78 (K4 parked)

Source: `github.com/Lexpedite/blawx` (gh API: license **MIT**, 158★, created 2020-01,
**last push 2024-11-01**, not archived; languages HTML/JS/Python); `Lexpedite/blawx_mcp`
(**archived**, MIT); CEUR "Building Blawx"; MIT Computational Law Report; OECD-OPSI;
pubpub demonstration paper (CC-BY-4.0); issue #20.

Blawx is an "open source, user-friendly, web-based declarative logic knowledge
representation tool … for encoding, testing and using rules" (GitHub) by Lexpedite Legal
Technology Ltd. (Jason Morris), partly under a 2022–2023 Interchange Agreement with the
Government of Canada. Visual programming via **Blockly**; the reasoning engine is
**s(CASP)** (constraint answer set programming — symbolic AI, explainable reasoning). It is
primarily an **authoring tool + reasoner**, not a published, tool-independent exchange
*format*.

| K | Criterion | W | Grade | W×G | Rationale (evidence) |
|---|-----------|:-:|:-----:|:---:|----------------------|
| K1 | Decision-logic power | 3 | 1 | 3 | s(CASP) = constraint answer set programming: nesting, negation (NAF + explicit), defaults/exceptions (defeasible reasoning), typed constraints — built for legal reasoning. Covers all K1 constructs natively; on par with Catala. |
| K2 | Verbatim separation | 3 | 4 | 12 | Encoding is a standalone logic representation (s(CASP) predicates in Blockly); the norm text is *encoded*, not carried as a verbatim field; no ADR-014 structural separation; inverted-SSOT tendency like Catala. Above RUML (6): MIT + self-hosting keeps owner ownership of the encoding (no ToU rights grant). Logic power counted under K1, not here. |
| K3 | OSCAL attachment | 3 | 5 | 15 | No native OSCAL binding; engine/language-bound like Catala — the encoding lives in the tool + s(CASP) reasoner, not a portable `link`/`back-matter` file. Below RUML (4, standalone XML); far below EuroSCAL (2, OSCAL-native). |
| K5 | Stable, semantic IDs | 3 | 4 | 12 | IDs = predicate/category/attribute names (semantic-near, unlike RUML's auto-increment), but **no format-native version/lifecycle construct** (no predecessor/successor, no retired); versioning only via Git/tool. Same as Catala. |
| K6 | Openness / license | 2 | 1 | 2 | **MIT** (OSI-approved, gh API verified); code public + self-hostable (Docker in repo); demonstration paper CC-BY-4.0; s(CASP) is an open academic system. Fully open — far above RUML (6). |
| K7 | Agent / machine evaluability | 2 | 6 | 12 | Logic runs via the **s(CASP) engine** — a foreign logic language, engine-bound; not the OSCAL model, not canonical YAML. The raw artifact is not evaluable without the engine. Same as Catala (compiler-bound, 6). (The "not actively maintained" fact is weighed under K9, not here.) |
| K9 | Stewardship & long-term health | 3 | 6 | 18 | **Single-person fork** (Lexpedite / Jason Morris), no foundation/standards steward; **last push 2024-11-01** (~1 year quiet), `blawx_mcp` **archived** (2026-06); Canada adoption only a time-boxed Interchange Agreement (2022–2023). This is the ADR-015 lesson in full (archived / one-person fork) → effectively dormant. Worse than RUML (4, at least active). Mitigating only: main repo not archived; MIT + self-hosting permits continuation by others (no lock-in). |
| K10 | Cascade compatibility | 3 | 6 | 18 | No cascade model — no versioned parent/child between norm levels, no `deviates-from`. Module/encoding structure is technical composition, not governance specialization. Same as Catala/EuroSCAL/RUML (6). |
| K11 | Norm conflict | 2 | 2 | 4 | s(CASP) handles defeasibility and competing rules natively — detects/surfaces inconsistencies (does not silently resolve); on par with Catala (2). Caveat (as Catala): resolution at reasoning/authoring time, not as a versioned data relation for the L4 MHC decision point. Above EuroSCAL/RUML (5). |
| K12 | Determinism & auditability | 3 | 2 | 6 | Strong: s(CASP) is deterministic, no LLM in the path, and **explainable by design** — natural-language **justification trees** (why a result holds), inherently more transparent than Rego. Not quite Catala (1, formal semantics + partial compiler certification); dragged by missing versioning (no diff/re-verification over time) and engine-bound auditability (K7). Above EuroSCAL (4) and RUML (5). |
| K4 | Schema validatability (CI) | 3 | *parked* | – | Un-park decision deferred. For the record: no published tool-independent exchange schema; s(CASP) is a language, not a JSON Schema/XSD. |

**Profile:** the **Catala-class** pattern — excellent logic substance (K1 = 1),
explainability/determinism (K12 = 2), conflict handling (K11 = 2), open MIT license
(K6 = 1); fails on the same structural points as Catala — foreign engine language instead
of OSCAL/YAML (K7 = 6), no cascade (K10 = 6), handover-only attachment (K3 = 5), no
verbatim/lifecycle (K2/K5 = 4). **Decisive differentiator vs. Catala: stewardship**
(K9 = 6 vs. Catala's 2) — single-person fork, ~1 year inactive, MCP archived. ⌀ = 3.78,
behind Catala (3.22) and EuroSCAL (3.07), ahead of RUML (4.78).

**Verdict:** **scored; not adopted as the L2 rules format** (K7/K9/K10 = 6). Same
Catala-class profile — strong Rules-as-Code logic, explainable reasoning, open license —
but a **foreign engine language (s(CASP))** instead of OSCAL/YAML (K7), no cascade (K10),
handover-only attachment (K3). **Decisive differentiator vs. Catala: stewardship (K9 = 6)**
— a single-person fork (Lexpedite), last push 2024-11, `blawx_mcp` archived (the ADR-015
lesson), which alone rules out a dependency. **Value retained:** a reference for
(a) **owner-friendly authoring** (Blockly visual programming for non-programmers) and
(b) **explainable reasoning** (s(CASP) justification trees), under the Meaningful Human
Control guardrail. **Feeds:** #8 (rules spec — as an authoring/elicitation pattern, like
Catala), **not** a dependency.

#### #21 OpenFisca (digital common; FR-government origin) — ⌀ = 3.44 (K4 parked)

Source: `github.com/openfisca/openfisca-core` (gh API: license **AGPL-3.0**, 249★, created
2013-12, **last push 2026-10-23** — active; Python); country packages active
(`openfisca-france` 2026-10-27, `openfisca-tunisia` 2026-10-28); openfisca.org/doc
(parameters / legislation evolutions); OECD-OPSI; issue #21.

OpenFisca is an "open-source engine to write rules as code" for tax/benefit microsimulation
(initiated by the French government in 2011; used in FR, NZ, AU, CA, …). Two artifact types:
**parameters** = **YAML files with date-stamped values** + legislative references (tree
structure, `values:` date→value, `metadata.reference`, `unit`, `brackets`/`scales`); and
**variables/formulas** = **Python code** (`def formula(person, period, parameters)`) that
consumes the parameters.

| K | Criterion | W | Grade | W×G | Rationale (evidence) |
|---|-----------|:-:|:-----:|:---:|----------------------|
| K1 | Decision-logic power | 3 | 1 | 3 | Logic in **Python** → fully general (nesting, AND/OR, negation, exceptions, reforms); thresholds as typed parameters (`brackets`/`scales` with `threshold`/`rate`/`unit`). Covers all K1 constructs; on par with Catala/Blawx. Its massive strength. |
| K2 | Verbatim separation | 3 | 4 | 12 | Clean structural split parameters (YAML) / logic (Python); logic never overwrites rule text. But **no verbatim model** — parameter YAML carries `metadata.reference` (a URL to the norm), **not the verbatim text**; inverted SSOT. Same as Catala/Blawx; no ToU/ownership issue (AGPL/self-hosted). |
| K3 | OSCAL attachment | 3 | 5 | 15 | No native OSCAL binding; the parameter YAML would be referenceable, but the **logic is Python, engine-bound** (OpenFisca-Core runtime) — the decision part is not a portable `link`/`back-matter` artifact. Referencing only the parameter YAML is insufficient (values, not logic). Same as Catala/Blawx (5). |
| K5 | Stable, semantic IDs | 3 | 3 | 9 | Semantic tree paths (`tax_on_salary.public_sector.rate`) + **native date-stamped values with legislative references** (`values: 1993-01-01 … 2010-01-01 …`) — a real data-borne temporal value history, unique among candidates → **above Catala/Blawx (4)**. But it is value-over-time, **not** the rule-identity lifecycle K5 demands (no predecessor/successor, no retired status) → not 2. |
| K6 | Openness / license | 2 | 2 | 4 | **AGPL-3.0** (OSI-approved, gh API); "digital common", horizontal RFC governance, public. Open — but **AGPL copyleft** is a real reuse caveat vs. O4R's permissive Apache-2.0 (applies on code/asset adoption, not format reference). Consistent with the RUML reasoning (license practicality counted): a notch below the permissive Apache/MIT candidates (1), far above RUML (6). |
| K7 | Agent / machine evaluability | 2 | 5 | 10 | Decision logic is **Python in an engine runtime** — not the OSCAL model, not canonical YAML, not evaluable without the engine (direction of Catala/Blawx 6). **Mitigated to 5** by the engine-free, traversable **parameter YAML** (a substantial declarative part is accessible without the engine, unlike Catala's pure compiler dependency). |
| K9 | Stewardship & long-term health | 3 | 1 | 3 | **Strongest stewardship of all candidates:** org-backed (`openfisca`, many active repos — not a one-person fork), continuously active since **2011** (core push 2026-10), broad multi-jurisdictional productive adoption (FR/NZ/AU/CA), explicit democratic "digital common" governance (RFCs). Above Catala/EuroSCAL (2). Caveat: a community/government ecosystem, not a formal standards steward. |
| K10 | Cascade compatibility | 3 | 6 | 18 | No cascade model — no versioned parent/child between norm levels, no `deviates-from`. Reforms are scenario variants; country packages sit side by side, no derivation hierarchy with conformance. Same as all candidates (6). |
| K11 | Norm conflict | 2 | 5 | 10 | No conflict-as-data model and no conflict-surfacing concept — reforms resolve alternative states in code, not as a versioned relation between competing norms. Does not silently resolve (no conflict concept at all), but does not surface it either. Same as EuroSCAL/RUML (5); below Catala/Blawx (2). |
| K12 | Determinism & auditability | 3 | 3 | 9 | Deterministic, reproducible, no LLM; strong YAML-test mechanism; **parameter side highly auditable** (date-stamped values + legislative references → what value held when and from where — strong diff/sign-off basis over time, best after Catala). **But the Python logic lacks inherent explainability** (no justification tree like Blawx/s(CASP), no formal semantics like Catala) — "which branch fired" is only via code reading. Above EuroSCAL (4)/RUML (5); below Blawx (2)/Catala (1). |
| K4 | Schema validatability (CI) | 3 | *parked* | – | Un-park decision deferred. For the record: parameter YAML has documented conventions + YAML tests; Python formulas are not schema-validatable. |

**Profile:** the **hybrid with the best stewardship** — massive logic power (K1 = 1), the
**strongest stewardship of all candidates** (K9 = 1), and uniquely a **native date-versioned
parameter YAML** (K5 = 3, above Catala/Blawx). Fails the O4R-defining axes like every RaC
candidate — no cascade (K10 = 6), engine/Python-bound logic (K7 = 5), handover-only (K3 = 5),
no conflict-as-data (K11 = 5), no verbatim (K2 = 4). AGPL copyleft (K6 = 2) as a reuse caveat.
⌀ = 3.44 — ahead of Blawx (3.78), behind Catala (3.22) and EuroSCAL (3.07).

**Verdict:** **scored; not adopted as the L2 rules format** (K3/K10 = 5/6; logic engine-bound).
A hybrid of a declarative, **date-versioned parameter YAML** (strong, legislation-referenced —
the K5 differentiator) and **Python decision logic** (powerful but engine-bound, not OSCAL/YAML).
**Best stewardship of all candidates** (K9 = 1: org-backed `openfisca`, active since 2011,
multi-jurisdictional digital common). Fails the O4R-defining axes like every RaC candidate — no
cascade (K10), no OSCAL binding (K3), no conflict-as-data (K11), no verbatim model (K2).
**License caveat:** AGPL-3.0 is OSI-approved and open (K6 = 2), but its copyleft is
**incompatible with O4R's Apache-2.0 on code/asset adoption** — relevant only if code were
adopted, not for format/concept reference. **Value retained:** the **date-versioned parameter
model** (`values` per date + `metadata.reference`) is a concrete reference for
**parameter/threshold handling and temporal value history in L2**, and the YAML-test pattern
for determinism. **Feeds:** #8 (parameter handling + temporal values), **not** a dependency
(AGPL + engine-bound logic).

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

#### #22 EASA AMC / AltMoC (means-of-compliance construct) — assessed, not scored

Source: EASA "Acceptable Means of Compliance (AMC) and Alternative Means of Compliance
(AltMoC)" (document library); EASA FAQ 19117 (status of IR / AMC / CS / AltMoC / GM);
Easy Access Rules (e.g. Airworthiness, Reg. (EU) 748/2012); issue #22.

**Why not scored against K1–K12:** AMC/AltMoC is **neither a format nor a tool** — it is a
**regulatory means-of-compliance construct / legal semantics** of the EASA regulatory system.
The K-grid measures fitness as an L2 rules *format*; forcing a legal construct through it
would yield a misleading total (Goodhart / false precision). Same class as OECD (#18) and
GEMARA (#16): assessed qualitatively. Recorded for traceability.

- **Scope & construct (verbatim):** AMC = regulator-issued, **non-binding** standards that
  carry a **presumption of compliance** — "The AMC illustrate a means, **but not the only
  means**, by which a requirement of an implementing rule can be met." AltMoC = an
  alternative chosen by the regulated person; the presumption is **lost** and compliance must
  be "demonstrate[d] to competent authorities" with **prior approval**. GM = non-binding
  guidance material.
- **EASA regulatory cascade:** Basic Regulation → **Implementing Rules** (binding) →
  **CS / AMC / GM** (soft law). Published as **Easy Access Rules** (consolidated, structured
  IR → AMC → GM).
- **Affected O4R layers (where the semantics land):**
  - **L2 Rules** — the **binding vs. non-binding obligation** distinction (IR binding; AMC
    soft law) maps onto O4R's obligation typing (verbindlich/empfohlen), already present in
    the applicability model.
  - **L4 Assessment** — **AMC = presumption of compliance** (a deterministic default pass
    path); **AltMoC = presumption lost + explicit prior approval** (a distinct evidence path
    with a named competent-authority decision — a natural **Meaningful Human Control**
    decision point).
  - **Cascade** — soft law sitting *below* the binding rule, a concrete cascade level.
- **License & governance:** EASA = official EU agency; highest institutional legitimacy;
  material public (Easy Access Rules). No software artifact / no OSS license to adopt; reuse
  terms are EASA-specific for the text material.

**Verdict:** **assessed, not scored — adopt the *semantics*, not an artifact.** AMC/AltMoC
provides the **established regulatory vocabulary** O4R should reuse rather than invent
(issue #22: "model means-of-compliance using the established regulatory semantics instead of
inventing our own"): binding/non-binding obligation (L2), presumption-of-compliance and the
AltMoC demonstration + prior-approval path (L4), soft-law-below-binding (cascade). This
mirrors the existing AMC concept in the DB-internal work (`KONZEPT-RULEMAPPING.md`) and the
Catala elicitation pattern, under the MHC guardrail. **Feeds:** **#10** (AMC/AltMoC semantics
in L2/L4), **#8** (rules spec — obligation typing) and **#26** (Railway Assessment Profile —
presumption/AltMoC paths). **Non-goal:** nothing to adopt as a format or tool.

## Review outcome (#13 — synthesis over all nine analyses)

**Bottom line: build the L2 rules format, do not adopt one — but reuse named parts of
several candidates for specific layers.** No candidate is adoptable *as the L2 rules
format*: all five scored candidates land between **3.07 and 4.78**, and every Rules-as-Code
tool fails the same O4R-defining axes — **K10 cascade = 6 across the board**, weak OSCAL
attachment (K3), no verbatim model. This is a pattern, not noise: **no existing format
carries the Regulatory Cascade + OSCAL-verbatim combination**, which is precisely the O4R
USP. Therefore O4R **specifies its own OSCAL-native, YAML-canonical, cascade-capable L2
format** and draws **concepts/parts** from the candidates.

**But "not the L2 format" ≠ "not relevant".** The framework is MECE-decomposed into layers,
and the analyses show the right building block per part:

### Explicit verdict per candidate (adopt / reuse-partial / reference-only / reject)

| Candidate | ⌀ | As L2 format | Concretely for which part/layer | Verdict |
|-----------|:--:|--------------|----------------------------------|---------|
| EuroSCAL / Clouditor (#19) | 3.07 | no | **L4 Assessment**: OSCAL-native metric model, `applicable`/`compliant` split, `security-metrics` governance-repo pattern | **reuse-partial (L4)** → #26/#27 |
| Catala (#15) | 3.22 | no | **L2 concept**: default logic + elicitation pattern (interpretable→deterministic); optional executable **upstream** | **reference-only (concept)** + optional upstream → #8/#12 |
| OpenFisca (#21) | 3.44 | no | **L2 parameter handling**: date-versioned parameter YAML + `metadata.reference` + temporal value history | **reuse-partial (concept)** → #8 |
| Blawx (#20) | 3.78 | no | **Enablement/authoring**: Blockly owner-friendly authoring; s(CASP) justification-tree explainability | **reference-only (concept)** → #8 |
| Rulemapping / RUML (#14) | 4.78 | no | only the legislator→compliance **process handover** (ADR-006); format proprietary/incompatible | **reject (as format)**; process-handover only |
| GEMARA (#16) | n/a | n/a | **interop** at the audit/evaluation boundary (consume O4R/OSCAL downstream) | reference / interop → #26 |
| ComplyTime (#17) | n/a | n/a | **L4 assessment-execution backend** for the GovernanceAgent (P3) | backend (other layer) → ADR-015 |
| OECD Law-as-Code (#18) | n/a | n/a | **positioning / the "why"** (Law-as-Code vs. Rules-as-Code vocabulary) | reference (positioning) → motivation.md / ADR-005 |
| EASA AMC / AltMoC (#22) | n/a | n/a | **L4 Assessment semantics (primary) + L2 obligation:** AMC = the regulator-issued solution that makes you **compliant by default** (presumption of compliance); AltMoC = self-chosen path, presumption lost, **demonstrate + prior approval**; plus binding/non-binding obligation typing | **adopt-semantics** → #26/#10/#8 |

### Consequences fed back into layer stories
- **#8 (Rules Layer spec):** own OSCAL-native L2 format; reuse OpenFisca's date-versioned
  parameter pattern; Catala/Blawx as elicitation + explainability patterns; adopt EASA
  obligation typing (binding/non-binding).
- **#26/#27 (Railway Assessment Profile):** EuroSCAL metric model + `applicable`/`compliant`
  split; **EASA AMC/AltMoC as the core L4 compliance model** — taking the regulator's AMC
  solution yields a **compliant-by-default** result (presumption of compliance), while an
  AltMoC requires an explicit demonstration + competent-authority approval (the MHC decision
  point); GEMARA audit/eval interop; ComplyTime as execution backend.
- **ADR-005 / motivation.md:** OECD Law-as-Code positioning.
- **ADR-006:** amend with the RUML equal-footing re-evaluation result (format not adopted;
  process handover stays valid).

### K4 un-parked (decision 2026-10-29)
With nine candidates assessed, K4 (schema validatability, CI) is **un-parked**. It was never
decisive for any scored candidate relative to the dominant axes (K10 cascade, K3 OSCAL,
K2 verbatim), so un-parking **does not change the ranking**. The **separate format-selection
ADR** scores K4 for the own-format proposal against the published OSCAL4Rail constraints
schema (CI-validatable by design) — i.e. the own format is expected to score K4 well, which
further supports *build over adopt*. No pre-set knock-outs are introduced retroactively; the
format ADR reads per-criterion grades, not only averages (Goodhart mitigation).

### Next step (separate ADR, not this one)
The **format-selection + own-L2-format specification** is a separate, later ADR (rules-layer
spec, #8), plus `docs/reference/ecosystem-positioning.md` (the comparison matrix as a
standalone reference). This ADR is their traceable evidence base.

## Open points (resolved on completion, 2026-10-29)

- **K4 un-parked** — done (see *Review outcome* → K4 un-parked). Carried into the format ADR.
- **K6/K9 as knock-outs** — decided **no** retroactive knock-outs; the format ADR reads
  per-criterion grades, not only averages (Goodhart mitigation). The individual 6s (e.g.
  RUML K2/K5/K6/K10) already dominate their averages without a hard gate.
- **K10/K11 relation semantics** — no sharpening needed; the analyses applied them
  consistently (K10 = 6 for every RaC candidate confirmed the cascade gap is real, not a
  grid artifact).

## Decision

Adopt the **scoring method** (school grades 1–6, lower is better; weights 3/2;
⌀ = Σ(weight × grade) / Σ(weight); no pre-set knock-outs) and the **criteria K1–K12** above
(K4 un-parked 2026-10-29, K8 dropped) as the grid for the rules-format candidate analyses
(#14–#22). **All nine candidates are assessed and the review outcome is recorded** (see
*Review outcome*): **no candidate is adopted as the L2 format (build, not adopt); named parts
of EuroSCAL, OpenFisca, EASA, Catala and Blawx are reused per layer.** The **format selection
and own-format specification remain a separate, later ADR** (#8) for which this ADR is the
evidence base.

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
