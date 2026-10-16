# Contributing to OSCAL4Rail

Thank you for contributing! OSCAL4Rail is an open standard maintained by the OpenRail community.

## Types of Contributions

| Type | How |
|------|-----|
| New catalog | Extract a regulation and submit a PR |
| Catalog correction | Open an issue or submit a PR with the fix |
| Tooling improvement | PR against `tools/` |
| Documentation | PR against `docs/` |
| New use case / example | PR against `docs/examples/` |

## Core Principle: Verbatim Only

**Never paraphrase regulation text.** Every `statement` in a control must be a verbatim quote from the source document. If the source text is unclear or ambiguous, add a `guidance` part with your interpretation — but keep the `statement` unchanged.

## Language Policy

**All framework artifacts are written in English** — documentation, ADRs, code comments, commit messages, issues, and user stories.

**The only exception is verbatim catalog content**, which stays in its source language (e.g. `catalogs/bs-ki/de/` holds the German BS-KI text verbatim). This exception follows directly from the Verbatim Only principle above: a catalog reproduces its source document, so its language is the source's language.

Rationale: OSCAL4Rail is an international, cross-organisation framework (DB, SBB, ÖBB, and beyond). A single working language keeps the framework contributable by everyone and ready for the OpenRail Association.

### File naming (prose docs)

Prose documents under `docs/` (specs, how-tos, tutorials) are English-first. The
English version is the default and is **suffixless** (e.g. `catalog-format.md`).
A translation carries a language suffix (`catalog-format.de.md`). ADRs keep their
own `ADR-NNN-<slug>.md` scheme.

This filename-suffix convention applies **only to prose docs** — never to OSCAL
artifacts or schemas (see below).

## Serialization (OSCAL artifacts)

OSCAL has three interchangeable serializations (XML, JSON, YAML). This project
uses **one canonical serialization and generates the others** — see
[ADR-012](docs/adr/ADR-012-canonical-serialization.md).

- **YAML is canonical.** Catalogs, profiles, mappings, and assessment results are
  authored, reviewed, and committed as `.yaml`. YAML is the single source of truth.
- **JSON and XML are generated, never hand-maintained.** Produce them from the
  canonical YAML with the official OSCAL tools (`oscal-cli convert`;
  `compliance-trestle` for authoring/validation). Do not write a custom converter.
- **Schemas are JSON Schema** (`.schema.json`, Draft-07). One schema validates all
  three serializations.
- **Language is not carried by the file extension** for OSCAL artifacts. It lives in
  `metadata/props[name="language"]` and the directory level
  `catalogs/<regulation>/<lang>/`.

## Submitting a New Catalog

1. Fork the repository
2. Create a branch: `feat/catalog-<name>-<language>` (e.g. `feat/catalog-tsi-tat-en`)
3. Run the extraction pipeline or create the YAML manually
4. Validate: `python3 tools/validate.py catalogs/<your-catalog>.yaml`
5. Add source files to the PR description (or link to them)
6. Submit a PR with title: `feat(catalog): add <regulation> <language>`

### Required fields per control

```yaml
- id: <regulation-prefix>-<chapter>        # e.g. bs-ki-2.1
  title: "Rule title"
  parts:
    - name: statement
      prose: |
        «Verbatim quote from source»
  props:
    - name: source-chapter
      value: "2.1"
    - name: source-document
      value: "source-file.pdf"
```

## Submitting a Catalog Correction

1. Open an issue with:
   - Control ID
   - Current text
   - Correct text
   - Source: document name, page number, chapter
2. Or submit a PR directly with the fix

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(catalog): add bs-ki FR catalog
fix(bs-ki): correct verbatim quote in control bs-ki-2.5
docs: add how-to for migrating existing governance
chore: update NIST schema to v1.1.3
```

## Code of Conduct

Be respectful. This is a technical project serving the public good. Disagreements about regulation interpretation should be resolved by reference to the source document and, if needed, by consulting the relevant standards body.
