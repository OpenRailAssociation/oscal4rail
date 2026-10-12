# Governance

## Project Status

OSCAL4Rail is currently in **incubation** under the OpenRail Association.

## Roles

| Role | Responsibilities |
|------|-----------------|
| **Maintainer** | Reviews and merges PRs, releases new versions, manages the roadmap |
| **Catalog Maintainer** | Responsible for a specific regulation catalog (accuracy, updates) |
| **Contributor** | Submits PRs, opens issues, participates in discussions |
| **Steering Committee** | OpenRail Association TC representatives; resolves escalations |

## Current Maintainers

See [MAINTAINERS.md](MAINTAINERS.md).

## Decision Making

- **Day-to-day** (bug fixes, documentation, minor catalog updates): Any maintainer can merge with one review
- **Significant changes** (new catalog, new props/format): Requires two maintainer approvals
- **Breaking changes** (ID scheme, schema changes): Requires Steering Committee consensus

Decisions are made transparently via GitHub issues and PRs. Unresolved disagreements are escalated to the OpenRail TC.

## Becoming a Maintainer

Contributors who have made sustained, high-quality contributions may be invited to become maintainers by existing maintainers. Maintainers are listed in MAINTAINERS.md.

## Catalog Ownership

Each regulation catalog has a designated **Catalog Maintainer** organisation responsible for accuracy and timely updates when the regulation changes:

| Catalog | Maintainer |
|---------|-----------|
| `bs-ki` | to be coordinated with KKI / SBB |
| `tsi-tat` | (to be assigned) |

## Versioning and Releases

- Catalogs are versioned independently using [Semantic Versioning](https://semver.org/)
- Tags: `<catalog>/<version>` (e.g. `bs-ki/v1.0`)
- A CHANGELOG entry is required for every release
- The tooling version follows the catalog versioning independently

## OpenRail Association Incubation

OSCAL4Rail follows the [OpenRail Association incubation process](https://github.com/OpenRailAssociation/technical-committee/blob/main/docs/incubation/process/index.md).

### Next Step

**End of July 2026:** Meeting with Max Mehl and Cornelius Schumacher (DB / OpenRail Association OSS leads) to review the incubation proposal and clarify details for formal submission to the Technical Committee.
