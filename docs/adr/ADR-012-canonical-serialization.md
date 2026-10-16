# ADR-012: Canonical Serialization — YAML Leading, JSON/XML Generated via OSCAL Tools

**Status:** Accepted

**Date:** 2026-10-16

**Deciders:** Jens Grote

## Context

OSCAL defines a single information model with **three interchangeable serializations**
— XML, JSON, and YAML — that are convertible into one another without loss. The
project must decide how it carries catalogs (and later profiles, mappings,
assessments) in the repository:

- **either** maintain the same content word-for-word in all three serializations, or
- **choose one leading (canonical) serialization** and generate the other two.

This is the same class of problem already decided for the base schemas in
[ADR-008](./ADR-008-reproducible-schema-acquisition.md): a hand-maintained copy
drifts. Maintaining three parallel serializations of every catalog would multiply
that risk by three and break the Single Source of Truth principle — the very
problem OSCAL4Rail exists to solve (silent drift, Goodhart's law: "it's
machine-readable" must not replace fidelity to a single source of truth).

### Facts (verified 2026-10-16)

1. **The internal PoC used YAML as the leading format**, with JSON only as an
   occasional second representation. In `oscal4rail-poc-db-catalogs`: 46 YAML files
   vs. 3 JSON; catalogs such as `eam-vorgaben-catalog.yaml` carry a parallel
   `.json`. No XML was used. (Inspected 2026-10-16.)
2. **The framework repo is already YAML-leading.** The only catalog,
   `catalogs/bs-ki/de/bs-ki-de.yaml`, is YAML; the fetched NIST schemas are JSON
   (ADR-008); `schemas/oscal4rail/` (constraints schema, #3) is JSON Schema.
3. **A lossless serialization roundtrip holds for BS-KI.** A model-level roundtrip
   YAML → JSON → YAML on `bs-ki-de.yaml` is identity (`YAML==JSON==YAML` all true,
   9 controls preserved). This is a principle proof via PyYAML/json, not the
   production tool.
4. **The official OSCAL tool validates the catalog.** `compliance-trestle v5.2.0`
   (OSCAL 1.2.1) imports the YAML natively and reports, verbatim:
   `VALID: Model … passed the Validator to confirm the model passes all registered
   validation tests.` `trestle` reads/writes YAML natively and has **no** `convert`
   subcommand.
5. **Serialization conversion is a NIST-provided, solved problem.** OSCAL schemas
   and converters are generated deterministically from the metaschema; the NIST
   `oscal-cli convert` command converts between XML/JSON/YAML. (See ADR-008 facts
   1–2 and NIST OSCAL tooling.)

### Not yet verified

- `oscal-cli convert` (Java-based) was **not** executed locally (tool not
  installed). The lossless YAML↔JSON↔XML conversion via `oscal-cli` is therefore
  asserted from NIST documentation and the model-level roundtrip, not yet
  demonstrated end-to-end in this repo. Tracked for CI (#5 / later #14).

## Decision

**Adopt a single canonical serialization and generate the others.**

1. **YAML is the canonical, leading serialization** for all OSCAL4Rail instance
   artifacts (catalogs, and later profiles, mappings, assessment results). It is the
   SSOT and the only serialization edited or reviewed by hand.
   - Rationale: YAML wins on owner readability and `git diff` readability — which is
     exactly the project's "verifiability by design" core. The PoC and the current
     repo already live this.
2. **JSON and XML are generated, never hand-maintained.** They are produced on demand
   from the canonical YAML using the **official OSCAL tools** — `oscal-cli convert`
   for serialization conversion, `compliance-trestle` for authoring/validation/profile
   resolution. We do not write a custom converter (consistent with ADR-007: build on
   existing tooling, do not reinvent).
3. **Schemas stay JSON Schema** (Draft-07, ADR-008). One schema validates all three
   serializations because they share the same model.
4. **Language is never carried by the file extension.** For OSCAL artifacts, the
   language lives in `metadata/props[name="language"]` and the directory level
   `catalogs/<regulation>/<lang>/` — see `docs/reference/catalog-format.md` §4, §8.
   The `.en`/`.de` filename suffix convention applies **only to prose docs**
   (Markdown), not to OSCAL artifacts or schemas.

### Scope note (Framework ≠ Content, ADR-007)

This ADR fixes the *mechanism* (which serialization leads, which tool converts). It
does not change any catalog content.

## Alternatives

### Alternative A: Maintain all three serializations word-for-word
- (+) All three forms visible directly in the repo, no tool needed to read any.
- (−) **Breaks SSOT** — three independently editable sources that must stay identical.
- (−) Every change edits 3 files, 3 reviews; `git diff` shows each change three times,
  making owner verification *harder*, not easier.
- (−) Drift is a question of *when*, not *if* (same failure mode as ADR-008).

### Alternative B: One canonical serialization + generated others (CHOSEN)
- (+) SSOT preserved; one source, two generated artifacts.
- (+) Conversion is a solved NIST problem — nothing to build, just invoke.
- (+) `git diff` stays unambiguous → owner verification remains feasible.
- (−) A consumer who needs XML/JSON must run the converter (one command) if the
  generated artifact is not committed.
- (−) Generated artifacts must be produced reproducibly (CI) or they go stale.

### Choice of canonical format (Pugh, reference = YAML)

| Criterion | YAML | JSON | XML |
|---|---|---|---|
| Owner readability (verbatim check) | + | S | − |
| Diff readability (`git diff`) | + | S | − |
| Schema/tooling (JSON Schema Draft-07 native) | S | + | − |
| PoC practice / lived | + | S | − |
| NIST convertibility to the other two | S | S | S |

YAML leads on the two criteria that *are* the project's USP (readability, diff).

## Consequences

### Positive
- One source of truth per artifact; `git diff` stays meaningful for owner sign-off.
- No custom converter to maintain; conversion delegated to official OSCAL tooling.
- Every OSCAL4Rail YAML remains valid OSCAL (trestle VALID, verified) and thus
  convertible to JSON/XML by standard tools.
- Consistent with ADR-007 (tooling foundation) and ADR-008 (reproducible, pinned).

### Negative / Risks
- Generated JSON/XML can go stale unless regenerated in CI (follow-up: #5/#14).
- `oscal-cli` is Java-based → an extra runtime dependency when XML/JSON output is
  needed; `trestle` (Python) covers authoring/validation but not conversion.
- The end-to-end `oscal-cli convert` roundtrip in this repo is still **to be
  verified** (see "Not yet verified").

## Follow-ups

- Verify `oscal-cli convert` YAML→JSON→XML→YAML roundtrip on BS-KI (identity check),
  then record the exact command in `docs/` and wire it into CI (#5 → #14).
- State the serialization/conversion rule in `CONTRIBUTING.md` and `README.md`.

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
