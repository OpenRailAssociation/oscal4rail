# OSCAL4Rail Catalog Format (Railway Profile over NIST OSCAL)

**Status:** Draft · **Layer:** 1 (Catalog) · **Base:** NIST OSCAL Catalog model
**Issue:** [#2](https://github.com/OpenRailAssociation/oscal4rail/issues/2)

This is a **reference specification** of the railway-specific conventions that an
OSCAL4Rail catalog follows *in addition to* the NIST OSCAL Catalog model. NIST
defines the structure; this document defines the conventions a railway governance
catalog must obey so that every catalog uses the same ID scheme, applicability
model, and mandatory fields.

> **Framework ≠ Content** ([ADR-007](../adr/ADR-007-tooling-foundation.md)). This
> document specifies the *shape* of a catalog. It never prescribes regulatory
> content. Rule text is authored by the governance owner and carried verbatim.

The conventions below are **derived from a working catalog**, not invented: the
Swiss *Nationaler Branchenstandard Kundeninformation* (BS-KI),
[`catalogs/bs-ki/de/bs-ki-de.yaml`](../../catalogs/bs-ki/de/bs-ki-de.yaml). Every
rule in this spec cites a verbatim example from that catalog.

Source of the standard itself:
<https://www.oev-info.ch/de/branchenstandard/nationaler-branchenstandard-kundeninformation>

---

## 1. Base model and relationship to NIST

An OSCAL4Rail catalog **is** a valid NIST OSCAL `catalog`. It MUST validate against
the pinned NIST OSCAL Catalog schema (`schemas/nist/oscal-catalog.json`, version
pinned in `schemas/nist/manifest.json`, see [ADR-008] and `schemas/README.md`).

Railway conventions are expressed **only** through mechanisms NIST already provides:

| Convention carried via | NIST mechanism |
|---|---|
| Stable IDs | `group/@id`, `control/@id` |
| Verbatim rule text | `control/parts[name="statement"]/prose` |
| Applicability | `control/props[name="applicability"]` (`value` + `class`) |
| Provenance | `metadata/props` and `control/props[name="source-chapter"]` |
| Language / country | `metadata/props[name="language" | "country"]` |

OSCAL4Rail does **not** fork NIST and does **not** add new top-level fields. The
additive constraints are validated by a separate OSCAL4Rail constraints schema
(see [#3](https://github.com/OpenRailAssociation/oscal4rail/issues/3)); this spec is
the human-readable contract that schema enforces.

---

## 2. ID scheme

**Rule.** IDs are **chapter-based**, never page-based. The chapter number from the
source regulation is the stable identity of a control; page numbers change between
layouts and reprints and MUST NOT appear in an ID.

**Format.**

```
<regulation>-<chapter>[.<section>][-<context>]
```

- `<regulation>` — short, lowercase, stable slug of the regulation (e.g. `bs-ki`).
- `<chapter>` — top-level chapter number → used for `group/@id`.
- `<chapter>.<section>` — chapter and section → used for `control/@id`.
- `[-<context>]` — optional suffix for a context-specific variant of the same rule.

**Verbatim example** (BS-KI):

```yaml
groups:
- id: bs-ki-2                 # group = chapter 2
  title: Allgemeine Informationsinhalte der Kundeninformation
  controls:
  - id: bs-ki-2.1             # control = chapter.section 2.1
    title: Aktuelle Uhrzeit
```

**Invariant.** The chapter number encoded in the ID MUST equal the value of the
mandatory `source-chapter` prop on the same control (§4). This double-encoding lets
a tool cross-check that IDs were derived from chapters, not reassigned by hand.

```yaml
  - id: bs-ki-2.1
    props:
    - name: source-chapter
      value: '2.1'            # equals the chapter part of the ID
```

---

## 3. Verbatim rule text (hard invariant)

**Rule.** The normative rule text is carried **verbatim** in a part named
`statement`. The text is a 1:1 copy of the source regulation — no paraphrasing, no
summarizing, no LLM rewriting. The governance owner must be able to recognize their
own wording unchanged. This protects against *silent drift* and *Goodhart's law*
(“machine-readable” must never become a proxy that replaces fidelity to intent).

**Where.** `control/parts[name="statement"]/prose`.

**What is preserved.** Original line breaks, bullet markers, and in-text
cross-references (e.g. “siehe Abschnitt 6.5”) are kept as written. Cross-references
are **not** rewritten into links in the statement text; they remain part of the
verbatim quote.

**Verbatim example** (BS-KI 2.1, unchanged from source):

```yaml
    parts:
    - name: statement
      prose: 'Bei Haltestellen mit weniger als 800 Ein- und Aussteigern pro Tag kann auf die Angabe der
        Uhrzeit verzichtet werden.


        Die aktuelle Uhrzeit ist für die Kundschaft ein zentrales Element zur Orientierung. Sie kann analog
        oder digital dargestellt werden (Informationen zur Darstellung siehe Abschnitt 6.5).'
```

**Invariant.** A `statement` part MUST exist and MUST NOT be empty for every
control. Interpretation, guidance, and “how to comply” belong to other layers
(Rules/AMC, Layer 2), never inside the verbatim statement.

---

## 4. Mandatory props beyond NIST OSCAL

NIST does not require provenance for governance use. OSCAL4Rail does, so that every
statement can be traced back to its exact source and verified by the owner.

### 4.1 Catalog metadata props (`catalog/metadata/props`)

| prop `name` | Required | Meaning | BS-KI value (verbatim) |
|---|---|---|---|
| `country` | yes | ISO country of the regulation | `CH` |
| `language` | yes | ISO 639-1 language of this file | `de` |
| `source-document` | yes | Source file the catalog was extracted from | `BS-KI_DE.pdf` |
| `source-url` | recommended | Canonical public URL of the source | `https://www.oev-info.ch/...` |
| `source-version` | recommended | Version label used by the source | `'1.0'` |
| `source-date` | recommended | Publication date of the source | `2026-01` |

**Verbatim example:**

```yaml
  metadata:
    title: Nationaler Branchenstandard Kundeninformation (BS-KI)
    props:
    - name: country
      value: CH
    - name: language
      value: de
    - name: source-document
      value: BS-KI_DE.pdf
    - name: source-version
      value: '1.0'
    - name: source-date
      value: 2026-01
```

### 4.2 Control-level prop (`control/props`)

| prop `name` | Required | Meaning |
|---|---|---|
| `source-chapter` | yes | Original chapter number, carried verbatim; equals the chapter part of the control ID (§2) |

---

## 5. Metadata profile layers (incl. the organization-specific block)

The mandatory props in §4 are the **core** provenance fields. Beyond them,
OSCAL4Rail uses **one** metadata model that adapts by *layering profiles*, never by
forking the schema. This is the subject of
[ADR-009](../adr/ADR-009-adaptive-metadata-model.md); the catalog format references
its mechanism, it does not redefine it.

Extensions are carried **only** through NIST `prop` with an organizational
namespace (`ns`) — the NIST-sanctioned extension point, so every OSCAL4Rail catalog
stays valid NIST OSCAL (ADR-008). Three layers:

| Layer | `ns` (pattern) | Who owns it | What it carries |
|---|---|---|---|
| **Core** | `…/ns` | OSCAL4Rail | Always mandatory, sector-wide, jurisdiction-neutral: `cascade-level`, `rule-format`, `lifecycle-status`, `provenance-ref` |
| **Jurisdiction** | `…/ns/jurisdiction/<country-code>` | Owner SSOT (generated) | Country/regime-specific props and enums: `theme-maingroup`, `theme-subgroup`, `legal-space`, `scope-structure` |
| **Org / variant** | `…/ns/org/<org-id>` | Adopting organization | **The company-/vehicle-series-specific block** — the native “addendum” home: `deviates-from`, `exception-for`, `vehicle-series` |

**The organization-specific block.** The `org/<org-id>` layer is where a specific
undertaking, infrastructure manager, or vendor places its own fields. Per ADR-009:

- *“Adaptation means selecting and layering profiles, never editing or forking the
  schema.”*
- A native **addendum** specialization **is an OSCAL profile** that imports and
  concretizes a parent catalog and may carry local deviations; conformance flows
  downward (a child may specialize, never contradict its parent — ADR-006 (a)).

**Framework ≠ Content boundary (ADR-007).** This spec documents only the *mechanism*
(the `ns` extension point and the profile layer). The **content** of an org block —
the concrete company fields and values — is owned by the adopting organization and
“kept in the adopting organization’s private repository, not here” (ADR-009). The
framework MUST NOT author or silently extend an owner’s org-specific vocabulary.

**Invariant.** Core props are mandatory on every catalog. Jurisdiction and org
props are optional at the framework level and become mandatory only when the
corresponding profile is selected. No extension may collide with a NIST field name;
all extensions live under an `ns`.

---

## 6. Applicability model

A single rule often applies **differently** depending on context: binding in one
transport mode, only recommended in another. OSCAL4Rail models this with one
`applicability` prop **per context**, where:

- **`value`** = the **obligation** level in that context, and
- **`class`** = the **context** the obligation applies to.

**Verbatim example** (BS-KI 2.1 — the same rule, two obligation levels across
contexts):

```yaml
    props:
    - name: applicability
      value: verbindlich
      class: haltestelle.bahn
      remarks: v e – verbindlich (abgeltungsberechtigt), empfohlen (eigenwirtschaftlich)
    - name: applicability
      value: empfohlen
      class: haltestelle.bus-tram-metro
    - name: applicability
      value: empfohlen
      class: haltestelle.schiff
    - name: applicability
      value: empfohlen
      class: haltestelle.seilbahn
    - name: applicability
      value: verbindlich
      class: fahrzeug-innen.bahn
```

### 6.1 Obligation (the `value`)

The obligation vocabulary is **defined by the regulation**, not by the framework.
In BS-KI the two observed values are `verbindlich` and `empfohlen`, with the
regulation’s own gloss carried verbatim in `remarks`:

> `v e – verbindlich (abgeltungsberechtigt), empfohlen (eigenwirtschaftlich)`

**Rule.** The set of allowed obligation values is a per-catalog decision and SHOULD
be stated once (in metadata remarks or the catalog’s source gloss). OSCAL4Rail does
not impose a universal obligation enum, because obligation terms are regulatory
content (ADR-007).

### 6.2 Context (the `class`)

The `class` is a **dot-separated context path**, read most-significant-first. It
expresses a point in a multi-dimensional context space. In BS-KI the dimensions
are *location* × *transport mode*, plus non-physical contexts such as data delivery:

| Dimension | Observed values (verbatim from BS-KI) |
|---|---|
| location | `haltestelle`, `fahrzeug-innen`, `fahrzeug-aussen.{seite,front,heck}`, `daten.einlieferung` |
| transport mode | `bahn`, `bus-tram-metro`, `schiff`, `seilbahn` |

Examples of composed classes actually used:
`haltestelle.bahn`, `fahrzeug-innen.schiff`, `fahrzeug-aussen.seite.bus-tram-metro`,
`daten.einlieferung`.

**Rule (MECE).** For a given catalog, the context dimensions and their allowed
values form a controlled vocabulary. The vocabulary MUST be:

- *mutually exclusive* — a context path denotes exactly one point in the space, and
- *collectively exhaustive* — every context in which a rule can apply has a path.

Not every context is `location.transport`. BS-KI uses `daten.einlieferung` (data
delivery) — a non-physical context. The model is therefore “a context class drawn
from the catalog’s controlled vocabulary”, **not** a fixed `location×transport`
grid. A catalog MAY define its own dimensions; it MUST declare them (see §6.3).

### 6.3 Declaring the vocabulary

Because `class` values are a controlled vocabulary, a catalog MUST make the allowed
dimensions and values declarable so a validator can reject typos (e.g.
`haltstelle.bahn`). The declaration mechanism is specified together with the
constraints schema in [#3]. Until then, the vocabulary is the set of `class` values
observed in the catalog itself.

**Invariant.** `class` MUST NOT be empty on an `applicability` prop. An empty or
missing context makes the obligation meaningless.

---

## 7. Groups and controls

- A `group` corresponds to a **chapter** of the regulation; `group/@id` is
  `<regulation>-<chapter>`.
- A `control` corresponds to a **section**; `control/@id` is
  `<regulation>-<chapter>.<section>`.
- Group and control `title` are carried verbatim from the regulation’s headings.

**Verbatim example:**

```yaml
- id: bs-ki-2
  title: Allgemeine Informationsinhalte der Kundeninformation
  controls:
  - id: bs-ki-2.1
    title: Aktuelle Uhrzeit
  - id: bs-ki-2.2
    title: Name der Haltestelle
```

---

## 8. Multilingual model

A regulation may exist in several languages. The framework records *how* a catalog
carries more than one language, using only NIST OSCAL mechanisms. It does not
decide which languages a catalog has, and it does not translate.

### 8.1 The governing invariant: same rule, not a second rule

**Multiple language versions are the *same* requirement, expressed in different
languages, never an additional requirement.** The identity of a requirement lives
in its **stable, chapter-based ID** (§2), not in its text. Two language versions
that share the same control ID are, by definition, *one and the same rule*; a
different ID would wrongly turn “the same rule in another language” into a second,
unrelated rule.

Consequences that follow directly from this invariant:

- **ID = identity, language = expression.** The same stable ID is reused across all
  language versions of a requirement. Chapter numbers and IDs stay consistent across
  languages; only `title` and the `statement` prose (the *linguistic* content) differ.
- **The author/owner decides the languages.** A requirement may exist in one
  language, or in many (identified by an [ISO 639] code). The framework imposes
  neither a minimum set nor completeness; the set of languages is edited by the
  governance owner to suit their need.
- **No machine translation (verbatim invariant, §3 restated).** Each language
  version is verbatim from *its own* language source. The framework never generates
  a translation and never paraphrases one language from another.
- **The owner verifies the linguistic equivalence (Meaningful Human Control).**
  Whether a language version faithfully expresses *the same* requirement is judged by
  the governance owner, not by the framework and not by any tool. A shared ID is the
  framework’s *claim* of sameness; confirming that claim is the owner’s editorial act.

### 8.2 Carrying language: NIST mechanism

NIST OSCAL (the pinned [1.2.3] JSON model, `schemas/nist/manifest.json`) does **not**
expose an XML-style `@lang` attribute in its JSON schema. Language is therefore
carried, NIST-conformantly, through a **`prop` named `language`** whose value is an
[ISO 639] code (§4.1). This is the single mechanism both patterns below build on.

**Why a `prop`, not `@lang` (format-portability).** The leading format is YAML;
the other serializations are produced from it with standard OSCAL tooling. Choosing
`prop[name="language"]` keeps the language carrier identical across YAML, JSON, and
XML, because `prop` exists in all three OSCAL serializations. An XML-only `@lang`
attribute would not survive a conversion to the JSON/YAML model. The patterns here
were round-tripped YAML↔JSON with the official OSCAL toolset
([compliance-trestle]) with no loss, and the `language` props are preserved. XML
output, when needed, is produced from the JSON model with NIST’s own
XML/JSON converter. OSCAL4Rail neither forks that path nor invents its own.

### 8.3 Two conformant patterns (choose per catalog)

Because the invariant lives in the ID, not in the file layout, two NIST-native
shapes satisfy it. Neither is excluded; the framework stays as close to the NIST
model as possible and leaves the choice to the owner.

| | **Pattern A: one file per language** | **Pattern B: one file, per-language parts** |
|---|---|---|
| When it fits | sources published separately per language | a single source that is itself multilingual (parallel columns) |
| Language carried by | `metadata/props[name="language"]` on each file | `props[name="language"]` on each language-specific `part` |
| Sameness carried by | identical control ID across the sibling files | one control ID, repeated language-tagged parts under it |
| Cross-reference | `metadata/links` between the sibling files (§8.4) | not needed, the parts live under one control |
| Equivalence of IDs | implicit (same ID) + optional mapping for edge cases (§8.5) | implicit (one ID) |

Both are valid NIST OSCAL and both validate against the pinned catalog schema. A
catalog MUST pick one pattern and apply it consistently; mixing A and B inside one
regulation is a finding.

**Pattern A, directory and file convention:**

```
catalogs/<regulation>/<lang>/<regulation>-<lang>.yaml
```

Each language file declares its own `metadata/props[name="language"]` and a
`source-document` pointing at that language’s source. The same control ID
(`<regulation>-<chapter.section>`) denotes the same requirement in every sibling
file. This is what makes the files linkable.

**Pattern B, language-tagged parts.** The control carries one `statement` part per
language, each tagged with its own `language` prop. `part` has a `props` array in
the NIST model, so this needs no extension. (NIST’s JSON schema has no `part/@lang`;
the `language` prop is the conformant carrier.)

A worked, synthetic example of both patterns and the edge-case mapping lives in
[`examples/multilingual/`](../../examples/multilingual/README.md). It uses an
invented placeholder regulation, not a real one (Framework ≠ Content, ADR-007).

### 8.4 Cross-reference between language files (Pattern A)

Sibling language files reference each other through NIST `metadata/links`. The
`link` assembly provides `href`, `rel`, `media-type`, and `text`.

- `rel` is an open `TokenDatatype` in NIST (its only predefined example value is
  `reference`). OSCAL4Rail uses the conventional value **`alternate`** to mean “an
  alternate language version of the same catalog”. This is an OSCAL4Rail convention,
  not a NIST-defined relationship value; it is declared here so a validator can
  recognize it.
- `text` SHOULD name the target language (e.g. the ISO 639 code) so the link is
  self-describing.

```yaml
  metadata:
    props:
    - name: language
      value: fr
    links:
    - rel: alternate
      href: ../de/example-de.yaml
      text: de
```

### 8.5 Edge case: divergent chapter numbering

The normal case needs no mapping: the same chapter-based ID *is* the equivalence.
But if a language version numbers its chapters differently (so the chapter-based IDs
cannot match), the equivalence is made explicit with a NIST **Control Mapping**
(`schemas/nist/oscal-mapping.json`), not a bespoke construct:

- a `map` entry whose `sources` and `targets` are `mapping-item`s of `type: control`
  (the NIST-defined subject types are `control` and `statement`),
- carrying `relationship` (an open token; OSCAL4Rail uses **`equivalent`**) together
  with the schema-required `matching-rationale`.

This reuses exactly the mechanism the Regulatory Cascade uses at framework
boundaries ([cascade-as-profiles]); here both sides are the *same* regulation in two
languages.

### 8.6 Consistency (what a check would assert)

Stated so the model is testable; the automated check itself is tracked for a later
milestone, not built here:

- **Pattern A:** a control ID present in one language file SHOULD be present in all
  sibling files of the same regulation and version; an unmatched ID is a finding
  (unless an §8.5 mapping explicitly bridges it).
- **Pattern B:** every control SHOULD carry the same set of `language` props its
  siblings carry; a missing language is a finding.
- Either way, the check only reports *structural* divergence. It never asserts that
  two language texts *mean* the same thing; that remains the owner’s editorial
  judgment (§8.1, Meaningful Human Control).

[ISO 639]: https://www.iso.org/iso-639-language-code
[1.2.3]: https://github.com/usnistgov/OSCAL/releases/tag/v1.2.3
[cascade-as-profiles]: cascade-as-profiles.md
[compliance-trestle]: https://github.com/oscal-compass/compliance-trestle

---

## 9. Known inconsistencies (to be resolved, not silently fixed)

Honest status, so the spec does not overstate precision:

1. **OSCAL version.** `catalogs/bs-ki/de/bs-ki-de.yaml` declares
   `oscal-version: 1.1.3`, while the pinned base (`schemas/nist/manifest.json`,
   ADR-008) targets a 1.2.x release. `schemas/README.md` already records this drift.
   The catalog’s `oscal-version` must be aligned to the pinned base; tracked
   separately, not changed by this document.
2. **Obligation vocabulary** is observed, not yet declared. §6.1/§6.3 define *where*
   it will be declared; the enforcing schema is [#3].
3. **Context vocabulary** is likewise observed from BS-KI. A second catalog (e.g.
   TSI Telematics) is needed to confirm the model generalizes.

---

## 10. Acceptance checklist (traceability to #2)

| #2 acceptance criterion | Section |
|---|---|
| ID scheme `<regulation>-<chapter.section>[-<context>]`, chapter-based, never page-based | §2 |
| Applicability model documented (context × obligation) | §6 |
| Multilingual model (same rule across languages; patterns A/B; cross-link and equivalence mapping) | §8 |
| Mandatory props beyond NIST (`source-chapter`, `source-document`) | §4 |
| Verbatim quoting documented as a hard invariant | §3 |

---

[ADR-007]: ../adr/ADR-007-tooling-foundation.md
[ADR-008]: ../adr/ADR-008-reproducible-schema-acquisition.md
[#3]: https://github.com/OpenRailAssociation/oscal4rail/issues/3

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
