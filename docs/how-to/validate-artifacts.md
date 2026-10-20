# How-To: Validate OSCAL4Rail Artifacts

Validate a catalog, profile, mapping or assessment with a single command that
gives one CI-usable pass/fail. See [ADR-013](../adr/ADR-013-validator-consolidation.md)
for the design decisions behind the validator.

## What the validator checks

It runs **two passes** (see [`schemas/README.md`](../../schemas/README.md)):

1. **NIST base schema** (always) — structural validity against the pinned NIST
   OSCAL schema for the detected model (`schemas/nist/`, pinned via
   `manifest.json`, [ADR-008](../adr/ADR-008-reproducible-schema-acquisition.md)).
2. **OSCAL4Rail constraints** (with `--strict`) — the additive railway
   conventions (`schemas/oscal4rail/`), **auto-mapped by model**:
   `catalog` → catalog constraints, `profile` → cascade constraints.

Models without an O4R schema (e.g. `assessment-results`, `component-definition`,
`mapping`) skip the second pass. The skip is recorded in the report. A skip does
not fail the run.

The validator also compares the artifact's `oscal-version` against the pinned
tag. This is reported, not enforced (ADR-013). A mismatch is a report finding,
not a failure.

## Usage

```bash
# NIST pass only
python3 tools/validate.py catalogs/bs-ki/de/bs-ki-de.yaml

# both passes (NIST + OSCAL4Rail constraints)
python3 tools/validate.py --strict catalogs/bs-ki/de/bs-ki-de.yaml

# validate several files; suppress the per-file stdout summary
python3 tools/validate.py --strict --quiet catalogs/**/*.yaml

# do not write report files (stdout summary only)
python3 tools/validate.py --strict --report none catalogs/bs-ki/de/bs-ki-de.yaml
```

**Exit code:** `0` if every file passes; non-zero if any NIST pass fails, or any
O4R pass fails while `--strict` is set. Skips and `oscal-version` mismatches do
not change the exit code.

## The validation report

By default the validator writes a full run report beside the validated file, in
two formats from one run:

- `<name>.validation.md` — human-readable
- `<name>.validation.json` — machine-/agent-readable

> These report files are generated, not versioned. The source of truth is the
> catalog plus the validator. They are excluded via `.gitignore`
> (`*.validation.md`, `*.validation.json`) and regenerated on demand and in CI.

### Report structure (example)

Markdown (`bs-ki-de.validation.md`, shortened):

```markdown
# Validation report — `bs-ki-de.yaml`

- **Generated:** 2026-10-20T13:08:25Z
- **Mode:** strict=True · require-o4r=False (deferred, #42)
- **Model:** `catalog`
- **Overall:** ✅ PASS

## NIST base schema (pass 1)
- Schema: `oscal-catalog.json`
- Status: ✅ pass

## OSCAL4Rail constraints (pass 2)
- Schema: `oscal4rail-catalog-constraints.schema.json`
- Status: ✅ pass

## oscal-version (reported, not enforced — ADR-013)
- Artifact: `1.1.3`
- Pinned: `1.2.3`
- Match: False
- Note: oscal-version mismatch: artifact 1.1.3 != pinned 1.2.3 (reported, not enforced — ADR-013)
```

JSON (`bs-ki-de.validation.json`, same run):

```json
{
  "generated": "2026-10-20T13:08:25Z",
  "validator": "tools/validate.py",
  "mode": { "strict": true, "require_o4r": false },
  "result": {
    "file": "catalogs/bs-ki/de/bs-ki-de.yaml",
    "model": "catalog",
    "nist_pass": { "status": "pass", "schema": "oscal-catalog.json", "errors": [] },
    "o4r_pass":  { "status": "pass", "schema": "oscal4rail-catalog-constraints.schema.json", "errors": [], "reason": null },
    "oscal_version": { "artifact": "1.1.3", "pinned": "1.2.3", "match": false, "note": "..." },
    "ok": true
  }
}
```

### Status values

| Field | Values | Meaning |
|-------|--------|---------|
| `nist_pass.status` | `pass` / `fail` / `error` | structural validity against the NIST schema |
| `o4r_pass.status` | `pass` / `fail` / `skipped` / `not-run` | `skipped` = no O4R schema for this model; `not-run` = `--strict` not set |
| `oscal_version.match` | `true` / `false` / `null` | `null` = artifact declares no `oscal-version`; `false` is reported, not enforced |
| `ok` | `true` / `false` | overall result (drives the exit code) |

## Related

- [ADR-013](../adr/ADR-013-validator-consolidation.md) — validator consolidation
- [ADR-008](../adr/ADR-008-reproducible-schema-acquisition.md) — pinned OSCAL version
- [`schemas/README.md`](../../schemas/README.md) — two-pass mechanism, constraint layer
- Issue #42 — `--require-o4r` strict coverage mode (future release)
