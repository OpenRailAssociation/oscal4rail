# Schemas

Two clearly separated layers (ADR-008, ADR-007):

```
schemas/
├── nist/          NIST OSCAL base schemas — FETCHED, never edited by hand.
│                  We DERIVE from these. Reproduced from a pinned OSCAL release
│                  via tools/fetch_oscal_schemas.py, verified against manifest.json.
│   ├── manifest.json   ← single source of truth: pinned OSCAL version + SHA256
│   └── oscal-*.json    ← normalized names (oscal-<model>.json)
│
└── oscal4rail/    OSCAL4Rail constraint schemas — OUR additive layer on top of NIST.
                   Railway conventions (stable IDs, mandatory props, applicability,
                   verbatim, language declaration). Authored here. (see #9)
```

## Why fetched, not committed as hand-copies

NIST no longer tracks schemas in git; each release publishes versioned schema
assets with SHA256. Hand-copying leads to drift — the previous state in this repo
mixed OSCAL 1.1.3 (catalog) and 1.2.1 (others). The fetch tool makes the base
schema reproducible and pinned to exactly one version.

## Usage

```bash
# fetch + verify all NIST base schemas for the pinned version
python3 tools/fetch_oscal_schemas.py

# verify existing files offline (CI)
python3 tools/fetch_oscal_schemas.py --verify-only

# bump the OSCAL version: edit oscal_version + release_tag in nist/manifest.json,
# then re-fetch and rewrite checksums, review the diff, commit
python3 tools/fetch_oscal_schemas.py --update-manifest
```

Current pinned version: see `nist/manifest.json`.
