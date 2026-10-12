# ADR-011: Generated Catalog Index (`index.json`)

**Status:** Proposed (Draft)

**Date:** 2026-10-01

**Deciders:** Jens Grote, Arpad Vasarhelyi

**Technical Story:** With potentially thousands of catalogs (one per regulatory document), an
assessment needs a single place to answer "which regulations exist and where do they belong"
without opening every catalog. This ADR deliberately fixes a **minimal first step** and defers
elaboration to future work.

---

## Context and Problem Statement

Once regulations are maintained code-first, a corpus grows to many catalogs (an organization may
reach the order of ten thousand). An assessment (Assessment Layer, L4) must know **which
regulations exist and how they are placed** (authority stream/level, theme, applicability,
lifecycle) — but it does not need the control bodies to answer that. Opening every catalog to
reconstruct this overview does not scale.

**The question:** What is the minimal, sufficient index that lets the Assessment Layer operate
over the whole corpus — without becoming a second, hand-maintained source of truth?

### Scope boundary

This ADR fixes the **minimum viable index** needed for assessment. It does **not** attempt to
design the eventual richer registry (dependency/conflict graph, change-impact queries, formats).
That elaboration is explicitly **future work** (see "Future Work").

---

## Decision Drivers

1. **Granularity is fixed:** **one catalog = one regulatory document.** This is the unit the
   index lists.
2. **Enable assessment now** — the index must carry exactly the metadata an assessment needs.
3. **No controls in the index** — control bodies stay in the catalogs; the index is heads only.
4. **Generated, never hand-maintained** — the catalogs are the single source of truth; the index
   is a derived projection (SSOT principle, ADR-008 mindset).
5. **Minimal** — do not over-engineer; defer richness to future work (Occam).

---

## Decision

**Maintain a single generated `index.json`** that lists, for every catalog in the corpus, the
**relevant metadata needed to perform an assessment** — and nothing more.

1. **One catalog per regulatory document.** The index has one entry per catalog.
2. **Projection, not authorship.** The index is **generated** from the catalogs' `metadata`
   heads. The catalogs remain the single source of truth; `index.json` is derived and is never
   edited by hand.
3. **Heads only, no controls.** Each entry carries the relevant metadata (identity, version,
   lifecycle status, authority placement, theme, applicability) — **no `controls`, no `groups`**.
4. **Purpose: enable the Assessment Layer (L4).** The index exists so an assessment can determine
   which regulations exist and which apply, without loading control bodies. Scope is limited to
   this purpose for now.

Illustrative shape (non-normative; exact fields to be pinned in tooling):

```json
{
  "generated": "2026-10-01T00:00:00Z",
  "entries": [
    {
      "catalog": "catalogs/<id>/catalog.yaml",
      "title": "...",
      "version": "...",
      "status": "in-force",
      "authority-stream": "corporate",
      "authority-level": "company",
      "theme": "...",
      "applicability": { "scope": ["..."], "legal-space": ["..."] }
    }
  ]
}
```

**"Relevant metadata" = whatever the Assessment Layer needs to select and scope regulations.**
The precise field set is fixed in the generator (and will track the Assessment Layer spec),
not frozen here.

---

## Consequences

### Positive
- The Assessment Layer can operate over the whole corpus from one artifact.
- No drift: the index is derived; catalogs stay the single source of truth.
- Cheap and simple; nothing over-designed.
- Fits code-first: the index can be regenerated on change in CI.

### Negative / Risks
- An index out of sync with the catalogs is misleading → generation must be automated and the
  index treated as a build artifact, not a source.
- The minimal field set may prove insufficient as the Assessment Layer matures (accepted;
  revisited in future work).

---

## Future Work (deferred — "future Jens")

Explicitly out of scope here, to be addressed when the need is concrete:

- Richer registry: the typed many-to-many dependency/conflict graph from ADR-010
  (`derived-from`, `conflicts-with`, …) across catalogs.
- Change-Impact (L3) queries over the corpus.
- Index format and generation strategy (full vs. incremental at large corpus sizes), consistency
  contract (behavior on dangling links or cycles), OSCAL-native vs. custom representation.

These are elaborations of this minimal index, not replacements for it.

---

## Actions

1. Implement a generator (`tools/`) that projects each catalog's `metadata` head into
   `index.json`; no controls; regenerated on change.
2. Pin the "relevant metadata" field set together with the Assessment Layer specification.

---

## References

- Related: [ADR-008](./ADR-008-reproducible-schema-acquisition.md) (SSOT / generated-not-copied
  mindset), [ADR-009](./ADR-009-adaptive-metadata-model.md) (metadata head: authority placement,
  theme, applicability — the projected fields), [ADR-010](./ADR-010-configurable-authority-meta-model.md)
  (typed relations — the basis for the deferred richer registry)
- [NIST OSCAL Assessment Layer](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/)

---

> 🤖 This document was created with AI assistance (Art. 50(4) EU AI Act). Content is subject to
> review and sign-off by a named maintainer before it changes status from Proposed to Accepted.
