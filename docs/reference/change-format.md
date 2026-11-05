# Change Impact Layer (Layer 3) — reference

> Normative reference for the OSCAL4Rail Change Impact Layer. Decision:
> [ADR-019](../adr/ADR-019-change-layer-vcs-native.md) (VCS-native interpretation, Git
> core, framework defines the interface and documents the method, it does not build the
> consuming engine). Reuses [ADR-014](../adr/ADR-014-rules-layer-placement.md) (version
> coupling via `metadata.version`) and [ADR-018](../adr/ADR-018-rules-format-oscal-native.md)
> (L2 modality semantics) and the cascade relations of
> [cascade-as-profiles](./cascade-as-profiles.md). Schema:
> `schemas/oscal4rail/oscal4rail-change.schema.json`.

## 1. What Layer 3 answers

Given two versions of a governance artifact, Layer 3 answers, at control level and beyond
a prose changelog:

1. **What** changed (which controls / rules were added, removed, or altered)?
2. **How severe** is each change (tightened, relaxed, inverted, deprecated, superseded, withdrawn, content-changed)?
3. **Who** is affected (which applicability contexts, which downstream cascade levels)?
4. **What action** does the change require of the affected owner?

L3 is the **semantic interpretation of a version control change**. It is not a file-diff
engine and not a second source of truth (ADR-019 D1).

## 2. The VCS is the change machine (ADR-019 D1, D2)

Governance-as-Code keeps the artifact in a version control system. The VCS already
provides, natively and authoritatively:

| The VCS (Git) provides | L3 does not re-build it |
|---|---|
| `git diff base..head`, `git log` — what changed, commit-exact | the line diff |
| authorship, sign-off, DCO — who, with which approval | the approval record |
| the Merge/Pull Request — the governed change process itself | the review process |
| tags / `metadata.version` — which state is which version | version storage |

L3 **consumes** a VCS change (a ref range `base..head`) and adds only the governance
semantics the VCS cannot express (section 4).

### 2.1 Git core, not a forge platform

The change source is **Git refs**, never a forge-specific API. The same method runs on
GitHub, GitLab, Codeberg, Gitea, Forgejo, Radicle and plain local Git (Pareto: the Git
core covers the ecosystem with one path). A forge platform (its CI, its MR/PR comment API)
is an **optional, exchangeable adapter** on top, not part of the layer. A **file fallback**
(`--from <file> --to <file>`) covers the VCS-less case. Non-Git VCS (e.g. SVN) are out of
scope; the file fallback absorbs them.

## 3. Relationship to `git diff` and the MR process

`git diff` and L3 are complementary, not redundant:

- `git diff` answers *which bytes changed*. It sees `recommended` → `binding` as a text
  change.
- L3 answers *what that change means for the obligation and for downstream owners*. It
  sees the same edit as an obligation **tightening** and routes the impact.

L3 is therefore best run **where the change is already governed**: as a check in the Merge
Request (CI), producing a report the reviewer reads alongside the diff. Git stays the
single source of truth; the L3 report is a derived, non-stored interpretation.

## 4. The change model

### 4.1 Change categories (per control)

A control-level change falls into exactly one category (MECE). The categories group into
three disjoint dimensions: **existence**, **lifecycle**, and **strength**.

| Dimension | Category | How it is expressed | Meaning |
|---|---|---|---|
| existence | `added` | `target-gap-summary` | a control exists in the new version, not in the old |
| existence | `removed` | `source-gap-summary` | a control exists in the old version, not in the new (hard delete) |
| lifecycle | `deprecated` | `map/@relationship` | the rule moved to `deprecated`: still in force for existing (legacy) systems, not to be used for new ones |
| lifecycle | `superseded` | `map/@relationship` | the rule was replaced by another rule (carries `superseded-by`) |
| lifecycle | `withdrawn` | `map/@relationship` | the rule was retired without replacement |
| strength | `tightened` | `map/@relationship` | the obligation became stronger (see 4.2) |
| strength | `relaxed` | `map/@relationship` | the obligation became weaker (see 4.2) |
| strength | `inverted` | `map/@relationship` | the obligation polarity flipped, `required` ↔ `forbidden` (see 4.2) |
| (fallback) | `content-changed` | `map/@relationship` | the statement or metadata changed, strength not derivable |

**Existence changes are NIST gaps, not relationships.** A NIST `map` requires both
`sources` and `targets` (each `minItems: 1`), so a one-sided change cannot be a map.
`added` (target only) is listed in the mapping's `target-gap-summary`, `removed` (source
only) in its `source-gap-summary`. This keeps the report a valid OSCAL mapping and
upgradeable on the NIST schema. The two-sided changes (lifecycle, strength, content) are
`map` entries whose category rides on `map/@relationship` (O4R namespace).

**Precedence when more than one applies.** A single edit can touch more than one
dimension (e.g. a rule is both `deprecated` and `relaxed`). The classification reports the
**governance-primary** category in this order: **lifecycle > strength > existence-content**.
A lifecycle change is the more governance-relevant statement, so `deprecated` /
`superseded` / `withdrawn` win over `tightened` / `relaxed` / `inverted`. The subordinate
observations may be listed as secondary notes on the same change.

> `removed` vs. `withdrawn` / `deprecated`: `removed` is a hard deletion from the document
> (the rule is simply gone). `withdrawn` and `deprecated` are **lifecycle states the rule
> still carries** (ADR-018 status axis): the rule is present but retired or legacy-only.
> Prefer the lifecycle state over a hard delete, so downstream owners keep an auditable
> trace.

### 4.2 Deriving `tightened` / `relaxed` / `inverted` from L2 semantics (ADR-019 D3)

`tightened` / `relaxed` / `inverted` is a **semantic** statement, derived deterministically
from the L2 signal (ADR-018 modality: `binding` / `rank` / `polarity`), never from the
prose:

| Observation on the matched rule | Classification |
|---|---|
| `modality.rank` **decreases** (lower rank = stronger, e.g. recommended → binding) | `tightened` |
| `modality.rank` **increases** (e.g. binding → recommended) | `relaxed` |
| `modality.polarity` **flips** (`required` ↔ `forbidden`) | `inverted` |
| `applicability` covers **more** contexts | `tightened` |
| `applicability` covers **fewer** contexts | `relaxed` |

### 4.3 Deriving `deprecated` / `superseded` / `withdrawn` from the L2 lifecycle axis

The L2 status carries a fixed `lifecycle` axis (ADR-018 status:
`draft` / `active` / `deprecated` / `superseded` / `withdrawn`). A transition on that axis
is classified directly:

| Transition of `status.lifecycle` | Classification |
|---|---|
| `active` → `deprecated` | `deprecated` (legacy-only: still binding for existing systems, not for new) |
| `* ` → `superseded` (with `superseded-by: <rule-id>`) | `superseded` |
| `* ` → `withdrawn` | `withdrawn` |
| `draft` → `active` | treated as `added` into force (a new in-force obligation) |

A `deprecated` rule typically also carries an `applies-when` restricting it to legacy
scope; L3 reports that restriction as part of the impact (who is still bound).

**Honest degradation.** If a catalog has **no L2** (L1 statements only), neither strength
(4.2) nor lifecycle (4.3) is derivable. The change is then reported as `added` /
`removed` / `content-changed`, never guessed (First Principles honesty; Goodhart
protection: no fake precision).

### 4.4 Detection procedure (how the reference CLI determines a change)

The method is deterministic and is what `tools/change` implements. For two states
(`source` = old, `target` = new), each identified by a Git ref or a file:

1. **Match by stable identity, and detect existence by set difference.** Build the set of
   `control-id`s present in source and in target. The `control-id` is the identity across
   versions (never the position or the prose). Compare the two sets first:
   - a `control-id` **present in target but not in source** is a **new control** → `added`;
   - a `control-id` **present in source but not in target** is a removed control → `removed`.
   This set comparison is how a newly added (or removed) control is discovered at all; it
   happens **before** any field comparison (a new control has no old state to diff against).
   An `added` control is written to the mapping's `target-gap-summary`, a `removed` control
   to its `source-gap-summary` (NIST-native; a map cannot be one-sided). Then iterate the
   **union** of both sets, sorted, so output is reproducible, for the two-sided changes.
2. **Per control-id, determine the changed field, then classify** in this precedence
   (lifecycle > strength > existence/content), taking the first that applies:
   - **existence**: in target only → `added`; in source only → `removed`
     (changed field: `control-existence`).
   - **lifecycle** (needs L2): `status.lifecycle` differs → `deprecated` / `superseded` /
     `withdrawn` (changed field: `status.lifecycle`).
   - **strength** (needs L2): `modality.polarity` flips → `inverted`
     (field `modality.polarity`); else `modality.rank` differs → `tightened` (rank
     decreased) / `relaxed` (rank increased) (field `modality.rank`).
   - **content**: the verbatim L1 `statement` differs → `content-changed`
     (field `statement`).
   - otherwise: no change, emit nothing for this control-id.
3. **Record what changed, not the content.** Each emitted `map` carries a `changed-field`
   prop naming the field that changed (`control-existence` / `status.lifecycle` /
   `modality.polarity` / `modality.rank` / `statement`) and the old/new values of the
   decisive axis (e.g. `old-rank` / `new-rank`). The report says **which control and which
   field** changed and **how** it is classified; it does **not** reproduce the rule's
   content text (that lives verbatim in the catalog, the single source of truth).
4. **Degrade honestly without L2.** If no rule-set is supplied, steps for lifecycle and
   strength are skipped; only existence and `statement` content changes are reported.

The procedure reads only the declared L2 semantics axis (`rank` / `polarity` /
`lifecycle`), never the owner's wording, so the same inputs always yield the same
classification (deterministic, auditable).

## 5. The impact model (as a description, not a built engine)

For each classified change, L3 describes an impact chain:

```
change  ──►  affected contexts        ──►  affected cascade levels      ──►  required action
(4.1/4.2)    (applicability class)         (specializes / concretizes /      (owner-facing,
                                            adapts / implements /             described, not decided)
                                            operationalizes / references)
```

- **Affected contexts**: the applicability classes the changed control applies to (which
  deployments / scopes are touched).
- **Affected cascade levels**: the downstream levels that stand in a conformance relation
  to the changed catalog. The relations are the verbatim cascade verbs
  (`specializes`, `concretizes`, `adapts`, `implements`, `operationalizes`, `references`);
  a change upstream propagates to the levels that specialize it.
- **Required action**: what the affected owner must consider (e.g. "re-verify downstream
  controls that specialize this one"). L3 **describes** the required action in the report;
  it does **not** decide or perform it.

The framework specifies the **shape** of this chain (the schema, section 7) and the
**method** to populate it. Computing it against real systems, and acting on it, is
consumption (section 6).

## 6. Interface and boundary (ADR-019 D4, D6)

L3 is a framework **interface + method**, not a consuming engine:

- The framework provides: the change model (this document), the **schema** (the machine
  contract for a change report, section 7), the **method** to classify and to describe
  impact, and a **reference CLI** that applies the method and self-validates the schema
  (section 7).
- The framework does **not** provide: an engine that checks impact against real systems,
  interprets the change agentically, takes the governance decision, or triggers follow-up
  activities. That is consumption, built by the consumer (a consuming agent or an owner automaton)
  under its own policy.

**Autonomy boundary.** Where the line between autonomous action and human decision sits is
set by the **using organisation**, which specifies the guardrails and capabilities its
agents operate within. Autonomous agents are legitimate: a human having specified the
guardrails and capabilities **is** the Meaningful Human Control, not a human executing
every action. The L3 report (deterministic, auditable: classification + impact + required
action) is the information on which such a policy is built. The framework defines this
boundary as an interface; it neither sets nor enforces it.

## 7. The report is an OSCAL artifact; validation and the reference CLI

The change report **is** an OSCAL artifact under the OSCAL4Rail schema (ADR-019 D7): a NIST
OSCAL `mapping-collection` that maps a source catalog version to a target catalog version.
It is not a free format. The same artifact is both the human-readable report and the
agent-readable diff, and it is what L4 re-assessment consumes.

- **Form**: a `mapping-collection` with `source-resource` (old) and `target-resource`
  (new), each carrying its catalog version (ADR-014 coupling). Each **two-sided**
  control-level change is one `map`; the change **category** rides on the native
  `map/@relationship`, qualified by the OSCAL4Rail change namespace, with values from
  section 4.1. The old/new signal snapshot, `superseded-by`, and the impact chain
  (section 5) ride on O4R `props`. **One-sided existence changes** (`added` / `removed`)
  are not maps: they go in the mapping's `target-gap-summary` / `source-gap-summary`
  (NIST-native, since a map requires both sides).
- **Schema**: `schemas/oscal4rail/oscal4rail-change.schema.json` (Draft 7), **additive
  over the NIST Mapping Model** (no fork). Validation is two-pass: NIST pass against
  `oscal-mapping.json` plus the O4R pass against this schema. A report is therefore valid
  OSCAL **and** a valid OSCAL4Rail change report.
- **Reference CLI** `tools/change`: takes two states (Git refs or `--from` / `--to`
  files), applies the classification method (section 4), and emits the OSCAL mapping that
  validates in both passes. It **interprets** (classifies and describes impact) and
  **self-validates** the format. It does **not act**: no notification, no downstream write,
  no agent trigger. It is the executable reference (MVP) of this specification, the L3
  counterpart to `tools/validate.py`, not a productive service.

**What validation does and does not mean.** Validation is layered and none of its layers
judges whether the rules are consistent or correct. NIST OSCAL tools check only that the
serialization is well-formed, schema-valid OSCAL. The OSCAL4Rail pass adds framework
conformance (declared vocabularies, control-id integrity, version coupling, the change
namespace). Neither says whether the catalog, controls and rules are consistent,
non-contradictory or correct. A statement about consistency and satisfaction is produced
by the **Assessment layer (L4)**, and intent remains the owner's to verify (Meaningful
Human Control). A green result means **well-formed OSCAL that conforms to the OSCAL4Rail
schema**, not that the content is correct (Goodhart protection); that is why the framework
relies on verbatim capture, round-trip verification and owner sign-off.

```
tools/change <base-ref> <head-ref>                  # OSCAL mapping to stdout
tools/change --from catalog@v1 --to catalog@v2 -o change.yaml
tools/change <base-ref> <head-ref> --summary        # human-readable summary
```

## 8. Summary

L3 reuses the VCS for *what changed* and L2 for *how binding*, and adds only the
governance-semantic delta: classification, impact, required action. Git is the source of
truth; the forge is an exchangeable adapter; the consumer and its organisation own the
decision and the action. The framework ships the model, the schema, the method and a
self-validating reference CLI, nothing that decides or acts.
