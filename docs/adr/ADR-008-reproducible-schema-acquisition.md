# ADR-008: Reproducible Schema Acquisition and OSCAL Version Policy

**Status:** Accepted

**Date:** 2026-09-29

**Deciders:** Jens Grote

## Context

A core goal of the OSCAL4Rail Foundation is: **The Base Schema must always be retrievable
from the current NIST-OSCAL versions** — not
stored as a manually copied, drifting hand copy in the repo.

The current state confirms the problem: The schemas stored in the SSOT
(`schemas/oscal-catalog.json` etc.) declare `oscal-version` **1.1.3**, although
documentation and ADR-007 assumed 1.2.1. A manual copying process demonstrably
leads to version drift and inconsistency.

Facts (verified 2026-09-29):

1. **NIST no longer tracks schemas in the Git repo.** Since `v1.1.0` artifacts
   (schemas, converters) are *no longer* versioned, but **generated as release assets**
   ([OSCAL build/README](https://github.com/usnistgov/OSCAL/blob/main/build/README.md):
   *"As of v1.1.0, artifacts are no longer tracked in the OSCAL git repository. Instead
   artifacts are generated as part of a release."*).
2. **OSCAL is generated from a metaschema.** JSON Schema (Draft-07) and XSD are generated
   deterministically from the metaschema modules
   ([NIST/CSRC](https://csrc.nist.gov/Projects/open-security-controls-assessment-language/oscal-tools-and-metaschemas):
   *"OSCAL Schemas are generated using Metaschema modeling language."*).
3. **Each release delivers ready, verified JSON schema assets** with SHA256 checksum, e.g.
   for v1.2.3 (release 2026-08-07): `oscal_catalog_schema.json`, `oscal_profile_schema.json`,
   `oscal_assessment-results_schema.json`, `oscal_assessment-plan_schema.json`,
   `oscal_component-definition_schema.json`, `oscal_mapping_schema.json` under the pattern
   `https://github.com/usnistgov/OSCAL/releases/download/<tag>/oscal_<model>_schema.json`.
   Live test of the catalog asset for v1.2.3: HTTP 200 (verified).
4. **Current stable is v1.2.3** (patch release, focus Security/Dependencies/Build),
   successor to v1.2.2 and v1.2.1.

## Alternatives

### Alternative A: Retrieve release assets (curl + SHA256-verify)

A lean tool pulls the official `oscal_<model>_schema.json` per configured release tag and verifies them against stored SHA256 checksums.

- (+) No build stack (no Maven/NodeJS/Java/Saxon/libxml)
- (+) Deterministic: tag + checksum pin exact schema version
- (+) Matches tech stack principle "minimal, portable, inspectable"
- (−) Trusts NIST release assets (mitigated by checksum + official source)

### Alternative B: Build schemas locally from metaschema (`make schemas`)

`git checkout <tag> --recurse-submodules` + `make schemas` generates schemas from source.

- (+) Full from-source reproducibility
- (−) Heavy build stack (Maven, NodeJS, libxml, Java/Saxon) — contradicts "minimal, portable"
- (−) Higher maintenance burden, slower

## Decision

**Alternative A as standard path.** OSCAL4Rail retrieves the NIST base schemas via a
tool `tools/fetch-oscal-schemas` (implementation in WP1), which:

1. reads a **configured OSCAL release tag** (Default: current stable, currently `v1.2.3`);
2. downloads the official `oscal_<model>_schema.json` from the release;
3. verifies each file against a **stored SHA256 checksum** (manifest in repo);
4. places the schemas in a `schemas/nist/` directory, **clearly separated** from the additive
   OSCAL4Rail Constraints Layer (`schemas/oscal4rail/`).

**Alternative B (`make schemas`) is documented as an audit/fallback path** in case assets are
ever unavailable or a from-source verification is needed.

### OSCAL Version Policy (resolves Issue #32)

- **Rolling against an explicit release tag**, not against `main`/`develop`.
- The target tag is at **one** place (manifest: tag + SHA256 per model) — Single Source of Truth.
- A version upgrade is a conscious, traceable commit (bump tag, update checksums,
  run Change Engine against own catalogs).
- The `oscal-version` field in O4R artifacts must match the pinned tag (validation in WP2).
- CI validates against the pinned version always.

## Consequences

### Positive
- Schema always reproducible and exactly versioned retrievable (core goal met)
- No heavy build stack in standard case
- Version drift (like the 1.1.3 finding) is structurally excluded
- Clear separation NIST base vs. O4R constraints (Framework ≠ Content, ADR-007)

### Negative / Risks
- Dependency on availability of NIST release assets (mitigated: checksums + fallback B)
- Checksum manifest must be maintained on every version bump (conscious, documented)

## Actions

1. WP1: Implement `tools/fetch-oscal-schemas` (path A) incl. SHA256 manifest for `v1.2.3`.
2. WP1: Separate `schemas/nist/` (fetched) and `schemas/oscal4rail/` (constraints); replace old
   `schemas/oscal-*.json` (1.1.3).
3. WP2: Validator checks `oscal-version` consistency against pinned tag.
4. Document `make schemas`-fallback in `docs/how-to/`.

## References

- [OSCAL Releases](https://github.com/usnistgov/OSCAL/releases) — versioned schema assets + SHA256
- [OSCAL build/README](https://github.com/usnistgov/OSCAL/blob/main/build/README.md) — artifacts generated as release, `make schemas`
- [NIST/CSRC OSCAL Tools & Metaschemas](https://csrc.nist.gov/Projects/open-security-controls-assessment-language/oscal-tools-and-metaschemas)
- [oscal-cli](https://github.com/usnistgov/oscal-cli) — can generate schemas from metaschema (Alternative B, reference)
- Related: Issue #32 (OSCAL Version Upgrade Strategy), [ADR-007](./adr/ADR-007-tooling-foundation.md)
