# ADR-018: Rules-Layer Format — OSCAL-native via `parameter/constraint/test` + Control Mapping

**Status:** Accepted (format + fields convention + Subset v1 fixed, 2026-11-05)

**Date:** 2026-11-05

**Deciders:** Jens Grote

> **Relationship to prior ADRs.** [ADR-016](./ADR-016-rules-format-decision-criteria.md)
> (Accepted) fixed the evaluation grid, scored all nine candidate formats, and concluded
> **build the own L2 format, do not adopt** an existing one. [ADR-014](./ADR-014-rules-layer-placement.md)
> fixed the *placement* (separate linked logic artifact, version-coupled via
> `metadata.version`). This ADR is the **own-format specification** ADR-016 announced: it
> decides **how** the own L2 format is realized. It does **not** re-open the candidate
> scoring (ADR-016) and does **not** specify the evaluator tool (that is an
> [ADR-015](./ADR-015-oscal-agent-tooling-landscape.md)-class tool story, see *Tooling
> implications*).

## Context

Layer 2 answers: *under which conditions does a control apply, and with which
obligation?* ADR-016 rejected adopting a foreign format (Rulemapping/RUML, Catala,
OpenFisca, Blawx, …): all fail the Regulatory Cascade (K10) and OSCAL-native verbatim
handling (K3/K7). The owner requirement is unambiguous: **the logic must live in the
OSCAL model, not in a foreign/proprietary format** (ADR-016 K7, verbatim: "Logic lives
in the **OSCAL model** … **canonically YAML** (ADR-012), losslessly machine-processable;
**programmatically traversable** without interpreting free text").

Before inventing a bespoke logic container, we checked what NIST OSCAL **already**
provides (First Principles, Occam, "reuse NIST mechanisms, do not fork" — ADR-008/014).

### Facts (verified 2026-11-05, against the pinned NIST schemas and the NIST reference)

1. **OSCAL has a native, tool-evaluated constraint/test slot.**
   `parameter/constraint` carries one or more `test` objects; each `test.expression`
   is, verbatim (NIST catalog metaschema): *"A formal (executable) expression of a
   constraint"* / *"A test expression which is expected to be evaluated by a tool"*
   (`expression` is `required`). Confirmed in the local pinned schema
   (`schemas/nist/oscal-catalog.json`).
2. **OSCAL's own expression language is Metapath** (its XPath derivative). NIST uses it
   in exactly this slot (OSCAL issue #1069, verbatim: *"In XPath/Metapath an effective
   test could be simply `.=//param[@id='au.02-odp.01']/(select/choice|value)`"*).
   OSCAL deliberately does **not** mandate a single expression language in the schema
   ("formal or informal expression"), so the choice of language is left to the profile.
3. **OSCAL has a native model for lateral relations between controls**: the **Control
   Mapping Model** (`mapping-collection` / `map` / `relationship`). NIST reference,
   verbatim: relations are *"expressed using well-defined set theory concepts such as
   equivalent-to, equal-to, subset-of, superset-of, intersects-with, and
   no-relationship"*, with `method` (syntactic/semantic/functional), `confidence-score`,
   `coverage`, and `qualifier` (requirements/incompatibilities/gaps). Present in the
   local pinned schema (`schemas/nist/oscal-mapping.json`).
4. **The control already carries the attachment and dependency slots**:
   `link rel="decision-logic"` (ADR-014, rulemapping pilot) and the official
   `link rel="depends-on"` / `prop[@name='depends-on']` (OSCAL issue #1069).
5. **Applicability (context × obligation) is already modeled** in the catalog via the
   `applicability` prop (`value` = obligation, `class` = context path), see
   [catalog-format.md §6](../reference/catalog-format.md).

**Consequence of the facts:** "build the own format" does **not** mean a new logic
language or container. Three of the four building blocks are NIST-native and reused
unchanged. The **only** genuine own-contribution is a *deterministic expression
convention* over the existing `constraint/test` slot, plus the O4R applicability/
obligation profile.

## Decision Drivers

1. **OSCAL-native, no fork (hard, ADR-016 K3/K7).** Logic must be expressible within
   stock NIST constructs; no bespoke container forced into the schema.
2. **Determinism and auditability (high, ADR-016 K12; MHC).** A given set of facts must
   yield one reproducible applicability result the owner can verify.
3. **Occam / schema simplicity (ADR-014 driver 6).** Reuse NIST constructs; add only a
   convention and a thin additive constraints schema, like
   `oscal4rail-catalog-constraints.schema.json`.
4. **Verbatim invariant (hard).** Logic never duplicates or overwrites the `statement`
   text (ADR-016 K2, catalog-format §3).
5. **Cascade-awareness (ADR-016 K10).** The format must carry the directed,
   versioned relations the cascade needs (specializes / deviates-from / depends-on),
   not only lateral set-relations.

## Decision

**Realize the Layer 2 format OSCAL-native, as a thin additive profile over three stock
NIST constructs. Introduce no foreign logic language and no bespoke logic container.**

1. **Decision logic = `parameter/constraint/test/expression`.** Applicability
   conditions (nested boolean AND/OR/NOT, typed thresholds, exceptions) are expressed
   as OSCAL `constraint/test` expressions attached to the rules artifact, which the
   control binds via `link rel="decision-logic"` (ADR-014). The verbatim statement
   text is never touched (driver 4).

2. **Expression language = a deterministic Metapath subset (OSCAL-native), fixed as
   Subset v1 below.** We adopt **Metapath**, because it is OSCAL's own expression
   language used in this very slot (fact 2), not a foreign format. OSCAL4Rail
   **constrains** it to a documented, deterministic, side-effect-free **subset** so
   results are reproducible and owner-auditable (driver 2, MHC).

   **Subset v1 — allowed (EARS: an expression MAY use):**
   - **Boolean:** `and`, `or`, `not(...)`, arbitrarily nested.
   - **Comparison / threshold:** `=`, `!=`, `<`, `<=`, `>`, `>=` over typed literals
     (number, string, boolean, ISO-date).
   - **Ordinal comparison:** `<=`/`>=`/… over a declared ordered vocabulary
     (e.g. `low < medium < high`); the order MUST be declared with the parameter,
     otherwise ordinal comparison is undefined.
   - **Context reference:** `context('<dimension>')` — reads one applicability
     dimension (from the `class` path, §6); no free tree navigation.
   - **Parameter reference:** `param('<id>')` — reads an OSCAL `param` value, including
     a dated value (temporal parameters, point 6).
   - **Set membership:** `x = ('a','b','c')` against an explicit value list.
   - **Literals:** number, quoted string, boolean, ISO-date.

   **Subset v1 — forbidden (EARS: an expression MUST NOT use):**
   - Arbitrary axis navigation (`//`, `..`, `following::`, document-order dependence).
   - Non-deterministic or environment-reading functions (`current-dateTime()`,
     `document()`, `doc()`, randomness, any I/O).
   - Recursion or user-defined functions.
   - Any read of the verbatim `statement` text (verbatim invariant, driver 4).

   Rationale (Occam + MHC): this is the minimal set that expresses the real patterns
   verified below (context matching; threshold; boolean AND; exception; ordinal
   comparison) while keeping every expression locally, reproducibly evaluable so the
   owner can verify it in the regenerated document. The EARS requirements and worked
   examples live in the Rules Layer reference (#9/#11).

3. **Lateral relations = the NIST Control Mapping Model, unchanged.** equivalent-to /
   subset-of / superset-of / intersects-with / no-relationship (fact 3) are expressed
   via `mapping-collection`, not an O4R construct. This satisfies ADR-016 K3's lateral
   axis without forking NIST.

4. **Cascade (vertical) relations = directed, versioned references as data.** The
   downward cascade relations the Mapping Model does *not* express
   (specializes / deviates-from / concretizes, carrying ID **and** version) are carried
   as O4R-profiled props/links, consistent with ADR-014 version coupling and the
   cascade spec. (This is the K10 gap every candidate failed; it is O4R's differentiator,
   not a NIST reuse.)

5. **Applicability/obligation = the existing catalog model (§6), reused.**
   `class` = context path (controlled vocabulary, MECE), `value` = obligation
   (regulatory vocabulary, not a framework enum — ADR-007). Obligation *typing*
   (binding / non-binding, presumption-of-compliance) adopts the **EASA semantics**
   per ADR-016, expressed as OSCAL props — not as an EASA artifact.

6. **Datised parameters (optional).** Where a threshold has a legislative validity
   history, parameter values MAY carry dated entries (the **OpenFisca temporal-value
   *concept***, per ADR-016), expressed as OSCAL `param`/`prop`, not as an OpenFisca
   structure.

7. **Canonical serialization = YAML** (ADR-012); JSON/XML are generated.

8. **Canonical rule-fields convention (the framework defines it; owners fill it).**
   A rule in the L2 artifact has a fixed set of fields. The framework owns this
   convention; it is **not** derived from any one regulation or internal rule set. To
   stay **adaptive**, the controlled fields use **open, catalog-declared vocabularies**,
   not hard-coded enums (same stance as the obligation vocabulary in §6, ADR-007).

   | Field | Purpose | Modality | Vocabulary |
   |---|---|---|---|
   | `rule-id` | stable, semantic ID, never reused (K5) | MUST | derived from chapter/control |
   | `control-id` | binding to the L1 control | MUST | OSCAL control reference |
   | `modality` | obligation **strength** | MUST | **declared**, semantics-bound (below) |
   | `rule-group` + `choice` | obligation **relation** between rules (alternative/choice) | MAY | fixed: `all \| one-of \| one-or-more` |
   | `status` | lifecycle | MUST | **declared**, bound to `active: bool` + a fixed `lifecycle` axis: `draft \| active \| deprecated \| superseded \| withdrawn` (`deprecated` = legacy-only; `superseded` carries `superseded-by`) |
   | `applies-when` | decision logic | MAY | Metapath Subset v1 |
   | `parameters` | calibratable, optionally dated thresholds | MAY | typed; order declared if ordinal |
   | `enforcement` | *how* the rule is meant to be enforced (deterministic / decision-model / agentic) — **a list**, a rule may be enforced several ways at once | SHOULD | **declared** (declaration only — see point 9) |
   | `source-ref` | SSOT pointer (document + section); no verbatim duplication | SHOULD | href + section |
   | `deviations` | conflict-as-data (K11): requirement vs. deviation + rationale | MAY | structured (declaration only — see point 9) |
   | `remarks` | owner prose, always allowed | MAY | free text (never read by the agent for semantics) |

   **Modality is two MECE dimensions, not one** (verified against the internal vASE
   artifact, which models both as data — `verbindlichkeitsgrad: verbindlich` and
   `prop logik: "UND (alle müssen zutreffen)"`):
   - **Strength** — how binding a single rule is. The owner declares the vocabulary
     *and binds it to a fixed semantics axis* the agent reads: `binding: bool` + `rank:
     int` (order) + `polarity: required | forbidden` (mandate vs. prohibition). Example:
     `{ MUSS: {binding: true, rank: 1, polarity: required}, "DARF NICHT": {binding: true,
     rank: 1, polarity: forbidden}, SOLL: {binding: false, rank: 2, polarity: required} }`.
     The agent never reads the word "MUSS" semantically — only `binding`/`rank`/`polarity`.
     (`polarity` was added after a viability test against a real internal rule set that
     distinguishes obligations from prohibitions; without it, "MUSS" and "DARF NICHT"
     would be indistinguishable to the agent.)
   - **Relation** — whether several rules stand in a choice/alternative ("entweder-oder",
     "at least one of"). Expressed as a `rule-group` with a **fixed, framework-defined**
     `choice` value (`all | one-of | one-or-more`), mapped onto the NIST
     `parameter-selection/@how-many` (`one | one-or-more`). `choice` is structural
     semantics, not regulatory content, so it MAY be fixed without violating ADR-007
     (contrast: `modality`/`status`/`enforcement` values are owner-declared).

   **Semantics binding is the answer to "owner-defined yet agent-interpretable".** The
   owner invents the words (verbatim, adaptive); the catalog declares each word's mapping
   onto a small fixed semantics axis; the agent reads only the fixed axis (deterministic).
   Owner prose stays in `remarks` next to the machine-readable field, never as the
   machine signal. Obligation *typing* (binding / non-binding, presumption-of-compliance)
   carries the **EASA semantics** (ADR-016); `enforcement` carries the deterministic /
   decision-model / agentic distinction (MHC). All are OSCAL props, not foreign constructs.

9. **L2 declares, L4 evaluates (MECE boundary).** `enforcement` and `deviations` are
   **optional L2 declaration fields** — L2 says *how a rule is meant to be enforced* and
   *that a deviation exists with its rationale*. Their **evaluation and status** (was the
   rule enforced? is the deviation `verified`/approved? the MHC decision point) are
   **Layer 4 (Assessment)**, not L2. This keeps the layers MECE and prevents L2 from
   drifting into assessment state (the conflation ADR-016 explicitly guards against).

10. **Two separate files, enforced by the tool (binding).** The L1 catalog and the L2
    rule-set are **always separate documents** (ADR-014 placement; drivers 1–3: the
    catalog stays pure NIST, readable by standard tooling). A single document mixing a
    catalog and a rule-set is **invalid**. Where a source mixes concerns (a rule row that
    carries both the verbatim `statement` — L1 — and `modality`/logic — L2), migration
    **splits** it into a catalog file (verbatim statements) and a rule-set file (logic),
    linked by `control-id` + `link rel="decision-logic"`. This is why `control-id` is
    **mandatory**, not optional: an L2 rule always points at an L1 control.

    The four-layer verification tool (`oscal4rail validate`) MUST enforce, as errors
    (Design by Contract post-conditions), that:
    - **Separation:** a catalog document contains no rule-set and vice versa.
    - **Referential integrity:** `catalog-ref` names the served catalog by **identity**
      (`catalog-uuid`, matched against the resolved catalog's own `uuid`) and
      **resolution** (`href`); every `rule.control-id` resolves to an existing control
      in that catalog. The catalog's owner/publisher and regulation are not in
      `catalog-ref` — they live in the catalog's own metadata (SSOT).
    - **Version consistency:** `rule-set.metadata.version` equals the catalog's
      `metadata.version` (ADR-014). A change to one forces a coordinated bump of the other.
    Owner convenience (one thing to read) is served by the round-trip generator, which
    *co-presents* control + linked logic without physically merging the files.

### Scope note (Framework ≠ Content, ADR-007)

This ADR fixes the *format mechanism* and the *rule-fields convention*. It authors no
regulatory content: obligation/status/enforcement vocabularies, context dimensions, and
the concrete rules are owner content. The convention was **stress-tested** against one
public example (BS-KI, in-repo) and two DB-internal rule artifacts (used only as
structural viability evidence, not published here); their convergent structure
(thresholds with operators, RFC-2119-style modality, lifecycle IDs, deviations,
calibratable parameters) confirms the convention is viable and adaptive. A concrete
migration of an internal rule set onto this schema is Project-2 work
(`oscal4rail-poc-db-catalogs`), not part of this framework ADR.

## Considered Options

### Option A: Bespoke O4R logic language / container (rejected)
A new JSON/YAML logic tree (all-of/any-of/not/threshold) defined by O4R.
- (−) Reinvents what `constraint/test` already provides (fact 1); violates Occam.
- (−) A new language is *not* "logic lives in the OSCAL model" — it is an O4R format
  bolted on, weakening the ADR-016 K7 claim and standard conformance.
- (−) New schema surface to maintain and to teach owners.

### Option B: OSCAL-native `constraint/test` + Metapath subset + Mapping Model (CHOSEN)
- (+) Logic lives in stock OSCAL; maximal standard conformance (K3/K7).
- (+) Minimal own surface: a convention + a thin additive constraints schema (Occam).
- (+) Reuses the Mapping Model for lateral relations; no fork.
- (−) Metapath is powerful; an unconstrained use would hurt owner auditability — hence
  the mandated deterministic Subset v1 (driver 2), fixed in Decision point 2.

### Option C: Full (unconstrained) Metapath (rejected for now)
- (+) Maximum expressiveness, zero O4R convention.
- (−) Non-deterministic/opaque expressions are possible; breaks MHC auditability
  (driver 2). Rejected in favor of the constrained subset (Option B).

## Resolved in this ADR (previously open)

**The Metapath subset is fixed as Subset v1** (see Decision point 2) — allowed and
forbidden constructs are enumerated. The **canonical rule-fields convention** is fixed
(Decision point 8) with open, catalog-declared vocabularies for `modality`/`status`/
`enforcement`. The **L2/L4 boundary** is fixed (Decision point 9). What remains for
#9/#11 is *encoding*, not *deciding*: the JSON Schema, the EARS phrasing, and the worked
examples (BS-KI public; internal artifacts as neutralized structural patterns only).

## Tooling implications

Two kinds of tooling must be distinguished (MECE), to avoid conflating format
enforcement with a semantic engine:

1. **Structural validation — implemented with this ADR (part of `tools/validate.py`).**
   The four-layer validator now recognizes the `rule-set` root as an OSCAL4Rail-native
   model and enforces, as errors (Design by Contract post-conditions), the point-10
   contract: **separation** (a document is either a catalog/profile or a rule-set, never
   both), **referential integrity** (`catalog-ref.catalog-uuid` matches the resolved
   catalog's `uuid`; `catalog-ref.href` resolves; every `rule.control-id` exists in that
   catalog), **version equality** (`rule-set.metadata.version` ==
   catalog `metadata.version`, ADR-014), plus intra-artifact integrity (declared
   `modality`/`status`/`enforcement` labels; `rule-group.member` resolves to a
   `rule-id`). This is format enforcement, not a semantic engine, so it belongs here —
   the same two-pass validator that already checks catalog/profile constraints
   (ADR-013), extended by the rule-set model.

2. **Semantic evaluator + round-trip generator — ADR-015 class, NOT here.** The
   **evaluator** that *executes* the Metapath-Subset-v1 expressions and decides
   applicability, and the **round-trip generator** that co-presents control + linked
   logic for owner sign-off, are tools in the sense ADR-016 separates out ("a hosted
   tool/SaaS belongs to the separate tool/verification story, **not** this grid"). They
   are decided in an ADR-015-class tool story. This ADR states the *contract* they must
   honor (deterministic subset, auditability, round-trip), not their implementation.

## Consequences

### Positive
- Logic is stock OSCAL; the catalog/control stays pure NIST (ADR-014 driver 1).
- Own surface is minimal: a convention + a thin additive schema (#9), mirroring the
  existing catalog-constraints schema.
- Lateral relations reuse the Mapping Model; no fork, no duplication.
- Verbatim invariant preserved; determinism/auditability serve MHC.

### Negative / Risks
- The Metapath subset must be defined carefully; too wide breaks auditability, too
  narrow cannot express real rules. Mitigation: #9/#11 fix it with EARS + examples,
  reviewed with an owner.
- Metapath literacy is lower than bespoke JSON among owners (K8 concern). Mitigation:
  the round-trip generator (tool story) presents human-readable conditions; owners
  verify the regenerated document, not the Metapath.
- Plain NIST tooling will not enforce the O4R subset or version-equality. Mitigation:
  `oscal4rail validate` enforces it; wire into CI as a hard failure (ADR-014 follow-up).

## Follow-ups

- #9: `oscal4rail-rules.schema.json` (Draft 7, additive over NIST) encoding this decision. **Done with this ADR.**
- #11: document the generic applicability sources slot and the Metapath subset
  (reference + EARS + examples). **Done with this ADR** (`docs/reference/rules-layer.md`).
- Structural validation (rule-set model, separation, `control-id` integrity, version
  equality) in `tools/validate.py`. **Done with this ADR** (point 10 contract enforced).
- ADR-015-class tool story (still open): the semantic **rules evaluator** (executes
  Subset v1) + the **round-trip generator** (co-presents control + logic for sign-off).
- Minimal worked example: BS-KI 2.1 applicability as linked decision-logic. **Done.**
- **Empirical rule-quality validation (the real acceptance test).** This convention is a
  *hypothesis* until an agent demonstrably decides rule applicability correctly against a
  rule set built in this format. Build a **golden set**: input cases with a *known*
  expected outcome (applies / does-not-apply, which obligation), have an agent evaluate
  them against the authored rules, and **measure the hit rate** against the expected
  answers. Rule quality is this measured score, not an assertion. The migration of an
  internal rule set (Project 2) is a natural first test corpus. Belongs to the
  assessment/tool story (L4 / ADR-015 class), not to this format ADR.

## References

- [ADR-014: Rules-Layer Placement](./ADR-014-rules-layer-placement.md)
- [ADR-016: Rules-Format Decision Criteria and Scoring](./ADR-016-rules-format-decision-criteria.md)
- [ADR-012: Canonical Serialization](./ADR-012-canonical-serialization.md)
- [ADR-007: Tooling Foundation / Framework ≠ Content](./ADR-007-tooling-foundation.md)
- [catalog-format.md §3 (verbatim), §6 (applicability)](../reference/catalog-format.md)
- NIST OSCAL Control Mapping Model — https://pages.nist.gov/OSCAL/learn/concepts/layer/control/mapping/
- NIST OSCAL issue #1069 (Metapath in `constraint/test`) — https://github.com/usnistgov/OSCAL/issues/1069
- Pinned NIST schemas: `schemas/nist/oscal-catalog.json`, `schemas/nist/oscal-mapping.json`

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
