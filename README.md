# OSCAL4Rail

> A framework building on [NIST OSCAL](https://pages.nist.gov/OSCAL/) for machine-readable railway governance. Four layers; the Catalog layer builds on NIST OSCAL, layers 2–4 are under design.
> Inspired by Arpad Vasarhelyi

**OSCAL4Rail** is an open standard for making railway governance machine-readable, deterministic, and AI-agent-ready — from internal IT standards (Konzernrichtlinien) down to regulatory compliance.

## Why OSCAL4Rail?

Railway companies translate legal requirements into internal IT governance (Konzernrichtlinien, internal standards). These company-level adaptations are today scattered across PDFs and Word documents — interpreted individually, applied inconsistently, invisible to automated systems. Nobody knows what changed between v1.0 and v2.0 at the rule level.

OSCAL4Rail is designed as a **4-layer framework**. Only the Catalog layer builds on a settled NIST OSCAL basis today; the format and tooling for layers 2–4 are still being evaluated in the project's analysis issues.

| Layer | Based on | Status |
|-------|----------|--------|
| **(1) Catalog** | [NIST OSCAL Control Layer](https://pages.nist.gov/OSCAL/learn/concepts/layer/control/) (Catalog + Profile + Mapping) | ⚙️ In progress — machine-readable regulations, cascade as profile chain, cross-framework mapping (multilingual, cross-border) |
| **(2) Rules** | *to be determined (see assessment issues)* | ⬜ Planned — applicability logic: which controls apply in which context? New — not in NIST OSCAL. |
| **(3) Change Impact** | *to be determined (see assessment issues)* | ⬜ Planned — structural diff + railway classification (tightened/relaxed/added/removed) + impact propagation through cascade |
| **(4) Assessment** | [NIST OSCAL Assessment Layer](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/) *(candidate)* | ⬜ Planned — compliance verification by AI agents and human reviewers |

The broader vision: the same framework also works for upstream regulations (EU TSI → national laws → industry standards → company implementation) — creating a complete, machine-readable regulatory cascade.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/OpenRail-Playground/OSCAL4Rail.git

# Validate an existing catalog (using compliance-trestle)
pip install compliance-trestle
cd OSCAL4Rail
trestle init
trestle import -f catalogs/bs-ki/de/bs-ki-de.yaml -o bs-ki-de
trestle validate -a
# ✅ VALID: Model passed all registered validation tests.
```

## The End Goal: Agentic Assessment

The primary use case for OSCAL4Rail is **automated compliance verification by AI agents**:

```
┌──────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│  OSCAL4Rail  │     │    AI Agent (MCP)    │     │   Railway System     │
│  Catalog     │────▶│                     │◀────│   (IT, Vehicle, Infra)│
│  + Profile   │     │  1. Load Profile     │     │                      │
│  + Rules     │     │  2. Resolve Controls │     │  System properties,  │
│              │     │  3. Check Evidence   │     │  configs, docs       │
└──────────────┘     │  4. Produce Result   │     └──────────────────────┘
                     └──────────┬────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  OSCAL Assessment    │
                     │  Results             │
                     │                      │
                     │  - Findings per ctrl │
                     │  - Evidence refs     │
                     │  - Railway scale:    │
                     │    ✅ vollständig     │
                     │    ⚠️  teilweise      │
                     │    ❌ nicht erfüllt   │
                     └──────────────────────┘
```

The agent:
1. **Loads** the applicable Profile (which controls apply to THIS system?)
2. **Resolves** it against the upstream Catalog (Profile Resolution → concrete control set)
3. **Checks** each control against system evidence (configuration, documentation, APIs)
4. **Produces** a machine-readable Assessment Result in OSCAL format

This requires ALL four layers to work together:
- **Catalog** provides the controls (what must be fulfilled)
- **Profile** selects the applicable subset (what applies to MY context)
- **Rules** determine applicability conditions (when does a control apply?)
- **Assessment** captures the findings (is it actually fulfilled?)

The [compliance-trestle-mcp](https://github.com/oscal-compass/compliance-trestle-mcp) server already provides the agent interface — OSCAL4Rail adds the railway-specific semantics on top.

## Tooling Stack

OSCAL4Rail builds on established OSCAL tooling rather than reinventing the wheel (→ [ADR-007](docs/adr/ADR-007-tooling-foundation.md)):

| Tool | Role in OSCAL4Rail | Source |
|------|-------------------|--------|
| **[compliance-trestle](https://github.com/oscal-compass/compliance-trestle)** | Validation, Profile Resolution, Workspace, Plugin Host | OSCAL-Compass (IBM) |
| **[oscal-deep-diff](https://github.com/usnistgov/oscal-deep-diff)** | Structural diff between catalog versions (candidate for Layer 3, under evaluation) | NIST |
| **[compliance-trestle-mcp](https://github.com/oscal-compass/compliance-trestle-mcp)** | AI agent integration via Model Context Protocol | OSCAL-Compass |
| **trestle-oscal4rail** (planned) | Railway plugin: cascade, semantic diff, assessment scales | OSCAL4Rail |

### NIST OSCAL Models – Implementation Status

| Model | OSCAL Layer | OSCAL4Rail Status | Agent Relevance |
|-------|-------------|-------------------|-----------------|
| Catalog | Control | ✅ Implemented (BS-KI, 42 controls) | Agent reads controls from here |
| Profile | Control | 🟡 Schema imported, Profile Resolution validated | Agent resolves "what applies to me" |
| Control Mapping | Control | 🟡 Schema imported | Cross-framework traceability |
| Component Definition | Implementation | 🟡 Schema imported | Agent identifies system-under-test |
| Assessment Plan | Assessment | 🔜 Planned | Agent follows this as test plan |
| Assessment Results | Assessment | 🟡 Schema imported | **Agent writes findings here** |
| POA&M | Assessment | ⏳ Later | Remediation tracking |

> 🟡 = Schema available + validator supports it, no railway-specific example yet

## Key Insight: The Regulatory Cascade IS a Profile Chain

The defining railway innovation — the multi-level regulatory cascade — maps directly to existing NIST OSCAL mechanisms:

```
EU TSI Catalog        → OSCAL Catalog
    ↓ specializes
National Profile      → OSCAL Profile (selects + constrains from EU)
    ↓ specializes
Industry Standard     → OSCAL Catalog (resolved from profile)
    ↓ specializes
Company Profile       → OSCAL Profile (selects subset for own systems)
    ↓ operationalizes
System Assessment     → OSCAL Assessment Results (agent-produced)
```

Each cascade level is a **Profile** that selects controls from an upstream Catalog. Profile Resolution produces a new Catalog. The agent consumes the final resolved Catalog and produces Assessment Results.

Railway-specific extensions are modeled as OSCAL `props` with namespace `ns="https://github.com/OpenRailAssociation/oscal4rail/ns"`:
- `cascade-level`: International | EU | National | Agency | Industry | Company | System
- `conformance-constraint`: must-not-contradict | specializes | implements
- `assessment-scale`: vollständig | teilweise | nicht-erfüllt | nicht-relevant
- `assessor-type`: human | agent | hybrid

## Documentation

| Type | Document | Description |
|------|----------|-------------|
| **Architecture** | [docs/arc42.md](docs/arc42.md) | Full arc42 architecture documentation |
| **Motivation** | [docs/motivation.md](docs/motivation.md) | Why OSCAL4Rail exists and what problem it solves |
| **Issue Plan** | [docs/ISSUES-PLAN.md](docs/ISSUES-PLAN.md) | Roadmap, Gap-Analyse, planned GitHub Issues |
| **ADR-005** | [docs/adr/ADR-005](docs/adr/ADR-005-law-as-code-relationship.md) | Relationship to Law-as-Code / SPRIND |
| **ADR-006** | [docs/adr/ADR-006](docs/adr/ADR-006-oscal4rail-vs-rulemapping.md) | OSCAL4Rail vs. Rulemapping positioning |
| **ADR-007** | [docs/adr/ADR-007](docs/adr/ADR-007-tooling-foundation.md) | compliance-trestle + oscal-deep-diff as tooling foundation |
| **ADR-012** | [docs/adr/ADR-012](docs/adr/ADR-012-canonical-serialization.md) | Canonical serialization: YAML leading, JSON/XML generated |
| **ADR-014** | [docs/adr/ADR-014](docs/adr/ADR-014-rules-layer-placement.md) | Rules-layer placement: separate linked logic artifact, version-coupled via `metadata.version` |
| **ADR-016** | [docs/adr/ADR-016](docs/adr/ADR-016-rules-format-decision-criteria.md) | Decision criteria and scoring method for the rules-layer format selection (work in progress) |
| **Catalog Format** | [docs/reference/catalog-format.md](docs/reference/catalog-format.md) | Railway Profile over NIST OSCAL: IDs, verbatim, applicability, metadata layers |
| **OSS Structure** | [docs/oss-structure.md](docs/oss-structure.md) | Future project structure and governance |
| **Tutorial** | [docs/tutorials/getting-started.md](docs/tutorials/getting-started.md) | Extract your first regulation catalog |
| **How-To** | [docs/how-to/integrate-agents.md](docs/how-to/integrate-agents.md) | Integrate OSCAL4Rail into AI agents and skills |
| **How-To** | [docs/how-to/verify-it-systems.md](docs/how-to/verify-it-systems.md) | Verify your IT systems against OSCAL4Rail catalogs |
| **How-To** | [docs/how-to/migrate-existing-governance.md](docs/how-to/migrate-existing-governance.md) | Migrate existing governance to OSCAL4Rail |
| **Examples** | [docs/examples/](docs/examples/) | Example catalogs and use cases |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |

## Example Implementations

| Implementation | Language | Status | Source |
|----------------|----------|--------|--------|
| `examples/bs-ki/de` | German | ✅ 42 controls | [BS-KI v1.0](https://www.oev-info.ch/de/branchenstandard/nationaler-branchenstandard-kundeninformation) |
| `examples/bs-ki/fr` | French | 🔜 planned | BS-KI v1.0 |
| `examples/bs-ki/it` | Italian | 🔜 planned | BS-KI v1.0 |
| `examples/tsi-tat` | English | 🔜 planned | EU TSI Telematics |

> **Note:** These are example implementations demonstrating how OSCAL4Rail works in practice. They are not official catalogs published by the respective standards bodies (KKI, ERA). Official catalogs would be published directly by standards bodies once they adopt OSCAL4Rail.

## Relationship to Law-as-Code / Rulemapping

### OSCAL Control Mapping vs. Rulemapping – different concerns

These two sound similar but solve fundamentally different problems:

| | **OSCAL Control Mapping** (Layer 1) | **Rulemapping** (Layer 2) |
|---|---|---|
| **Question** | "Which controls from Framework A correspond to which in Framework B?" | "Under which conditions does a control APPLY?" |
| **Type** | Static relationship between frameworks | Dynamic decision logic within a framework |
| **Example** | BS-KI 2.1 (CH) ↔ TSI TAT 4.2.1 (EU) = equivalent | BS-KI 2.1 applies IF station AND ≥800 passengers AND rail |
| **Output** | "A covers B at 85%" (coverage + gaps) | "For YOUR system: yes/no/not relevant" |
| **Actor** | Compliance team (once, when mapping frameworks) | Agent/system (at every assessment) |

They complement each other in the assessment flow:

```
1. Profile selects controls (what's in scope?)        ← Layer 1 (Profile)
2. Rulemapping checks applicability (does it apply?)  ← Layer 2 (Rules)
3. Agent assesses compliance (is it fulfilled?)       ← Layer 4 (Assessment)
4. Control Mapping shows implication                  ← Layer 1 (Mapping)
   ("fulfilling BS-KI 2.1 also covers TSI TAT 4.2.1")
```

### Positioning in the Law-as-Code ecosystem

OSCAL4Rail is positioned within the emerging Law-as-Code ecosystem:

| Actor | Role |
|-------|------|
| **SPRIND** | Funds the Law-as-Code initiative for machine-readable legislation |
| **Rulemapping Group** | Defines the rules format — **adopted by OSCAL4Rail as Layer 2** |
| **OpenCode.de** | Will host the machine-readable artifacts |
| **OSCAL4Rail** | Sectoral governance layer for railway — manages, versions, and verifies rules at scale |

| Phase | Who | Tool | Question |
|-------|-----|------|----------|
| **Create** | Legislators, standards bodies | Rulemapping | "How do I formulate this rule precisely?" |
| **Manage** | Compliance teams, IT architects | OSCAL4Rail | "Which rules apply? What changed? Is our implementation conformant?" |
| **Verify** | AI agents, human reviewers | OSCAL4Rail Assessment Layer | "Does system X comply with control Y?" |

Railway regulation bodies (ERA, EBA, BAV) currently publish as PDF only. Once the Law-as-Code ecosystem delivers machine-readable regulations, OSCAL4Rail is designed to consume them as authoritative upstream — replacing today's PDF extraction pipeline.

See [ADR-006](docs/adr/ADR-006-oscal4rail-vs-rulemapping.md) for the full analysis.

## License

- **OSCAL4Rail tooling and documentation:** [Apache 2.0](LICENSE)
- **NIST OSCAL base standard:** [CC0 1.0 Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)
- **Example catalogs (BS-KI, etc.):** Apache 2.0 — created at Hack4Rail @ OpenRail Association. They model, but are not official copies of, the underlying standards.
