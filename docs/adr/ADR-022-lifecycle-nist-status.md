<!--
SPDX-FileCopyrightText: 2026 DB Systel GmbH
SPDX-License-Identifier: Apache-2.0
-->

# ADR-022: Lifecycle: retire controls with the NIST `status` values, never delete them

**Status:** Proposed

**Date:** 2026-11-11

**Deciders:** Jens Grote

## Context

A regulation changes over time. Requirements are replaced, merged into others, phased out
or dropped. The framework must say how a catalog expresses that a control is no longer
current, and with which words.

Today there are two gaps.

1. **A control can only be retired through the rules layer.** The lifecycle state lives in
   the rule-set ([ADR-018](./ADR-018-rules-format-oscal-native.md), status axis `draft` /
   `active` / `deprecated` / `superseded` / `withdrawn`). The rules layer is optional. A
   catalog without a rule-set has no way to retire a control; it can only delete it.
2. **A deletion is treated as a normal change.** The change layer reports a deleted control
   as `removed` (`change-format.md` §4.1) while the same section says "Prefer the lifecycle
   state over a hard delete, so downstream owners keep an auditable trace." Reporting the
   deletion handles the symptom. The cause is that the catalog cannot say "retired".

A deleted control also breaks what the framework is built on: the stable, chapter-based
control id ([ADR-003](../arc42.md#adr-003-chapter-number-as-stable-identifier)) is the identity every rule, mapping, profile and
change report refers to. Once the control is gone, those references point at nothing.

### Facts (verified 2026-11-11)

1. **NIST OSCAL defines a status for controls.** In the catalog metaschema of the pinned
   tag v1.2.3 (`src/metaschema/oscal_catalog_metaschema.xml`) a control carries the prop
   `status`. Its documented values, verbatim:
   - `withdrawn`: "The control is no longer used. It may have been retired, incorporated
     into another control, or moved to a different control."
   - `deprecated`: "This control will be withdrawn. The withdrawn timeline or milestone may
     be described in the remarks."
   - `superseded`: "This control has been superseded by the artifact indicated by one or
     more "superseded-by" links or as described in the remarks."
   - `experimental`: "This control is a pilot or proposed control; not yet required."
   - `reserved`: "This is a placeholder for a future control."
   - `conditional`: "This control is only applicable under certain conditions described in
     the remarks."
   - `modified`: "This control has been updated from a prior version, as described in the
     remarks."

   Other values are allowed (`allow-other="yes"`).
2. **NIST defines the link to the successor.** Link relations on a control, verbatim:
   `incorporated-into`: "The link identifies other control content where this control
   content is now addressed."; `moved-to`: "The containing control definition was moved to
   the referenced control."
3. **NIST does not require a statement on a retired control.** The metaschema expects a
   statement unless the status is `withdrawn`, `reserved` or `superseded`.
4. **NIST practises this.** In the SP 800-53 Rev. 5 catalog (version 5.2.0, OSCAL 1.2.3,
   `usnistgov/oscal-content`) 182 of 1196 controls carry `status: withdrawn`. All 182 keep
   their id and title; 166 link `incorporated-into`, 34 `moved-to`. Example: `ac-2.10` links
   `incorporated-into` `#ac-2_smt.k`. No other status value is used in that catalog.
5. **OSCAL has no per-control change model.** Version changes are recorded as prose in
   `metadata.revisions`. This is why the change layer exists
   ([ADR-019](./ADR-019-change-layer-vcs-native.md)).
6. **Three of our five lifecycle words are already the NIST words:** `deprecated`,
   `superseded`, `withdrawn`.

### Forces

- **Upgradeability.** Words that NIST defines keep the catalog readable by NIST tooling and
  spare us maintaining a vocabulary of our own (L1 is a profile over NIST, not a new model).
- **Two layers, two objects.** The control layer (L1) and the rules layer (L2) are
  different things. A control is a catalog entry, the verbatim text of a requirement. A rule
  says how and whether that requirement binds. Both have a lifecycle, and both matter.
- **Framework ≠ Content** ([ADR-007](./ADR-007-tooling-foundation.md), ADR-019 D8). The
  tools validate form and framework conformance, never whether the content is consistent.
- **Verbatim invariant.** The owner must be able to recognise their own text
  (`catalog-format.md` §3).

## Decision

**A control is never deleted. It is retired with the NIST control prop `status`, and
OSCAL4Rail uses the NIST status words on both layers wherever the meaning is the same.**

1. **Control status (L1) uses the NIST prop `status`, unchanged.** A control states its
   lifecycle with `props[name="status"]` in the default OSCAL namespace, with the NIST
   values. A control without the prop is current. This works without a rule-set.

2. **Vocabulary alignment.** The lifecycle words of OSCAL4Rail are the NIST words:

   | Until now (ADR-018) | From now on | Note |
   |---|---|---|
   | `draft` | `experimental` | NIST: "a pilot or proposed control; not yet required" |
   | `active` | `active` (rule status only) | NIST has no word; on a control, no `status` prop means current |
   | `deprecated` | `deprecated` | identical |
   | `superseded` | `superseded` | identical |
   | `withdrawn` | `withdrawn` | identical |

   `reserved`, `conditional` and `modified` are NIST values and therefore valid on a
   control. OSCAL4Rail assigns them no meaning of its own. `modified` is not needed: what
   changed between versions is the change report.

3. **Control status and rule status are two separate lifecycles.** The control status
   says what happened to the catalog entry. The rule status (L2, ADR-018) says whether the
   rule is in force. **Validity is taken from the rules layer, not from the control
   layer.** Where no rule-set exists, the framework makes no statement about validity.
   Neither status is derived from the other.

4. **No cross-layer consistency check.** Whether a control status and a rule status fit
   together (for example an active rule on a withdrawn control) is content. It stays with
   the rule author and the user. The validator does not check it (ADR-019 D8).

5. **The successor of a control is named with NIST links.** `incorporated-into` and
   `moved-to` as defined by NIST; for `superseded`, a link with `rel="superseded-by"`, as
   the NIST description of that status says. The successor of a **rule** stays the
   rule-set field `superseded-by` (ADR-018).

6. **A control id that was published never disappears.** Removing a control from a
   catalog is not a change category. It is an error at publication, found by comparing the
   catalog with its previous published version.

7. **A retired control keeps its verbatim statement.** NIST allows dropping it;
   OSCAL4Rail does not, because the owner and every downstream reader must still find the
   original wording (verbatim invariant). This is stricter than NIST and stays valid OSCAL.

### Scope note (Framework ≠ Content, ADR-007)

This ADR fixes the mechanism: where a lifecycle is stated and with which words. It does not
decide, for any real regulation, which control is retired or which rule is in force. That
is the owner's declaration.

## Alternatives

### Alternative A: Keep `removed` as a change category (status quo)
- (+) No change to the catalog format.
- (−) Treats the symptom. References to the deleted id break; the catalog still cannot
  say "retired" without a rule-set. Rejected.

### Alternative B: Forbid deletion only where a rule-set exists
- (+) No new prop on the control.
- (−) The rule depends on an optional layer; a catalog without rules keeps deleting.
  Rejected.

### Alternative C: An OSCAL4Rail-specific status prop with our own words
- (+) Full control over the vocabulary.
- (−) Duplicates what NIST already defines; NIST tooling would not read it; a second
  vocabulary to maintain. Contradicts "profile over NIST, no fork". Rejected.

### Alternative D: One authoritative lifecycle, on the control only
- (+) One place.
- (−) Collapses two different objects. A requirement can stay in the catalog while the
  rule that binds it changes, and validity is a statement of the rules layer. Rejected.

### Alternative E: NIST `status` on the control, aligned words on both layers, two separate lifecycles (CHOSEN)
- (+) NIST-native on L1, works without L2, ids stay resolvable.
- (+) One vocabulary across the framework, defined by NIST.
- (+) Keeps the layer boundary: validity stays in L2.
- (−) A breaking rename in the rules layer (`draft` → `experimental`).
- (−) Publication needs a comparison with the previous version.

## Consequences

### Positive
- A control can be retired in any catalog, with or without a rule-set.
- Every id that was ever published stays resolvable; rules, mappings, profiles and change
  reports keep pointing at something.
- The lifecycle of a control is readable by tooling that knows NIST OSCAL.
- The change layer loses its only "source side only" case. One-sided changes reduce to
  newly added controls.

### Negative / trade-offs
- **Breaking change in L2:** rule-sets that declare the lifecycle value `draft` must be
  changed to `experimental`.
- **Catalogs grow** and keep retired controls. Readers and renderers must show the status
  so a retired control is not mistaken for a current one.
- **Stricter than NIST** on the statement of a retired control.
- **A new check with a new input:** "no id disappears" needs the previous published
  version. What counts as "published" (a Git tag, a ref) must be defined.
- **Two lifecycles can disagree**, and the framework will deliberately not say so.

### Follow-ups
- #104: implement this ADR (catalog format, rules schema, validator, change layer, tests).
- Amend ADR-018 (lifecycle axis words) and ADR-019 with `change-format.md` (`removed` is no
  longer a change category; control status transitions are detected without a rule-set;
  `changed-field` names the layer) with dated notes when this ADR is accepted.
- #72: with `removed` gone, define the valid report for "only additions" and "no change".
- #73, #74: revise the change categories and the detection accordingly.
- `tools/generate_doc.py`: show the status and the successor of a retired control.

## References

- NIST OSCAL v1.2.3, catalog metaschema, control prop `status` and link relations:
  https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_catalog_metaschema.xml
- NIST SP 800-53 Rev. 5 in OSCAL (withdrawn controls in practice):
  https://github.com/usnistgov/oscal-content/tree/main/nist.gov/SP800-53/rev5
- [ADR-018](./ADR-018-rules-format-oscal-native.md) (rule status axis),
  [ADR-019](./ADR-019-change-layer-vcs-native.md) (change layer; D8: tools never validate
  content), [ADR-007](./ADR-007-tooling-foundation.md) (Framework ≠ Content)
- `docs/reference/catalog-format.md` §2 (ids), §3 (verbatim statement);
  `docs/reference/change-format.md` §4.1
