<!--
SPDX-FileCopyrightText: 2026 DB Systel GmbH
SPDX-License-Identifier: Apache-2.0
-->

# ADR-019: Change Impact Layer (L3): VCS-native interpretation, not a diff engine

**Status:** Accepted (VCS-native L3, Git-core, framework-defines-interface, 2026-11-05)

**Date:** 2026-11-05

**Deciders:** Jens Grote

> **Proposed amendment (2026-11-11, [ADR-022](./ADR-022-lifecycle-nist-status.md); takes
> effect when ADR-022 is accepted).**
> - **`removed` is no longer a change category** (D3, D7). A control is never deleted; it
>   is retired with the NIST control prop `status`. A control id that is missing from the
>   new state is an error at publication, not a change: the reference CLI stops and writes
>   no report. The `source-gap-summary` is therefore not used.
> - **Control status transitions are changes in their own right** and are detected without
>   a rule-set, because the status is stated on the control (L1). Rule status transitions
>   are detected as before, with a rule-set (L2). The `changed-field` prop names the layer
>   that changed.
> - **The lifecycle words are the NIST words:** the transition into force is from
>   `experimental` (formerly `draft`).
> - **No cross-layer check** is added. Whether a control status and a rule status fit
>   together is content and stays outside the tools, as D8 already states.
>
> One-sided changes reduce to newly added controls. How a report stays a valid NIST mapping
> when it contains only additions, or no change at all, is decided separately (#72).

> **Relationship to prior ADRs.** [ADR-007](./ADR-007-tooling-foundation.md) named Change
> Detection as "Layer 3: structured diff between Catalog versions" and listed
> `oscal-deep-diff` (NIST, TypeScript) as a candidate backend. This ADR **refines** that:
> it keeps the goal (structured, machine-readable change notification) but rejects the
> premise that L3 is a *file diff engine*. [ADR-014](./ADR-014-rules-layer-placement.md)
> fixed version coupling via `metadata.version`; L3 reuses it as the change axis.
> [ADR-018](./ADR-018-rules-format-oscal-native.md) fixed the L2 modality semantics
> (`binding`/`rank`/`polarity`) and applicability; L3 reuses that signal to classify a
> change as *tightened* / *relaxed*. [ADR-007 (Framework ≠ Content)](./ADR-007-tooling-foundation.md)
> is the hard boundary this ADR applies to L3: the framework **documents the method and
> defines the interface**, it does **not** build the consuming engine.

## Context

Layer 3 answers: *what changed between two versions of a governance artifact, how severe
is the change, who is affected, and what action does it require?* This goes beyond a
prose changelog.

Governance-as-Code / Law-as-Code assumes the artifact lives in a **version control
system** (Git) and that change itself is already a first-class, governed operation there:

### Facts (established with the owner, 2026-11-05)

1. **The VCS already is the change machine.** `git diff base..head` and `git log` show
   *what* changed, commit-exact and lossless. Merge/Pull Requests are the *established
   governance process* for a change (review, approval, sign-off, DCO). Authorship and
   "who approved which version when" are native VCS facts. A file-based tool that compares
   two catalog **files** someone hands it would **duplicate** what the VCS does natively
   and authoritatively. That is a second source of truth, an SSOT violation.

2. **Git is dominant and the ecosystem is Git (Pareto).** The Governance-/Law-as-Code
   ecosystem is effectively all Git: SPRIND/**openCode** (GitLab CE), **Codeberg**
   (Forgejo), Gitea, **Radicle** (decentralised, still Git-native), GitHub, GitLab,
   OpenRail. Covering the **Git core** covers ~all of them with one decision. Platform
   forges (GitHub/GitLab/Codeberg …) differ only in the *platform layer* (MR/PR API,
   review UI, CI). Radicle has **no** central MR/PR REST API, so binding L3 to a forge
   API would make it non-runnable there, while binding it to **Git refs** runs everywhere.

3. **What Git cannot do is exactly the O4R value.** `git diff` sees `recommended` → `binding` as a text change, not as an **obligation tightening**. Git knows no
   `applicability`, no Regulatory Cascade relations (`specializes`/`concretizes`/…), and
   derives no required action. Those three are only computable with OSCAL4Rail knowledge
   (L1 statements + L2 semantics + Cascade), not from the raw diff.

4. **Consumption is not framework (ADR-007).** Computing impact against real systems,
   interpreting a change agentically, taking the governance decision, and triggering
   follow-up activities are **consumption** of the framework, built by the consumer under
   its own policy (a consuming agent or the owner's own automation). These are
   legitimate and expected. The point is only that the **framework itself** does not build
   them: if it did, it would become a content/decision system, which it must never be
   (ADR-007). Who may do what autonomously is set by the using organisation, not by the
   framework (see D6).

## Decision

L3 is the **VCS-native semantic interpretation of a change**, specified and schema-defined
by the framework, **not** a file-diff engine and **not** a consuming engine.

### D1: L3 sits on top of the VCS; it does not re-implement it

L3 **uses** the existing VCS capabilities (diff, history, authorship, sign-off, the MR/PR
governance process) and builds **only the additive, governance-semantic delta** Git does
not have:

- **Classification** of each control-level change, in three disjoint dimensions:
  existence (`added`, `removed`), lifecycle (`deprecated`, `superseded`, `withdrawn`),
  strength (`tightened`, `relaxed`, `inverted`), with `content-changed` as fallback.
- **Impact model**: change → affected contexts (applicability `class`) → affected cascade
  levels (via the `specializes`/`concretizes`/… relations) → **required action**.

L3 does **not** re-build line diff, history, blame, or the approval process.

### D2: Git core, not a forge platform (Pareto + plattform-neutral)

The change source is **Git refs** (`base..head`), never a forge-specific API. This covers
Codeberg, GitLab, GitHub, Gitea, Forgejo, Radicle and plain local Git with one code path.
Forge platforms are an **optional, thin, exchangeable adapter** (receive webhook, post an
MR/PR comment, run in CI) layered on top (explicitly not the core). A **file fallback**
(`--from <file> --to <file>`) covers the VCS-less and non-Git case. **SVN and other
non-Git VCS are deliberately out of scope** (irrelevant in the target ecosystem,
YAGNI/Occam); the file fallback absorbs them.

### D3: Classification is derived from L2 semantics, honestly degraded without L2

`tightened` / `relaxed` is a **semantic** statement, derived deterministically from the
L2 signal (ADR-018), not from prose:

- `modality.rank` decreases (e.g. recommended → binding) ⇒ **tightened**; increases ⇒
  **relaxed**.
- `modality.polarity` flips (`required` ↔ `forbidden`) ⇒ **replaced** (obligation inverted).
- `applicability` covers **more** contexts ⇒ tightened; **fewer** ⇒ relaxed.

If a catalog has **no L2** (L1 statements only), `tightened`/`relaxed` is **not**
derivable: the change is reported as `added`/`removed`/`content-changed`, never guessed.
(First Principles honesty, Goodhart protection: no fake precision.)

### D4: The framework documents the method and defines the interface; it does not build the consumer

The framework deliverables for L3 are, MECE:

| The framework builds | The framework does NOT build (consumption, the consumer/owner) |
|---|---|
| **Spec / method** (`docs/reference/change-format.md`, #23): change model, how to classify from L2 semantics, the impact model as a **description**, relationship to git diff / MR | no engine that autonomously processes the report |
| **Schema** (`oscal4rail-change.schema.json`, #24): the change report as a machine-readable **interface contract** | no cascade-impact computation against real systems |
| **Interface definition**: input (Git refs / diff) → output (change report per schema) | no agentic interpretation function |
| **Interpretation hints** (how a consumer / agent *may* read the report) | no governance decision, no downstream catalog mutation |

### D5: Reference CLI interprets and self-validates; it does not act

`tools/change` (#25) is a **lightweight reference CLI**: it takes two states (Git refs or
`--from/--to` files), applies the documented classification method (D3), and emits a
change report that validates against the schema (#24). It is the **executable reference of
the specification** and our **self-validation** of the format: the L3 counterpart to
`validate.py`. It **interprets** (classifies) but it does **not act**: no notification, no
downstream write, no agent trigger, no follow-up activity. It is not a productive service
consumed by an agent or other tooling.

### D6: Autonomy boundary set by the using organisation (Meaningful Human Control)

L3 is usable by any consumer: a human at the console, a CI step in an MR, or an autonomous
automaton/agent with Git rights (e.g. on GitLab Premium). **The framework does not fix a
single autonomy boundary.** Where the line between autonomous action and human decision
sits is set by the **using organisation**, which specifies the guardrails and the
capabilities its agents operate within. Autonomous agents are legitimate and desirable:
operating them is how the efficiency gain is realised. That is exactly consistent with
Meaningful Human Control: control means a human has **specified the guardrails and
capabilities** within which an agent may act autonomously, not that a human executes every
individual action.

So an agent may detect a change, classify it, route the impact, and trigger follow-ups
(notify, open a downstream issue/MR, request review), and it may go further where the
organisation has authorised it to, up to and including proposing or applying downstream
changes under the policy the organisation has set. What the framework provides is the
**interface and the information** on which such a policy can be built: a deterministic,
auditable change report (classification, impact, required action) plus the
`L3-declares / consumer-decides` contract, analogous to the `L2-declares / L4-evaluates`
boundary of ADR-018. The framework **defines this boundary as an interface and documents
how it can be parameterised**; it neither sets the boundary for the organisation nor
enforces it in a built engine. Setting and enforcing it is the organisation's governance
responsibility (owner sign-off, policy, guardrail configuration), not the framework's.

### D7: The change report is an OSCAL artifact under the OSCAL4Rail schema (NIST Mapping Model)

The change report is **not** a free report format. It **is** an OSCAL artifact: a NIST
OSCAL `mapping-collection` that maps a **source** catalog version to a **target** catalog
version. OSCAL4Rail supplies the **schema** (additive constraints over the stock NIST
Mapping Model, two-pass like the L1 catalog constraints, no fork), the **tools**, and the
**connections**; the organisation builds its machine-readable governance catalogs on that
basis. Concretely:

- The change **category** rides on the native `map/@relationship`, qualified by an
  OSCAL4Rail change namespace (so a generic NIST relationship is not mistaken for an O4R
  change category). No foreign field is invented (OSCAL-native, no fork, ADR-016/018).
- The compared versions are the mapping's `source-resource` / `target-resource`
  (version coupling, ADR-014); the old/new signal snapshot and the impact chain ride on
  O4R `props`.
- **Existence changes use the NIST gap-summary, not a one-sided map.** A NIST `map`
  requires both `sources` and `targets` (each `minItems: 1`). An `added` control (target
  only) therefore goes in `target-gap-summary`, a `removed` control (source only) in
  `source-gap-summary`. This is the only solution that keeps the report a valid OSCAL
  mapping and **upgradeable on the NIST schema** (no empty-side hack, no fork).
- Validation is two-pass: NIST pass against `oscal-mapping.json` **plus** an O4R pass
  against `oscal4rail-change.schema.json`. A change report is therefore a valid OSCAL
  document **and** a valid OSCAL4Rail change report.

**Why it must be an OSCAL artifact (not merely a convenient choice).** Three reasons, each
sufficient:

1. **Unbroken machine- and agent-readability.** L1 and L2 are OSCAL; if L3 broke out into
   free JSON or prose, machine-readability would break exactly at the change, where it
   matters most. The same OSCAL artifact is both the human-readable report and the
   agent-readable diff: one source, two readings.
2. **Code as the single source of truth (the paradigm).** The framework lives the shift
   from documents-for-documents' sake to machine-readable governance as a living rule
   catalog. The change is itself part of that living catalog (Code = SSOT), from which
   everything else (human view, agent input, MR note) is generated, never the reverse.
3. **The L1 ⊕ L2 → L3 → L4 circle.** "What applies to me" is the resolved L1 ⊕ L2 OSCAL
   result. L3 is the OSCAL mapping between two such results ("what changed for me"), and
   L4 assessment consumes the same OSCAL result ("do I satisfy it"); an L3 change triggers
   L4 re-assessment. Only an OSCAL artifact lets the change apply to the same OSCAL result
   L4 evaluates. A free format would break this fuge.

**Terminology (precise).** The artifact is an **OSCAL artifact**, based on the
**OSCAL4Rail schema** (NIST OSCAL as the standard, OSCAL4Rail as the railway/governance
profile over its layers), as a **Governance-as-Code object, i.e. a rule catalog** (its
functional role for the owner). "OSCAL4Rail" is not a separate file format; it is a schema
over genuine OSCAL. OSCAL4Rail delivers the schema, the tools and the connections so an
organisation builds its own machine-readable governance catalogs and derives the whole
Governance-as-Code context from them (Framework ≠ Content, ADR-007).

### D8: The tools validate form and framework conformance, never content

Validation is layered, and none of its layers judges whether the rules are consistent or
correct:

- **NIST OSCAL tools** check only that the serialization (JSON/YAML/XML) is **well-formed,
  schema-valid OSCAL**. They say nothing about railway conventions and nothing about
  content.
- **OSCAL4Rail `validate.py`** (the second pass, and the L3 reference CLI) additionally
  checks **framework conformance**: declared vocabularies, control-id referential
  integrity, version coupling, the change namespace and categories. It still says nothing
  about whether the catalog, its controls and its rules are **consistent, non-contradictory
  or correct**.
- **Assessment (L4)** is where a statement about consistency and satisfaction is produced,
  and even that is ultimately bound to Meaningful Human Control: only the governance owner
  can verify that the content is what they intend.

So a green validator means **well-formed OSCAL that conforms to the OSCAL4Rail schema**,
nothing more. Whether a change was classified as the owner would judge it, whether the
obligation is right, and whether the rule set is internally consistent are **not**
validation questions. Consistency/satisfaction is the Assessment layer's job; intent is
the owner's (MHC). This separation is deliberate (Goodhart protection: "it validates" must
not be mistaken for "it is correct"), and it is why the framework relies on verbatim
capture, round-trip verification and an explicit owner sign-off, not on a green validator.

## Consequences

### Positive

- **No second source of truth.** Git stays the SSOT and the change source; L3 produces a
  derived interpretation, not a stored second rule set.
- **No platform lock-in, no second runtime.** Git-ref input runs on every forge and on
  Radicle; the Python reference CLI stays consistent with `validate.py` (no TypeScript /
  `oscal-deep-diff` dependency). Minimal, portable, inspectable.
- **Clear Framework ≠ Content line.** The framework ships spec + schema + interface +
  self-validating reference CLI; interpretation, checking against systems, and action stay
  with the consumer.
- **Reuses L2 and Cascade** instead of inventing mechanics: classification from ADR-018
  modality, impact from the cascade relations.

### Negative / trade-offs

- **`tightened`/`relaxed` needs L2.** Catalogs without a rule-set get only coarse
  classification. Accepted: honest over fake-precise.
- **The forge adapter and the acting consumer are out of scope here.** Users who want
  automated MR comments or agent-driven routing must build the adapter themselves against
  the documented interface. Accepted: that is consumption, not framework.
- **Deliberate deviation from the issue wording.** Issues #23–#25 still assume a file-based
  `old.yaml new.yaml` diff tool. This ADR reframes them (VCS-native, interface-first,
  self-validating reference CLI). The issues are refined accordingly, not newly scoped.
- **Non-Git VCS unsupported** except via file fallback. Accepted (Pareto/YAGNI).

### Follow-ups

- #23 Spec `docs/reference/change-format.md` (this ADR is its decision basis).
- #24 Schema `schemas/oscal4rail/oscal4rail-change.schema.json` (the interface contract).
- #25 Reference CLI `tools/change` (self-validation; interprets, does not act).
- Document the consumer-side interface: how a consumer (agent or owner automaton) consumes a
  change report) as an **interface description**, not an implementation.
