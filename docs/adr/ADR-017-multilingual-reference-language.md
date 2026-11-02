# ADR-017: Multilingual Model: Same Rule Across Languages, with an Optional `reference-language` Marker

**Status:** Accepted

**Date:** 2026-10-27

**Deciders:** Jens Grote, Simon Freihart

## Context

A railway regulation may exist in several languages. BS-KI, the catalog this
framework is derived from, is published in German, French, and Italian. EU acts are
published in all official languages. Norms are often authoritative in English. The
framework must say *how* a catalog carries more than one language, without ever
translating, and without turning "the same rule in another language" into a second,
unrelated rule.

Two questions had to be separated:

1. **How is multilingualism carried structurally?** (Already specified in
   `docs/reference/catalog-format.md` §8: same chapter-based ID = same rule; two
   NIST-native patterns; language carried by `prop[name="language"]`; cross-links
   and an edge-case Control Mapping.)
2. **Which language version governs if the versions diverge?** Raised in review of
   PR #46 (`simon-frei`, verbatim): *"we need to define for multi-language controls
   which is the source/main language somewhere. you think we should integrate it
   here?"*

This ADR records the decision on question 2 and anchors the governing invariant of
question 1, because the two are tightly coupled: the marker only makes sense under
the "same rule, not a second rule" invariant.

### Facts and constraints

1. **The framework does not translate and does not judge equivalence.** Whether two
   language versions mean the same thing is the governance owner's editorial act
   (Meaningful Human Control). The framework provides structure, not content
   (Framework ≠ Content, [ADR-007](./ADR-007-tooling-foundation.md)). Deriving
   controls in other languages from one input was explicitly ruled out by the owner.
2. **Identity lives in the ID, expression in the text.** The stable, chapter-based
   control ID (§2) is the identity of a requirement; language versions sharing that
   ID are the same rule. This was already the catalog-format invariant; this ADR
   makes it a recorded decision.
3. **Authoritativeness is a regulatory fact, not a framework choice.** Who decides
   which version governs varies by regulator:
   - BS-KI: one master language (German), French/Italian derived (*"available in
     DE/FR/IT, master = DE"*).
   - EU acts: **all** official language versions are equally authentic, with no single
     master.
   - Norms: typically a de-facto English reference.
4. **Everything must stay NIST-conformant and format-portable.** Per
   [ADR-012](./ADR-012-canonical-serialization.md), YAML leads and JSON/XML are
   generated; the language carrier must survive conversion, so it is a `prop`, not
   an XML-only `@lang` attribute (catalog-format §8.3).

## Decision

**Anchor the "same rule across languages" invariant, and add an optional
catalog-metadata prop `reference-language` to mark which language version governs if
versions diverge.**

1. **Governing invariant (recorded).** Multiple language versions are the *same*
   requirement, expressed in different languages, never an additional requirement.
   The same stable, chapter-based control ID is reused across all language versions;
   only `title` and `statement` prose differ. No machine translation; each language
   version is verbatim from its own source. The owner verifies linguistic
   equivalence (MHC). (catalog-format §8.1.)

2. **`reference-language` is an optional marker, not an instruction to translate.**
   It records a fact the owner already knows: *"if in doubt, the definition in
   language X is authoritative."* The framework never generates or derives a
   language version from this value. (catalog-format §8.2.)

3. **Value range (hard rule).** A `reference-language` prop value MUST be **either**
   a single [ISO 639] language code **or** the reserved sentinel **`all`**. No other
   values are permitted. A validator MUST reject anything else.
   - exactly one language governs → one code (e.g. BS-KI: `de`);
   - a named subset governs equally → one `reference-language` prop per code;
   - every version governs equally → a single prop with value `all`.

4. **`all` and codes are mutually exclusive.** `all` already means "every version",
   so mixing it with an explicit code is contradictory and is a finding. A non-`all`
   code SHOULD name a language the regulation actually exists in; otherwise a finding.

5. **`reference-language` is optional; absence asserts nothing.** Absence means the
   owner has not singled out a governing language. **Absence is not the same as
   `all`.**

### Scope note (Framework ≠ Content, ADR-007)

This ADR fixes the *mechanism* (an optional marker and its value range). It does not
author regulatory content and does not decide, for any real regulation, which
language governs; that remains the owner's declaration.

## Alternatives

### Alternative A: Infer the primary language implicitly (e.g. "first language listed")
- (+) No new field.
- (−) Breaks under Pattern A (one file per language, so there is no single "first"
  across sibling files).
- (−) Implicit, unverifiable; the owner cannot see or sign off the intent. Rejected.

### Alternative B: Let the framework translate / generate other-language controls
- (−) The framework cannot judge linguistic equivalence (MHC); would create silent
  drift and false precision (Goodhart). Explicitly ruled out by the owner. Rejected.

### Alternative C: A single mandatory "main language" field
- (−) Cannot express the EU case, where **all** official versions are equally
  authentic and there is no single master. Rejected.

### Alternative D: Optional `reference-language`, ISO 639 code(s) or `all` (CHOSEN)
- (+) Expresses all three real cases (one master / named subset / all-equal).
- (+) Explicit and owner-set → verifiable, signed off (MHC).
- (+) Consistent with the existing `prop`-based mechanism (§8.3) and with
  multi-valued props like `applicability` (§6).
- (−) Needs a small validator rule for the value range (tracked with the constraints
  schema, #3).

### Why `all`, not a frozen 24-code list, and not `any`
- An EU act is authentic in *all official languages*, and that set changes over
  time; `all` states the intent robustly without embedding a list that silently goes
  stale. An explicit multi-code list stays available when the authoritative set is a
  fixed, named subset.
- `all` is an **all**-statement (every version is equally authoritative). `any` would
  wrongly suggest "pick any one version", inviting Goodhart (choose the convenient
  one). `all` was chosen; `any` rejected.

## Consequences

### Positive
- The owner can declare governance intent explicitly and verifiably, in one marker.
- Covers single-master (BS-KI), named-subset (norms), and all-equal (EU) uniformly.
- Stays valid NIST OSCAL and format-portable (prop, survives YAML↔JSON↔XML).
- Does not expand the framework into translation or equivalence judgement (MHC,
  ADR-007 preserved).

### Negative / Risks
- A value-range check (ISO 639 or `all`; no mixing; code must be a present language)
  must be enforced by the constraints schema/validator, tracked with #3, not built
  in this ADR.
- `reference-language` is advisory metadata; it does not and must not *enforce* which
  text a consumer reads. It records intent for human adjudication, not automated
  precedence.

## Follow-ups

- Encode the value-range rule (ISO 639 code **or** `all`; mutual exclusion; code must
  name a present language) in the OSCAL4Rail constraints schema (#3) and the
  validator.
- Enable the YAML↔JSON roundtrip verification for the multilingual examples so the
  new `reference-language` prop is shown to be preserved losslessly (examples
  `README.md`; wire into CI with #5/#14).

## References

- Catalog format: `docs/reference/catalog-format.md` §8 (esp. §8.1 invariant, §8.2
  reference language, §8.3 NIST carrier, §8.7 consistency).
- Worked example: `examples/multilingual/`.
- Issue [#7](https://github.com/OpenRailAssociation/oscal4rail/issues/7); review
  discussion on PR [#46](https://github.com/OpenRailAssociation/oscal4rail/pull/46).
- [ADR-007](./ADR-007-tooling-foundation.md) (Framework ≠ Content),
  [ADR-012](./ADR-012-canonical-serialization.md) (serialization / prop portability).

[ISO 639]: https://www.iso.org/iso-639-language-code

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
