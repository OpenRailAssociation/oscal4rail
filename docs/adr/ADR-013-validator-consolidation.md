<!--
SPDX-FileCopyrightText: 2026 DB Systel GmbH
SPDX-License-Identifier: Apache-2.0
-->

# ADR-013: Consolidated Validator (Two-Pass, Auto-Mapped O4R Constraints, Report Beside the File)

**Status:** Accepted

**Date:** 2026-10-20

**Deciders:** Jens Grote

## Context

The framework needs **one** validator that gives a single, CI-usable pass/fail for an
OSCAL4Rail artifact. Two concerns must be checked together:

1. structural validity against the pinned NIST OSCAL base schema
   ([ADR-008](./ADR-008-reproducible-schema-acquisition.md): single pinned version via
   `schemas/nist/manifest.json`), and
2. the additive OSCAL4Rail constraints
   (`schemas/oscal4rail/`, authored in the project — Framework ≠ Content,
   [ADR-007](./ADR-007-tooling-foundation.md)).

`schemas/README.md` already fixes the mechanism: the O4R constraint schemas are
**standalone** Draft-07 schemas that deliberately do **not** `$ref` the NIST schema
(Variant A, [#3](https://github.com/OpenRailAssociation/oscal4rail/issues/3)). Validation is
therefore a **two-pass** process. This ADR records the consolidation decisions for the
validator itself ([#5](https://github.com/OpenRailAssociation/oscal4rail/issues/5)).

### Facts (verified 2026-10-20)

1. The repo contains **one** `tools/validate.py` (NIST pass only). The "two duplicate
   validate.py" noted in #5 no longer applies — there is a single script to consolidate,
   not two to merge.
2. Two O4R constraint schemas exist, each applicable to exactly one model:
   `oscal4rail-catalog-constraints.schema.json` (→ `catalog`) and
   `oscal4rail-profile-cascade-constraints.schema.json` (→ `profile`).
3. Models without an O4R schema today: `assessment-results`, `component-definition`,
   `mapping`.
4. The pinned OSCAL version is the single source of truth in
   `schemas/nist/manifest.json` (`oscal_version: 1.2.3`); ADR-008 requires an artifact's
   `oscal-version` to match it.

## Decision

A single consolidated `tools/validate` with the following behaviour:

1. **Two-pass validation.** Pass 1: NIST base schema (by detected model). Pass 2: the
   OSCAL4Rail constraints — **auto-mapped by model** (`catalog` → catalog constraints,
   `profile` → cascade constraints), enabled with `--strict`.
2. **Skip-and-report for models without an O4R schema.** When no O4R schema applies, the
   O4R pass is **skipped**, not failed. The skip is **recorded in the report** so coverage
   gaps are observable (no silent drift). A skip keeps the exit code at `0`.
3. **`oscal-version` compared against the pinned tag** (ADR-008), read from
   `schemas/nist/manifest.json` — **reported, not enforced** in this version (see
   "Consciously deferred" below). A mismatch is a recorded report finding; it does **not**
   fail the run.
4. **Report beside the validated file**, in **both** Markdown (human-readable) and JSON
   (machine-/agent-readable), generated from one run: `<file>.validation.md` and
   `<file>.validation.json` in the same directory as the validated artifact.
5. **Full run report** (NIST pass + O4R pass + skips + `oscal-version` check), not only the
   gaps — for traceability.
6. **Non-zero exit on failure**, clear messages (CI-ready).

### Consciously deferred to a future release

- **Hard `oscal-version` enforcement.** The pinned-version match (ADR-008) is reported, not
  enforced. Reason: the only in-repo test catalog, `bs-ki-de.yaml`, still declares
  `oscal-version: 1.1.3` while the manifest pins `1.2.3`. BS-KI will be revised anyway once
  the Catalog Railway Profile schema is final. Bumping it now, then again later, is wasted
  work. We keep the mismatch visible in the report and defer hard enforcement until the
  catalog is updated against the final schema.
- **`--require-o4r` (strict coverage mode).** A flag that turns a skipped O4R pass into a
  failure is out of scope here. For now, models without an O4R schema pass with a recorded
  skip. Tracked for a future release in
  [#42](https://github.com/OpenRailAssociation/oscal4rail/issues/42); not on a v0.x milestone.

### Out of scope here (tracked elsewhere)

- The cross-field invariant "chapter encoded in a control `@id` equals its `source-chapter`
  prop" (`catalog-format.md` §2), which JSON Schema cannot express, is noted in
  `schemas/README.md` as validator work. Whether it ships in #5 or a follow-up is decided in
  #5, not pre-empted here.

## Consequences

### Positive
- One inspectable, dependency-lean validator (tech-stack principle: `jsonschema`, Draft-07).
- Coverage gaps are **visible** (reported), not hidden — observability by design.
- CI gets a single pass/fail plus a durable per-file report in two formats (one run → MD + JSON).

### Negative / Risks
- Without `--require-o4r`, a project cannot yet *enforce* that every artifact is O4R-checked;
  it can only *see* the gaps in the report. Mitigation: #42 (future release).

## References

- [#5](https://github.com/OpenRailAssociation/oscal4rail/issues/5) — Consolidate the validator (this work)
- [#42](https://github.com/OpenRailAssociation/oscal4rail/issues/42) — `--require-o4r` (deferred, future release)
- [#3](https://github.com/OpenRailAssociation/oscal4rail/issues/3) — two-pass constraint design (Variant A)
- [ADR-007](./ADR-007-tooling-foundation.md) — lightweight Python core; Framework ≠ Content
- [ADR-008](./ADR-008-reproducible-schema-acquisition.md) — pinned OSCAL version, `oscal-version` policy
- `schemas/README.md` — two-pass mechanism, constraint layer
