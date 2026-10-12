# OSS Project Structure

## Repository Layout

```
OSCAL4Rail/
├── README.md                    # Project overview and quick start
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # Apache 2.0
├── CHANGELOG.md                 # Release changelog
│
├── catalogs/                    # Published OSCAL4Rail catalogs
│   ├── bs-ki/
│   │   ├── de/bs-ki-de.yaml    # Swiss BS-KI (German)
│   │   ├── fr/bs-ki-fr.yaml    # Swiss BS-KI (French)
│   │   └── it/bs-ki-it.yaml    # Swiss BS-KI (Italian)
│   ├── tsi-tat/
│   │   └── en/tsi-tat-en.yaml  # EU TSI Telematics (English)
│   └── schema/
│       └── oscal-catalog.json  # NIST OSCAL JSON Schema (pinned)
│
├── tools/                       # Extraction and validation tooling
│   ├── extract.py               # PDF + XLSX → OSCAL4Rail YAML
│   ├── validate.py              # Validate against NIST schema
│   ├── diff.py                  # Semantic diff between catalog versions
│   └── changelog.py            # Generate CHANGELOG from diff
│
├── docs/                        # Documentation (Diátaxis structure)
│   ├── arc42.md                 # Architecture documentation
│   ├── motivation.md            # Why OSCAL4Rail?
│   ├── oss-structure.md         # This file
│   ├── tutorials/
│   │   └── getting-started.md  # Extract your first catalog (tutorial)
│   ├── how-to/
│   │   ├── migrate-existing-governance.md
│   │   ├── integrate-agents.md
│   │   └── verify-it-systems.md
│   ├── reference/
│   │   └── format.md           # Format specification
│   ├── examples/
│   │   ├── bs-ki-minimal.yaml  # Minimal example catalog
│   │   └── scenarios.md        # Use case scenarios
│   └── adr/                    # Architecture Decision Records
│       ├── ADR-001-oscal-base.md
│       ├── ADR-002-deterministic-extraction.md
│       ├── ADR-003-chapter-ids.md
│       └── ADR-004-one-file-per-language.md
│
└── .github/
    ├── workflows/
    │   └── validate.yml         # CI: validate all catalogs on every PR
    └── ISSUE_TEMPLATE/
        ├── new-catalog.md
        └── rule-correction.md
```

## Governance

### Roles

| Role | Responsibility |
|------|---------------|
| **Catalog Maintainer** | Reviews and merges catalog PRs, ensures verbatim accuracy |
| **Tool Maintainer** | Reviews extraction pipeline and validation tooling |
| **Steering Committee** | OpenRail Association representatives, standards bodies |
| **Contributor** | Anyone submitting PRs |

### Catalog Ownership

Each catalog has a designated maintainer organisation:

| Catalog | Maintainer | Standards Body |
|---------|-----------|----------------|
| `bs-ki` | SBB | KKI / Alliance SwissPass |
| `tsi-tat` | (to be assigned) | ERA |
| `ril-420` | DB | DB Netz AG |

### Decision Making

- Minor changes (typos, formatting): Catalog Maintainer approves
- Structural changes (new props, new groups): 2 Maintainer approvals
- Breaking changes (schema changes, ID changes): Steering Committee

## Release Process

1. Regulation update published by standards body
2. Contributor runs extraction pipeline → PR with updated catalog
3. CI validates against NIST OSCAL schema
4. Manual spot-check of verbatim quotes
5. Catalog Maintainer approves and merges
6. `changelog.py` generates diff summary
7. Release tagged: `<catalog>/<version>` (e.g. `bs-ki/v2.0`)

## Versioning

OSCAL4Rail uses **Semantic Versioning**:

- `Major`: Breaking change to catalog structure or ID scheme
- `Minor`: New controls added, new guidance integrated
- `Patch`: Corrections to verbatim quotes, typos

Catalog versions are independent of the OSCAL4Rail tooling version.

## Communication Strategy

### Community

- **GitHub Discussions** for questions and proposals
- **GitHub Issues** for catalog corrections and feature requests
- **Monthly community call** (once adopted by OpenRail Association)

### Adoption Path

| Phase | Target | Action |
|-------|--------|--------|
| Phase 1 | OpenRail members | Present at OpenRail Working Groups |
| Phase 2 | Standards bodies | KKI, BAV, ERA pilot — publish in OSCAL4Rail |
| Phase 3 | All European railways | Reference implementation for TSI compliance |
| Phase 4 | Regulation authors | Write new regulations natively in OSCAL4Rail |

### Publication Channels

- GitHub (primary)
- OpenRail Association blog and newsletter
- ERA regulatory channels (for TSI catalogs)
- Railway IT conferences (InnoTrans, RailTech)
