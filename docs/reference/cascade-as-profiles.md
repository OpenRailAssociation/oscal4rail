<!--
SPDX-FileCopyrightText: 2026 DB Systel GmbH
SPDX-License-Identifier: Apache-2.0
-->

# Regulatory Cascade as an OSCAL Profile Chain

**Status:** Draft · **Layer:** 1 (Catalog) + Cascade · **Base:** NIST OSCAL Profile and Mapping models
**Issue:** [#4](https://github.com/OpenRailAssociation/oscal4rail/issues/4)

This is a **reference specification** of how OSCAL4Rail expresses the **Regulatory
Cascade**, the railway-specific USP, without inventing a bespoke cascade schema.
Each cascade level is a NIST OSCAL **Profile** that selects and specializes controls
from an upstream **Catalog**; relationships across frameworks or languages are NIST
**Control Mappings**. We reuse the standard, and OSCAL4Rail only adds a thin layer of
extension props to label the chain.

> **Framework ≠ Content** ([ADR-007](../adr/ADR-007-tooling-foundation.md)). This
> document specifies the *shape* of a cascade. A profile **selects** upstream controls;
> it never authors regulatory text. On resolution, the statement text comes 1:1 from the
> upstream catalog, so the verbatim invariant ([catalog-format.md §3](./catalog-format.md))
> is preserved end to end.

The mechanism below is **demonstrated with a working example**, not invented: a company
profile over the German BSI *Stand-der-Technik-Bibliothek* Grundschutz++ catalog, pinned
and fetched reproducibly, plus a cross-framework mapping to ISO/IEC 27001:2022.

---

## 1. The cascade (source: arc42 §1)

The defining railway-specific innovation is the regulatory cascade with conformance
constraints and impact propagation across 5–6 hierarchy levels
([docs/arc42.md](../arc42.md) §1), quoted verbatim:

```
International   ISO, EN standards (e.g. ISO 27001, EN 50126)   ← ISO, CEN/CENELEC
                    │ referenced by
EU              TSI, EU Directives (e.g. EU 2026/253)          ← ERA, EU Commission
                    │ specializes (must not contradict)
National        e.g. EBO, AEG (DE) / LEisenbG (CH)            ← EBA / BAV
                    │ concretizes
Agency          e.g. EBA-Verfügungen, BAV-Rundschreiben        ← Federal agency
                    │ adapts
Industry        e.g. BS-KI (CH), Ril 420 (DE), DIN norms      ← Industry bodies, DIN
                    │ implements
Company         e.g. Internal standards, guidelines            ← CIO, EA
                    │ operationalizes
System/Team     e.g. Architecture decisions, ADRs              ← Dev teams
```

Key properties (verbatim, arc42 §1):

- **Conformance flows downward**: each level may only specialize, never contradict its parent
- **Changes cascade**: when a TSI changes → national law adapts → industry standard adapts → company guidelines adapt → systems must update
- **Impact propagates**: "TSI 4.2.1 changed" → which national rules affected? → which company standards? → which IT systems?

The verbs on the arrows (*specializes, concretizes, adapts, implements, operationalizes*)
are the controlled vocabulary of the `conformance-constraint` prop (§4).

---

## 2. The modeling decision: profile chain, not custom schema

> **Cascade model: OSCAL Profile chain (not custom schema).** *Each cascade level = one
> Profile selecting from upstream Catalog* ([arc42 §4.1](../arc42.md), verbatim).

| Cascade concept | NIST OSCAL mechanism |
|---|---|
| A level selecting from the level above | `profile` with `imports[].include-controls` |
| The upstream the level specializes | `import/@href` → parent catalog (or parent profile's resolved catalog) |
| Conformance "may only specialize" | declarative `conformance-constraint` prop (enforced by validator / Layer 3) |
| Cross-framework / cross-language link | `mapping-collection` (`relationship` + `sources`/`targets`) |
| Resolving a level to a usable catalog | NIST **profile resolution** → resolved catalog |

A profile **composes** one or more upstream catalogs and selects a subset of their
controls. Resolving the profile yields a normal catalog whose control text is the
upstream text, unchanged. A chain is simply a profile whose upstream is itself the
resolved output of the level above.

OSCAL4Rail adds **nothing structural**. The only additions are three props under the
OSCAL4Rail namespace (`…/ns`), the NIST-sanctioned extension point
([catalog-format.md §5](./catalog-format.md)), so every cascade profile stays valid NIST
OSCAL.

---

## 3. Worked example (the chain in this repository)

The example models the lower end of the cascade with **real, authoritative upstream
content**:

```
International   ISO/IEC 27001:2022 Annex A
                    │  mapping-collection (relationship: equivalent-to / subset-of)
Industry/Nat.   BSI Grundschutz++ (Kernel + Methodik → profile → resolved catalog)   ← © BSI, CC-BY-SA-4.0
                    │  import + include-controls   (conformance-constraint: specializes)
Company         examples/profiles/company-over-bsi-grundschutz.profile.yaml          ← this repo, Apache-2.0
```

| Artifact | File |
|---|---|
| Company-level profile (selects a GS++ subset) | [`examples/profiles/company-over-bsi-grundschutz.profile.yaml`](../../examples/profiles/company-over-bsi-grundschutz.profile.yaml) |
| Cross-framework mapping (company subset ↔ ISO 27001) | [`examples/mappings/company-subset-to-iso27001.mapping.yaml`](../../examples/mappings/company-subset-to-iso27001.mapping.yaml) |
| Pinned upstream manifest (BSI) | [`examples/upstream/bsi/manifest.json`](../../examples/upstream/bsi/manifest.json) |
| Reproducible fetch tool | [`tools/fetch_bsi_example.py`](../../tools/fetch_bsi_example.py) |

### 3.1 The upstream is referenced, never vendored

The BSI *Stand-der-Technik-Bibliothek* is licensed **CC-BY-SA-4.0**; this repository is
**Apache-2.0**. To avoid mixing licenses, OSCAL4Rail **does not copy** the BSI catalog
into the repository. It is fetched from a **pinned commit** and verified by SHA256. This is the
same reproducible-acquisition policy used for the NIST base schemas
([ADR-008](../adr/ADR-008-reproducible-schema-acquisition.md)). The BSI repository
publishes no release tags, so the pin is a **commit SHA** instead of a tag; the policy is
otherwise identical.

```bash
python3 tools/fetch_bsi_example.py              # fetch + SHA256-verify into _fetched/ (git-ignored)
python3 tools/fetch_bsi_example.py --verify-only  # offline verification (CI)
```

Source: BSI *Stand-der-Technik-Bibliothek*,
<https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek> (CC-BY-SA-4.0).

---

## 4. Railway extension props (defined here)

Carried on `profile/metadata/props`, under `ns =
https://github.com/OpenRailAssociation/oscal4rail/ns`. Enforced by
[`schemas/oscal4rail/oscal4rail-profile-cascade-constraints.schema.json`](../../schemas/oscal4rail/oscal4rail-profile-cascade-constraints.schema.json).

| prop `name` | Required | Meaning | Vocabulary |
|---|---|---|---|
| `cascade-level` | yes | Which level of the cascade this profile represents | `international`, `eu`, `national`, `agency`, `industry`, `company`, `system` |
| `parent-catalog-ref` | yes | Stable reference to the upstream (parent) catalog this level specializes | manifest key / URI / pinned reference (non-empty) |
| `conformance-constraint` | recommended | Type of conformance relationship to the parent | `specializes`, `concretizes`, `adapts`, `implements`, `operationalizes`, `references` |

**Verbatim example** (from the company profile):

```yaml
props:
- name: cascade-level
  ns: https://github.com/OpenRailAssociation/oscal4rail/ns
  value: company
- name: parent-catalog-ref
  ns: https://github.com/OpenRailAssociation/oscal4rail/ns
  value: bsi:grundschutz-plusplus-resolved-catalog
- name: conformance-constraint
  ns: https://github.com/OpenRailAssociation/oscal4rail/ns
  value: specializes
```

**Invariant (declarative, not enforced here).** `conformance-constraint` *labels* the
relationship; it asserts "conformance flows downward" but does not by itself verify it.
Verifying that a child never contradicts its parent is the job of the validator
([#5](https://github.com/OpenRailAssociation/oscal4rail/issues/5)) and the Change Impact
layer. Modeling it in #4 only establishes the vocabulary and the carrying mechanism.

---

## 5. Selection only: the verbatim boundary

A cascade profile expresses specialization through **selection** (`include-controls` /
`exclude-controls`), not through rewriting. In the example, the company level selects
five real Grundschutz++ controls by their verbatim IDs:

```yaml
imports:
- href: ../upstream/bsi/_fetched/grundschutz-plusplus-resolved-catalog.json
  include-controls:
  - with-ids:
    - GC.1.1   # Errichtung und Aufrechterhaltung eines ISMS
    - GC.1.2   # Freigabe des ISMS
    - GC.5.1   # Festlegung von Zielen für die Informationssicherheit
    - GC.6.1   # Festlegung des Geltungsbereichs
    - GC.7.1   # Vorgehen bei der Informationssicherheitseinstufung
```

**Where company-specific *content* goes.** A level that adds its *own* concretizing
requirement text (NIST `modify/add`) is authoring content. That is **owner work** and
belongs to the adopting organization's own repository, not to this framework example
(ADR-007; [catalog-format.md §5](./catalog-format.md), the org block). The framework
specifies the *mechanism*; it must not invent an owner's text.

---

## 6. Cross-framework mapping (the international boundary)

The cascade's top boundary (industry/national ↔ international standard) is a NIST
**Control Mapping**, not a bespoke link. The example maps the company subset to ISO/IEC
27001:2022 Annex A:

```yaml
maps:
- relationship: equivalent-to
  sources: [{ type: control, id-ref: GC.1.1 }]
  targets: [{ type: control, id-ref: 'A.5.1' }]
- relationship: subset-of
  sources: [{ type: control, id-ref: GC.5.1 }]
  targets: [{ type: control, id-ref: 'A.5.1' }, { type: control, id-ref: 'A.5.4' }]
```

`relationship` uses the NIST mapping vocabulary (`equivalent-to`, `subset-of`, …). The
map entries assert relationships **between identifiers**. They carry no requirement text
from either framework.

> **Illustrative vs. authoritative.** The example mapping is non-normative: it shows the
> *shape*. The **authoritative** ISO↔GS++ crosswalk is published by the BSI itself
> (`control_layer/Mappings/ISO-27001-zu-GSpp/`, fetched via `tools/fetch_bsi_example.py`)
> and uses exactly this NIST model, which confirms the mechanism generalizes beyond
> OSCAL4Rail's own authorship.

**Multilingual as a special case.** The same model links *the same requirement across
languages* (DE ↔ FR), using stable IDs across language files
([catalog-format.md §8](./catalog-format.md)). Anchoring the multilingual model is the
subject of [#7](https://github.com/OpenRailAssociation/oscal4rail/issues/7); #4 fixes only
the cross-framework shape that #7 reuses.

---

## 7. Validation (how "resolves correctly" is checked)

Two passes, mirroring the catalog approach:

1. **NIST base schema.** The profile is a valid NIST OSCAL Profile and the mapping a
   valid NIST Mapping Collection:
   ```bash
   python3 tools/validate.py examples/profiles/company-over-bsi-grundschutz.profile.yaml
   python3 tools/validate.py examples/mappings/company-subset-to-iso27001.mapping.yaml
   ```
2. **OSCAL4Rail cascade constraints.** The extension props (`cascade-level`,
   `parent-catalog-ref`, `conformance-constraint`) are checked against
   `schemas/oscal4rail/oscal4rail-profile-cascade-constraints.schema.json`.

**Resolution check.** Every control ID selected by the profile (and every mapping source
ID) must exist in the pinned upstream catalog. This is what "the profile resolves
correctly" (AC2) means operationally: selection against a known, pinned parent, with no
dangling IDs. The check runs against the fetched upstream after
`tools/fetch_bsi_example.py`.

---

## 8. Known inconsistencies (honest status)

1. **OSCAL version drift.** The BSI Grundschutz++ profile/catalog declare
   `oscal-version: 1.1.3`; the OSCAL4Rail-pinned NIST base is 1.2.3
   (`schemas/nist/manifest.json`). The example profile mirrors the upstream's 1.1.3 for
   consistency with its parent; the mapping uses 1.2.3. Full profile *resolution* across
   the version gap is tracked with the validator work
   ([#5](https://github.com/OpenRailAssociation/oscal4rail/issues/5)), not resolved here.
2. **`conformance-constraint` is declarative only.** Enforcement (child must not
   contradict parent) is Layer 3 / validator scope, not #4.
3. **One upstream, one framework pair.** The chain is shown for BSI Grundschutz++ ↔ ISO
   27001. A second, independent cascade (e.g. a TSI branch) is needed to confirm the model
   generalizes across jurisdictions.

---

## 9. Acceptance checklist (traceability to #4)

| #4 acceptance criterion | Section / artifact |
|---|---|
| `docs/reference/cascade-as-profiles.md`: cascade = profile chain | this document, §1–§2 |
| Example `examples/profiles/` selecting a subset from an upstream catalog resolves correctly | §3, §5, §7 + `company-over-bsi-grundschutz.profile.yaml` |
| Railway extension props defined: `cascade-level`, `conformance-constraint`, `parent-catalog-ref` | §4 + cascade constraints schema |
| Control Mapping example (multilingual and/or cross-framework) | §6 + `company-subset-to-iso27001.mapping.yaml` |

---

[ADR-006]: ../adr/ADR-006-oscal4rail-vs-rulemapping.md
[ADR-007]: ../adr/ADR-007-tooling-foundation.md
[ADR-008]: ../adr/ADR-008-reproducible-schema-acquisition.md

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
