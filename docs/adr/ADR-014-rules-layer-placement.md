# ADR-014: Rules-Layer Placement — Separate Linked Logic Artifact, Version-Coupled via `metadata.version`

**Status:** Accepted

**Date:** 2026-10-27

**Deciders:** Jens Grote

## Context

The Rules Layer (Layer 2) answers a question the Catalog (Layer 1) deliberately
cannot: under which conditions does a control apply, and with which obligation? The
Catalog carries **what** is required (verbatim statement text) and a **static**
applicability matrix (`context × obligation`, see
[catalog-format.md §6](../reference/catalog-format.md)). It does **not** carry
**decision logic**: nested boolean conditions (AND/OR), negation, typed thresholds,
and exceptions. That logic is the subject of Layer 2 (issue
[#8](https://github.com/OpenRailAssociation/oscal4rail/issues/8)).

Before specifying the *format* of that logic (a separate decision, taken after the
AP0 research phase: Rulemapping, Catala, GEMARA, see issues #13–#22), two structural
questions must be answered first, because they constrain every later format choice:

1. **Placement.** Does the decision logic live **inline** on the control inside the
   catalog, or in a **separate artifact** that the control links to?
2. **Version coupling.** If separate, how do we guarantee that the logic artifact
   (and later the assessment artifact) can never drift away from the catalog version
   it belongs to?

This ADR decides **only** these two structural questions. It does not choose a rules
format and does not author any regulatory content (Framework ≠ Content,
[ADR-007](./ADR-007-tooling-foundation.md)).

### Relationship to prior decisions

- [ADR-006](./ADR-006-oscal4rail-vs-rulemapping.md) already reasoned about
  decision-logic placement and leaned toward *not* mixing logic into the catalog
  (IOSP; "Vermischung von Daten und Logik verletzt das Prinzip"), referencing an
  external rulemap via `link rel="decision-logic"`. This ADR **confirms and makes
  binding** the separate-artifact direction and **supersedes ADR-006 in that single
  aspect** by fixing the mechanism precisely. ADR-006's broader positioning
  (Rulemapping vs. OSCAL4Rail as different tools for different jobs) is unaffected.
- The version-coupling mechanism reuses the existing NIST `metadata.version` field
  already lived by catalog and profile artifacts (verified below), consistent with
  SSOT and with the "reuse NIST mechanisms, do not fork" stance of
  [ADR-008](./ADR-008-reproducible-schema-acquisition.md) and the cascade spec.

### Facts (verified 2026-10-27)

All read from the repository's working artifacts, not assumed.

1. **Every OSCAL artifact already carries a NIST-native version block.**
   `catalogs/bs-ki/de/bs-ki-de.yaml` has `metadata` with `version: '1.0'`,
   `last-modified: '2026-06-23T13:35:00Z'`, `oscal-version: 1.1.3`, plus a
   `source-version` prop (`'1.0'`).
2. **The cascade profile uses the same block and already pins its upstream.**
   `examples/profiles/company-over-bsi-grundschutz.profile.yaml` has `metadata` with
   `version: '0.1.0'`, and a `parent-catalog-ref` prop pinning the parent catalog
   ([cascade-as-profiles.md §4](../reference/cascade-as-profiles.md)).
3. **The control already has a native link slot for external logic.** The
   Rulemapping pilot demonstrated `link rel="decision-logic" href="…"` on a control
   ([rulemapping-pilot.md](../experiments/rulemapping-pilot.md)); the control stays
   valid NIST OSCAL.
4. **NIST assessment models share the same `metadata` block** (Assessment Plan,
   Results, POA&M), so the same version mechanism extends to Layer 4 without new
   constructs.

## Decision Drivers

The two highest-weighted drivers were stated by the governance owner during the
decision dialogue:

1. **Standard conformance (high).** The catalog/control must remain *pure* NIST
   OSCAL, with no bespoke logic container forced into the catalog schema.
2. **Tooling cleanliness (high).** Validation, diff, and resolution tools must stay
   tractable; the logic format must be swappable without touching the catalog schema.
3. **Upgrade-ability (high).** Loose coupling so the rules format can evolve (or be
   replaced) independently of the catalog, but never *drift* from it.
4. **Verbatim invariant (hard).** The verbatim statement text
   ([catalog-format.md §3](../reference/catalog-format.md)) must stay untouched.
5. **Determinism and auditability (high).** An assessment result must be
   reproducible: it must be unambiguous which catalog version and which logic version
   it was evaluated against.
6. **Schema simplicity (Occam).** Do not grow the schema with coupling constructs if
   a tool check suffices.

## Considered Options

### Option A: Inline / co-location (logic defined on the control in the catalog)

Logic carried on the control via a NIST `part` or namespaced `props`.

- (+) One place per rule gives the best **owner ergonomics** (K8); single artifact to
  read.
- (+) Logic change and text change appear in **one** control diff, which is good for
  Change Impact (Layer 3).
- (−) **Burdens the catalog schema**: nested boolean logic (AND/OR, negation, typed
  thresholds) does not fit flat NIST `props`; encoding a tree into a prop value is
  ugly and hard to validate.
- (−) **Tends to violate IOSP** (data and logic mixed in one artifact), the ADR-006
  objection.
- (−) Couples the logic format to the catalog schema, which **hurts upgrade-ability**.

### Option B: Separate linked logic artifact (CHOSEN)

Logic in its own artifact; the control references it via `link rel="decision-logic"`.

- (+) Control stays **pure NIST OSCAL**; no pressure on the catalog schema (driver 1).
- (+) Logic format is **swappable** without touching the catalog, giving
  upgrade-ability (driver 3); a mightier, typed logic format can express full boolean
  trees (K1).
- (+) IOSP preserved; L1 stays lean (ADR-006 line).
- (−) Knowledge spans **two artifacts**, giving weaker owner ergonomics (K8) and a
  risk the two **drift apart**, addressed by the version-coupling decision below.
- (−) Tools must additionally check **referential integrity** (link resolves, IDs
  consistent) and version equality.

### Option C: Hybrid (simple logic inline, complex trees external)

- (+) Owner simplicity for the common binary case, power for the rare complex case
  (ADR-006: "not every rule needs a tree").
- (−) **Two mechanisms** raise conceptual complexity; violates Occam without a
  demonstrated need. Rejected for now; may be revisited if evidence demands it.

### Version-coupling sub-options (given Option B)

| Sub-option | Mechanism | Assessment |
|---|---|---|
| **B-ref** | New pinned reference prop (e.g. `rules-for-catalog-ref` with UUID, version, hash) | Powerful, but **grows the schema** with a bespoke construct. Rejected (driver 6, Occam). |
| **B-lockstep (CHOSEN)** | Reuse the existing NIST `metadata.version`; related artifacts MUST carry the **same** `version` value; equality is **enforced by the validation tool**, not by the schema | No new schema construct; coupling lives in the tool; satisfies "never independent, same change". |

## Decision

**Option B plus B-lockstep.**

1. **Decision logic lives in a separate artifact**, not inline on the control. The
   control binds it through the existing NIST `link rel="decision-logic"` slot.
   Rationale: standard conformance (driver 1), tooling cleanliness (driver 2),
   upgrade-ability and loose coupling (driver 3). The catalog/control remains pure
   NIST OSCAL.

2. **Version coupling uses the existing NIST `metadata.version` field.** No new
   schema construct, no separate metadata file. Related artifacts
   (catalog, rules, assessment) **MUST carry the same `version` value**. The equality
   is a **validation-tool check**, not a schema mechanism:
   - `oscal4rail validate` (the trestle-based tool chain) MUST fail, as an **error,
     not a warning** (Design by Contract post-condition), when related artifacts have
     diverging `version` values.
   - This guarantees the owner's condition: the artifacts are **never versioned
     independently**; a change to one forces a coordinated version bump and
     re-validation of the others.

3. **Association versus equality (explicit).** The `version` field only answers
   whether artifacts are the same version. *Which* rules artifact belongs to *which*
   catalog is established by the `link rel="decision-logic"` plus the path/naming
   convention (analogous to `catalogs/<regulation>/<lang>/…`). The link establishes
   belonging; the tool enforces version equality.

4. **Assessment follows the same mechanism.** An assessment artifact carries the same
   `version` as the catalog (and rules) it was evaluated against. This is what makes
   an assessment result deterministic and auditable (driver 5): evaluated against
   catalog `1.0` plus rules `1.0`.

### Scope note (Framework ≠ Content, ADR-007)

This ADR fixes *where the logic lives* and *how versions are coupled*. It does **not**
choose a rules format (Rulemapping, Catala, GEMARA, and so on), which is decided after
the AP0 research phase, and it authors no regulatory content.

### Overarching principle (unchanged)

Meaningful Human Control is the framework's overarching, untouchable concept and is
**not** a per-step gate: the tools and verifiers deliver *deterministic, documented,
prepared* data, with conditions made visible and conflicts surfaced as data, and the
human decides what to derive from it (and bears responsibility if they choose to
automate that derivation downstream). This ADR serves that principle by keeping
results deterministic and auditable; it does not insert mandatory human checkpoints
into the mechanism.

## Consequences

### Positive
- Catalog/control stays pure NIST OSCAL, giving maximal standard conformance and
  upgrade-ability; the rules format can evolve or be swapped without schema churn.
- Schema stays minimal (Occam): coupling is a tool check, not a construct.
- Verbatim invariant preserved: logic never touches the statement text.
- Deterministic, auditable assessments (same `version` across the chain).
- Reuses mechanisms already lived in the repo (`metadata.version`, `link`, path
  convention), consistent with ADR-006/007/008 and the cascade spec.

### Negative / Risks
- Knowledge spans two artifacts, giving weaker owner ergonomics (K8). Mitigation: the
  round-trip generator must present control and linked logic together for owner
  verification; the path/naming convention keeps them findable.
- The tool now owns an invariant the schema does not express. If a consumer validates
  with plain NIST tooling only (not `oscal4rail validate`), the version-equality check
  is skipped. Mitigation: document the invariant prominently and enforce it in CI.
- Change Impact (Layer 3) must correlate two artifacts to report that a rule changed.
  Mitigation: the equal-`version` rule means a rule change is always a coordinated
  version bump, which L3 can key on.

## Follow-ups

- Implement the version-equality check in `oscal4rail validate` (ties into the
  validator work, #5) and wire it into CI (#14) as a hard failure.
- Specify the `link rel="decision-logic"` and path/naming convention for rules
  artifacts in `docs/reference/` as part of the Rules Layer spec (#8).
- Decide the **rules format** in a separate ADR after the AP0 analyses (#13–#22);
  this ADR is a precondition for that one.
- Define how the round-trip generator co-presents control and linked logic for owner
  sign-off.

## References

- [ADR-006: OSCAL4Rail vs. Rulemapping](./ADR-006-oscal4rail-vs-rulemapping.md)
  (superseded in the inline-versus-external aspect)
- [ADR-007: Tooling Foundation / Framework ≠ Content](./ADR-007-tooling-foundation.md)
- [ADR-008: Reproducible Schema Acquisition](./ADR-008-reproducible-schema-acquisition.md)
- [ADR-012: Canonical Serialization](./ADR-012-canonical-serialization.md)
- [catalog-format.md](../reference/catalog-format.md) §3 (verbatim), §6 (applicability)
- [cascade-as-profiles.md](../reference/cascade-as-profiles.md) §4 (pinned parent reference)
- [rulemapping-pilot.md](../experiments/rulemapping-pilot.md) (`link rel="decision-logic"`)
- Issue [#8](https://github.com/OpenRailAssociation/oscal4rail/issues/8) (Specify the Rules Layer)

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
