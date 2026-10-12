# ADR-010: Configurable Authority Meta-Model

**Status:** Proposed (Draft)

**Date:** 2026-10-01

**Deciders:** Jens Grote, Arpad Vasarhelyi

**Technical Story:** Generalization of the metadata model (ADR-009) after analyzing how
regulatory authority actually layers in the rail sector: multiple parallel authority streams
(statutory, normative, sectoral, corporate, vendor), many-to-many dependencies across those
streams, and the empirical reality that the same topic is sometimes regulated redundantly or
contradictorily at different places.

---

## Context and Problem Statement

ADR-006 modeled the Regulatory Cascade as a single inheritance ladder
(International → EU → National → Agency → Industry → Company → System/Team). ADR-009 refined
the metadata head into four orthogonal dimensions and layered profiles. Both are correct but
insufficient for how rail-sector authority really works:

1. **Authority is not one ladder — it is several parallel streams.** A railway artifact must
   simultaneously satisfy statutory law (e.g. an EU directive and its national transposition),
   technical norms (ISO/EN/DIN), sectoral rules (TSI/agency), corporate rules, and vendor
   specifications. "EU law" and "an ISO standard" are both "high up" — but in *different*
   streams. They cannot be stacked on one ladder.

2. **Dependencies are many-to-many and cross-stream.** A single corporate baseline can be
   derived from several parents at once — a technical norm *and* an agency standard *and* an
   EU statute — and may additionally be constrained by further statutes. This is a directed
   graph, not a tree.

3. **The ideal (no contradictions) does not match reality.** In theory each level only
   specializes its parent and never contradicts it (ADR-006 property (a)). In practice the
   same topic is regulated at several places — sometimes identically (redundancy), sometimes
   contradictorily (conflict). A model that can only express the contradiction-free ideal is
   useless for real governance; it would be false precision (Goodhart).

4. **Different organizations have different authority structures.** The set of streams, the
   depth of levels within a stream, and the relevant relationship types differ per company,
   per country, per sector. Hard-coding one fixed set into the framework would break the
   adaptivity that ADR-009 established.

**The central question:** How do we provide **one framework** that lets any organization
express its own authority structure (streams, levels, typed many-to-many relationships) and
mark where topics are specialized, overlap, duplicate, or conflict — **without the framework
prescribing any particular structure, and without assuming conformance that may not exist?**

### Scope Boundary (important)

**This ADR defines the model only — the capability to *express and detect*.** It is
deliberately independent of, and silent about, what an organization *does* with that
capability (conflict-resolution processes, ownership assignment, deadlines, CI gates). That
operational use is a separate layer that *builds on* this model and is documented elsewhere.
The model stays neutral and value-free: it must not impose any governance process, because
imposing one would contradict its own adaptivity. This is "Framework ≠ Usage", one level above
"Framework ≠ Content" (ADR-007).

---

## Decision Drivers

1. **One framework, many authority structures** — organizations configure, they do not fork.
2. **Parallel streams, not one ladder** — express concurrent authority sources (statutory,
   normative, sectoral, corporate, vendor, …).
3. **Many-to-many, cross-stream, directed** — a node may depend on several parents in several
   streams; cycles must be detectable where a relation requires acyclicity.
4. **Reality over ideal** — the model must be able to express overlap, duplication and
   contradiction as first-class relationships, not assume a clean hierarchy.
5. **Conformance is a describable state, not an assumption** — a dependency asserts intent, not
   proven conformance; the default is "unverified".
6. **Framework validates structure, owner judges meaning (MHC)** — structural validity
   (allowed relation type, direction, cardinality, acyclicity) is checkable by the framework;
   whether two texts truly mean the same or truly contradict is an owner judgment.
7. **Value-free model** — no process, no deadlines, no ownership workflow in the model layer.
8. **Reuse NIST primitives** — express everything via `prop`/`ns` and `link`/`rel` over the
   unchanged NIST OSCAL base (ADR-008); do not invent new schema elements where OSCAL has them.

---

## The Model (three parts)

### Part 1 — Node Placement (where a node sits)

Each catalog/regulation is a **node** that declares its placement via properties:

- `authority-stream` — which stream the node belongs to (value from the organization's profile)
- `authority-level` — how deep within that stream (value from the organization's profile)

Placement is an **intrinsic property of the node**. Levels are only comparable *within* a
stream; cross-stream comparison of levels is meaningless by design.

### Part 2 — Typed, Many-to-Many Relationships (how nodes relate)

Relationships are **typed directed edges** between nodes, expressed as OSCAL `link` with a
namespaced `rel`. Any number of links per node gives many-to-many for free.

Two families:

**Vertical (specialization / dependency):**

| `rel` (example) | Meaning | Cardinality | Direction | Structural rule |
|---|---|---|---|---|
| `derived-from` | concretizes / derives from | n:m | child → parent | acyclic |
| `implements` | technical realization of | n:m | impl → rule | — |
| `constrained-by` | additionally bound by | n:m | node → constraint | — |
| `applies-to` | scope / applicability | n:m | rule → target | — |
| `supersedes` | replaces (temporal) | 1:n | new → old | acyclic |

**Horizontal (topic collision — the "reality" case):**

| `rel` (example) | Meaning | Cardinality |
|---|---|---|
| `overlaps-with` | regulates the same topic (neutral) | n:m |
| `duplicates` | regulates the same topic redundantly/identically | n:m |
| `conflicts-with` | regulates the same topic contradictorily | n:m |

These horizontal relations make redundancy and contradiction **expressible and visible** in
the model, instead of hiding them behind an assumed-clean hierarchy.

### Part 3 — Conformance as a Describable Attribute (not an assumption)

A vertical relationship asserts an *intent* ("this is meant to concretize that"), not a proven
fact. Conformance is therefore a **describable attribute of the edge**, defaulting to
`unverified`:

```yaml
links:
  - rel: oscal4rail/derived-from
    href: "#parent"
    props:
      - name: conformance-status
        ns: https://oscal4rail.openrail.org/ns
        value: unverified          # unverified | conformant | specializes | conflicts | unknown
```

This attribute is **purely descriptive** (is / is-not conformant). It is deliberately *not* an
action-demanding status (nothing like "open/resolved/accepted" — that is operational use, out
of scope here).

### Meta-Schema: the framework is configured, not hard-coded

The framework does **not** define the concrete streams, levels, or relation types. It defines a
**meta-schema**: *what an authority profile may declare*. Each organization supplies an
**Authority Profile** (configuration) that the framework validates catalogs against.

```yaml
# authority-profile (configuration, authored by each organization)
authority-profile:
  id: acme-rail
  ns: https://acme-rail.example/ns
  streams:
    - id: statutory
      levels: [eu, national, state]
    - id: normative
      levels: [international, european, national]
    - id: corporate
      levels: [group, company, division, department, team]
    - id: vendor
      levels: [supplier, product-line]
  relation-types:
    - id: derived-from
      cardinality: n-to-m
      direction: child-to-parent
      acyclic: true
    - id: conflicts-with
      cardinality: n-to-m
      direction: symmetric
      acyclic: false
```

Two layers, strictly separated:

| Layer | What it fixes | Who authors |
|---|---|---|
| **Meta-schema** (framework, stable) | the shape of a profile: a profile *has* streams with levels, relation types with cardinality/direction/acyclicity, property types | OSCAL4Rail (OSS) |
| **Authority Profile** (configuration, variable) | the concrete streams/levels/relation/property types of *this* organization | each organization (owner) |

### The binding boundary (Devil's Advocate, confirmed)

A free n:m graph can degenerate into noise (everything linked to everything, phantom
relations) — Goodhart. Therefore:

- **Framework checks structure:** is the `rel` declared in the active profile? Does it respect
  the declared cardinality and direction? Does a relation marked `acyclic` form a cycle? Does a
  node's `authority-stream`/`authority-level` exist in the profile?
- **Owner judges meaning:** whether a `derived-from` edge *actually* concretizes without
  contradicting, whether two nodes *actually* conflict or merely look similar — this is semantic
  and not derivable from structure. It stays with the owner (Meaningful Human Control) and is
  never delegated to the tool.

The framework is thus a **conflict/overlap candidate detector** (hypothesis generator), never a
conflict judge.

---

## Considered Alternatives

### Alternative A: Fixed stream and relation vocabulary in the framework

Hard-code the five streams and the relation types.

- (+) Simple, immediately comparable across users.
- (−) Breaks adaptivity (ADR-009): every org with a different structure must fork.
- (−) Imposes one worldview; wrong for cross-border / multi-org reality.

### Alternative B: Free-form links, no meta-schema

Allow any `rel`/`prop` with no declared profile.

- (+) Maximally flexible.
- (−) No structural validation possible → phantom relations, drift, Goodhart.
- (−) Not machine-checkable; useless for the Assessment layer.

### Alternative C: Configurable meta-model (chosen)

Framework defines the meta-schema; each organization declares an Authority Profile; the
framework validates catalogs against the active profile.

- (+) One framework, any authority structure; configuration, not forking.
- (+) Structural validation possible (allowed rel, direction, cardinality, acyclicity).
- (+) Expresses reality (overlap/duplicate/conflict) and honest conformance state (`unverified`).
- (+) Value-free: no process imposed (Framework ≠ Usage).
- (−) Full freedom can hurt cross-organization comparability (see Open Questions).
- (−) Validator must resolve the active profile before validating a catalog.

---

## Decision

**Adopt Alternative C.** OSCAL4Rail defines a **Configurable Authority Meta-Model**:
node placement (`authority-stream`/`authority-level`), typed many-to-many relationships
(vertical + horizontal, incl. `conflicts-with`/`duplicates`/`overlaps-with`), and conformance
as a describable edge attribute defaulting to `unverified` — all expressed via NIST `prop`/`ns`
and `link`/`rel` over the unchanged base (ADR-008). Concrete streams, levels and relation types
are **declared per organization in an Authority Profile**, validated against a framework-owned
meta-schema. The framework validates **structure**; the owner judges **meaning** (MHC). The
model is **value-free and process-free** by design.

---

## Benefit for All Organizations (why this is worth it)

This model is the OSS value proposition of OSCAL4Rail — equally usable by any railway
undertaking, infrastructure manager, authority, or supplier:

- **One shared language, local vocabularies.** DB, SBB, ÖBB, SNCF, a national authority or a
  vendor each declare their own Authority Profile but speak the same meta-model. Cross-border
  artifacts become expressible in one framework instead of N incompatible ones.
- **Reality is representable, not hidden.** Overlap, redundancy and contradiction become
  first-class, queryable facts. Any organization can *see* where the same topic is governed in
  several places — the precondition for ever fixing it.
- **Honest conformance.** `unverified` by default prevents false precision: a link is a claim,
  not a proof. This protects every adopter from the "it is code, so it must be right" fallacy.
- **Machine-checkable structure, human-owned meaning.** Automatable structural checks (allowed
  relations, acyclicity, declared placement) scale to thousands of rules, while the semantic
  judgment stays where it belongs — with the rule owner.
- **A foundation for Change Impact (L3) and Assessment (L4).** Because dependencies are an
  explicit directed graph, a change in any upstream node has a traceable downstream reach — the
  same mechanism works for an EU directive, a technical norm, or a vendor spec.
- **No lock-in.** The model is NIST-OSCAL-native and value-free; adopting it does not impose any
  particular governance process on the organization.

What an organization *does* with the detected overlaps and conflicts — assign owners, set
deadlines, gate CI, resolve or consciously accept — is **operational use layered on top**, not
part of this model, and will differ per organization.

---

## Consequences

### Positive
- One adaptive framework serves the whole sector; organizations configure via profiles.
- Parallel streams and cross-stream n:m dependencies are expressible (reality fit).
- Overlap/duplication/conflict are first-class and detectable.
- Conformance defaults to `unverified` — no assumed correctness.
- Clear split: framework = structure, owner = meaning (MHC); model = capability, not process.
- NIST base untouched (ADR-008); every artifact remains valid NIST OSCAL.

### Negative / Risks
- Cross-organization comparability depends on some shared conventions (Open Question 1).
- The validator gains a profile-resolution step.
- Horizontal relations can be over-produced; prioritization is a usage concern, not a model one.

## Open Questions (deliberately not closed)

1. **Common mandatory core vs. full freedom.** Should every Authority Profile be required to
   include a minimal shared core (e.g. `derived-from` with fixed semantics) to preserve
   cross-organization comparability, with free extensions above it — analogous to ADR-009's
   "CORE profile always mandatory"? Trade-off: comparability vs. adaptivity.
2. **Conformance-status vocabulary.** Is `unverified | conformant | specializes | conflicts |
   unknown` the right minimal set, or fewer/more values?
3. **Profile interoperability.** How are two organizations' profiles mapped for cross-border
   artifacts (e.g. one org's `national` vs. another's `state`)?

## Actions

1. Specify the meta-schema (profile shape: streams, levels, relation-types with
   cardinality/direction/acyclicity, property-types) as an OSCAL4Rail constraints document
   (`schemas/oscal4rail/`), separate from NIST (ADR-008).
2. Provide a **reference Authority Profile** (neutral example, e.g. "ACME Rail") demonstrating
   the five streams and the vertical/horizontal relation types — as illustration, not norm.
3. Implement structural validation: allowed `rel` per active profile, direction, cardinality,
   acyclicity (cycle check for `derived-from`/`supersedes`), declared placement.
4. Decide Open Question 1 (mandatory core) in a follow-up ADR before v1.0.

## References

- [NIST OSCAL Model Overview](https://pages.nist.gov/OSCAL/learn/concepts/layer/overview/) —
  `prop`/`ns` extension, `link`/`rel` relationships
- [EUROSCAL — The EU Friends of OSCAL](https://euroscal.eu/) — EU OSCAL adoption community
  (cloud cybersecurity); no sectoral/authority meta-model, no overlap
- Related: [ADR-006](./ADR-006-oscal4rail-vs-rulemapping.md) (Regulatory Cascade — **refined**
  by this ADR from a single ladder to a typed multi-stream graph),
  [ADR-007](./ADR-007-tooling-foundation.md) (Framework ≠ Content),
  [ADR-008](./ADR-008-reproducible-schema-acquisition.md) (NIST base unchanged),
  [ADR-009](./ADR-009-adaptive-metadata-model.md) (adaptive metadata model — **concretized** by
  this ADR via the meta-schema / Authority Profile mechanism)

---

> 🤖 This document was created with AI assistance (Art. 50(4) EU AI Act). Content is subject to
> review and sign-off by a named maintainer before it changes status from Proposed to Accepted.
