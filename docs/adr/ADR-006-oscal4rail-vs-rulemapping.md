# ADR-006: OSCAL4Rail and Rulemapping — Complementarity or Competition?

**Status:** Accepted (amended — see note below)
**Date:** 2026-06-25
**Deciders:** Jens Grote
**Technical Story:** Evaluation of the Rulemapping Builder export (pilot BS-KI 2.1, 2026-06-25)

> **Amendment (2026-10-27, [ADR-014](./ADR-014-rules-layer-placement.md)).** This ADR
> argued for the placement of decision logic (an external rulemap, referenced via
> `link rel="decision-logic"`, rather than mixing data and logic in the catalog).
> ADR-014 **confirms** that direction and makes the **placement and version-coupling
> mechanism binding** (separate linked logic artifact; version coupling via the NIST
> `metadata.version` field, enforced by the validation tool). In **exactly this
> aspect**, ADR-006 is refined/superseded by ADR-014. The broader positioning
> (Rulemapping and OSCAL4Rail solve different problems for different audiences) remains
> unchanged. The choice of the concrete rules **format** is still open and will be
> decided after the analysis phase (AP0, issues #13–#22) in a separate ADR.

---

## Context and Problem Statement

Within the SPRIND "Law as Code" initiative, Rulemapping has established itself as a
central methodology for machine-readable legislation. OSCAL4Rail pursues a different
approach to the same underlying problem using NIST OSCAL: making regulation
machine-readable.

**The central question:** Are OSCAL4Rail and Rulemapping competing approaches, or
complementary tools that play to their respective strengths through integration?

### Trigger

- SPRIND "Law as Code" initiative with Rulemapping as its core methodology
- Pilot test of the Rulemapping Builder with BS-KI 2.1 (successful, 2026-06-25)
- Railways are subject to a deep regulatory cascade (EU → national → industry → group → subsidiary)
- Need for clarity for the OpenRail incubation and stakeholder communication

### The regulatory cascade

Railway regulation is not a flat rulebook but an inheritance hierarchy with conformant
specialization:

```
EU directive / TSI (abstract)
  "Systems must be protected against known vulnerabilities"
    │
    ▼ national implementation
BSI IT-Grundschutz / BSKG / EBO
  "Patches must be applied following a risk assessment"
    │
    ▼ group rule
DB guideline
  "You must patch according to BSI Grundschutz"
    │
    ├─▼ DB Systel                          ├─▼ DB InfraGO
    │  "CVSS score sets the deadline:      │  "Only KRITIS systems,
    │   Critical ≤72h, High ≤7d..."        │   per method XYZ"
    │                                       │
    └── both CONFORMANT to the DB guideline ┘
```

Each level **specializes** the one above, it may concretize but not contradict.
Different subsidiaries may implement the same parent rule differently, each in a
conformant way.

---

## Decision Drivers

1. **Rule content**: What does the rule say? Verbatim, auditable.
2. **Applicability**: Whom does it apply to? (channel, transport mode, obligation)
3. **Decision logic**: Under which conditions does it apply? (thresholds, exceptions)
4. **Change tracking**: What has changed? New, removed, tightened, relaxed, replaced?
5. **Consistency & redundancy**: Are there duplications, contradictions, additions across rulebooks and levels?
6. **Cascade & inheritance**: Can the hierarchy EU → national → group → subsidiary be represented?
7. **Conformance checking**: Is a specialization still conformant to the parent rule?
8. **Schema validatability**: CI-capable validation against a formal schema?
9. **Stable identifiers**: For version diff and cross-system referencing?
10. **Openness**: No vendor lock-in, open source, open standards?
11. **Independence**: Does each approach also work on its own?

---

## Analysis: Strengths and Weaknesses

### OSCAL4Rail

| Dimension | Strength | Weakness |
|-----------|----------|----------|
| Rule content | Verbatim quotes, auditable, no interpretation | – |
| Applicability | Matrix model (channel × transport mode → obligation) | Static, no conditional logic |
| Decision logic | – | Not modelable. Thresholds only as free text |
| Change tracking | Semantic diff at control level: new, changed, removed | – |
| Consistency & redundancy | Comparison across catalogs (diff/alignment) | Contradiction detection not yet implemented |
| Cascade & inheritance | ✅ OSCAL layer model: Catalog → Profile → Component Definition | – |
| Conformance checking | Architecturally possible (profile inheritance), not yet built | – |
| Schema validation | ✅ NIST JSON Schema, CI-capable | – |
| Stable IDs | ✅ Chapter-based, semantic | – |
| Openness | ✅ Apache 2.0, OSCAL itself CC0, existing tooling ecosystem | – |

### Rulemapping

| Dimension | Strength | Weakness |
|-----------|----------|----------|
| Rule content | – | No verbatim model. Rule text only as free text in `alttext` |
| Applicability | – | No applicability model |
| Decision logic | ✅ Boolean operators (OR, AND, XOR, NAND, NOR), negation, tree structure | Thresholds only as free text in the node title |
| Change tracking | – | No versioning in the format, no diff tooling |
| Consistency & redundancy | – | No comparison between rulemaps foreseen |
| Cascade & inheritance | – | No layer model, no hierarchy between rule levels |
| Conformance checking | – | Not foreseen |
| Schema validation | – | No published schema (XSD/JSON Schema) |
| Stable IDs | – | Numeric (auto-increment), not semantic |
| Openness | RUML announced as an open standard. Builder free to use | As of today: proprietary format, not schema-validatable |

---

## Core Finding

**OSCAL4Rail and Rulemapping solve fundamentally different problems.**

### Different purposes

| Dimension | Rulemapping | OSCAL4Rail |
|-----------|-------------|------------|
| **Audience** | Citizens, case workers, lawyers, legislators | IT architects, compliance teams, standardization bodies |
| **Core question** | "Does this rule apply to *my individual case*?" | "How do I manage *10,000 rules* across 5 levels with change tracking?" |
| **Interaction** | A human walks interactively through a decision tree | A machine checks automatically against a catalog |
| **Result** | A yes/no for one concrete case | A compliance report across all systems and rules |
| **Scale** | One law, one case | Hundreds of rulebooks, thousands of controls, over years |
| **Analogy** | Advisor at the counter / self-service website | Auditor with a checklist |

### Rulemapping: citizen–state dialogue

Typical Rulemapping use cases:
- "Do I need a building permit for my extension?" → Floor area? Height? Zoning plan? → Yes/No
- "Do I need a visa for Thailand?" → Length of stay? Purpose? Nationality? → Yes, type X / No
- "Which tax forms must I fill in?" → Self-employed? Children? Income? → Annex N + KAP

This is an **interactive single-case decision tree**, a human walks the tree and gets
an answer.

### OSCAL4Rail: regulation management across levels and time

Typical OSCAL4Rail use cases:
- "We operate 4,700 stops and 12 IT systems. Which 42 rules apply to each?"
- "What has changed since last year? Which rules are tightened, relaxed, new, removed?"
- "Is our implementation (DB Systel: CVSS-based) still conformant to the parent rule (DB guideline: BSI Grundschutz)?"
- "The TSI was updated, which of our systems are affected?"

This is **automated mass checking with version management**, no human walks a tree
interactively.

### No competition, different worlds

The two approaches *can* touch at one interface: when a legislator models a law via
Rulemapping, the result *could* feed as input into an OSCAL catalog. But that is a
**handover**, not integration in the sense of "both work on the same artifact".

| | Rulemapping world | Handover | OSCAL4Rail world |
|---|-----------------|----------|-----------------|
| Actor | Legislator/lawyer | → publishes → | Compliance team/IT architect |
| Artifact | Decision tree (rulemap) | → becomes → | Control in the catalog (OSCAL) |
| Purpose | "This is how you decide" | | "This is what you must comply with" |

### Not every rule needs a decision tree

Many rules are simple, binary statements without any decision logic:
- "Code must be stored publicly readable in Git."
- "Architecture decisions must be documented and published."
- "Systems must be patched."

There is nothing to "decide" here, it simply applies, full stop. No threshold, no
exception, no tree. This is the majority of all rules.

The BS-KI 2.1 pilot test (with a threshold of ≥800 passengers and multi-dimensional
applicability) is an *unusually complex* case, not the normal case.

---

## Decision

**OSCAL4Rail and Rulemapping solve different problems for different audiences. They are
neither competitors nor necessarily to be integrated.**

- **OSCAL4Rail** is the tool for **regulation management**: managing catalogs, tracking
  versions, representing cascades, checking compliance by machine.
- **Rulemapping** is the tool for **single-case decisions**: citizen self-service, case
  worker support, interactive checking.

### Possible point of contact

Where a rulebook actually contains complex conditional logic (thresholds, exceptions,
context-dependent applicability), a Rulemapping decision tree *could* exist as a
complementary artifact alongside the OSCAL4Rail control. But that is the exception, not
the rule.

```yaml
# Only for complex conditional logic, not the default
controls:
  - id: bs-ki-2.1
    title: "Aktuelle Uhrzeit"
    parts:
      - name: statement
        prose: "Bei Haltestellen mit weniger als 800 Ein- und Aussteigern..."
    links:
      - href: "rulemaps/bs-ki-2.1.xml"
        rel: "decision-logic"
        text: "Entscheidungsbaum: Anwendbarkeitsbedingungen"
```

### What OSCAL4Rail does NOT adopt from Rulemapping

- No interactive citizen dialogue
- No single-case decision tree as a core concept
- No adoption of the Rulemapping format as the primary data model

### What OSCAL4Rail delivers alone (and Rulemapping cannot)

- Regulatory cascade (EU → national → group → subsidiary)
- Semantic diff across versions
- Conformance checking between levels
- Schema-validated catalogs with stable identifiers
- Change tracking: what is new, removed, tightened, relaxed

---

### Complementarity at the process level, not the data level

The complementarity of Rulemapping and OSCAL4Rail lies not in wiring both formats
together, but in the fact that they serve **different phases in the life cycle of a
rule**:

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Author the rule (rule writer)                      │
│                                                              │
│  Legislator / standardization body / domain expert           │
│  ├── writes the law/regulation                               │
│  └── models the decision logic in the Rulemap Builder        │
│       → "When does what apply? Which conditions? Exceptions?" │
│                                                              │
│  Tool: Rulemapping                                           │
│  Artifact: decision tree (rulemap)                           │
└──────────────────────────────┬──────────────────────────────┘
                               │ publishes rule text
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Manage the rule (compliance team)                  │
│                                                              │
│  OSCAL4Rail reads the published rule text                    │
│  ├── extracts verbatim controls                              │
│  ├── assigns applicability                                   │
│  ├── represents the cascade (EU → national → group → subs.)  │
│  └── tracks changes across versions                          │
│                                                              │
│  Tool: OSCAL4Rail                                            │
│  Artifact: catalog with controls                             │
└──────────────────────────────┬──────────────────────────────┘
                               │ catalog provided
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: Check the rule (IT architects / AI agents)         │
│                                                              │
│  Automated compliance checking:                              │
│  ├── Which controls apply to my system?                      │
│  ├── Is my implementation conformant?                        │
│  └── What has changed since the last check?                  │
│                                                              │
│  Tool: MCP agents / compliance tooling                       │
│  Artifact: compliance report                                 │
└─────────────────────────────────────────────────────────────┘
```

**Two tools, two phases:**
- Rulemapping helps the **author** of the rule to formulate it precisely and without contradiction
- OSCAL4Rail helps the **user** of the rule to manage and check it by machine

---

## Consequences

### Positive

- Clear positioning: OSCAL4Rail need not be measured against Rulemapping, different purpose
- OSCAL4Rail stays lean and focused on regulation management
- No pressure to build Rulemapping integration as a feature
- Clearly communicable toward SPRIND/OpenRail: "Different tools, different problems, possible point of contact at the legislator → compliance-team interface"
- The regulatory cascade and change tracking are OSCAL4Rail USPs that Rulemapping does not address

### Negative / Risks

- Rulemapping could be mistakenly perceived as a competitor → mitigation: this ADR as a clear communication basis
- When contacting SPRIND, the differentiation must be explained cleanly to avoid slipping into a "who is better" comparison

### Open / to be clarified

- Is a handover interface (Rulemapping → OSCAL4Rail) relevant in practice or purely theoretical?
- Will RUML be published as an open standard? (monitoring, but no dependency)
- Are there rulebooks with so much conditional logic that a systematic link becomes worthwhile?

---

## Considered Alternatives

### Alternative 1: OSCAL4Rail only (no Rulemapping)

- (+) Simpler, no external dependency
- (-) Decision logic and conditions not modelable
- (-) Agent must interpret free text for "does this rule apply to me?"
- **Assessment:** Sufficient for the majority of rules. For complex rules the logic layer is missing.

### Alternative 2: Model decision logic directly in OSCAL4Rail

- (+) Everything in one format
- (-) The NIST OSCAL Catalog has no logic model (requires custom extensions)
- (-) Breaking change relative to the OSCAL standard
- (-) Mixing of data and logic (violates the IOSP principle)
- **Rejected:** Contradicts the OSCAL philosophy and the principle of separation of concerns.

### Alternative 3: DMN (Decision Model and Notation, OMG/ISO 19510)

- (+) Open standard, established tooling (Camunda, Drools)
- (+) Formal decision tables with data types
- (-) Complex, heavyweight
- (-) No connection to the Law-as-Code/SPRIND ecosystem
- **Noted as a fallback** should the Rulemapping format remain proprietary permanently.

### Alternative 4: Catala (functional legal language, INRIA)

- (+) Open source, academically grounded, formal semantics
- (-) A programming language → lawyers/domain experts cannot work with it
- (-) Different audience, no SPRIND connection
- **Noted as a technical alternative** for the future.

---

## Validation

Pilot test conducted on 2026-06-25:
- BS-KI 2.1 "Aktuelle Uhrzeit" modeled as a rulemap (complex case with threshold)
- Import/export in the Builder successful
- Boolean logic (OR/AND) + negation (`invertlogic`) functional
- Results documented in `docs/experiments/rulemapping/`

---

## Links

- [ADR-005: Relationship to Law-as-Code Initiatives](ADR-005-law-as-code-relationship.md)
- [Experiment: Rulemapping Builder Pilot](../experiments/rulemapping-pilot.md)
- [Experiment: Export analysis](../experiments/rulemapping/README.md)
- [SPRIND Law-as-Code](https://sprind.org/en/actions/strategic-projects/law-as-code)
- [Rulemapping Builder](https://builder.rulemapping.org)
- [NIST OSCAL](https://pages.nist.gov/OSCAL/)

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
