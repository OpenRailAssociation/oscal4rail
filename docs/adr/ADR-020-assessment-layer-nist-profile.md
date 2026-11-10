<!--
SPDX-FileCopyrightText: 2026 DB Systel GmbH
SPDX-License-Identifier: Apache-2.0
-->

# ADR-020: Assessment Layer (L4): a Railway Profile over the NIST Assessment model, not a fork

**Status:** Accepted (profile-over-NIST via props/ns; dual-encode 4-level scale with binary state; declared human-control level; AMC via recommended-means, 2026-11-10)

**Date:** 2026-11-10

**Deciders:** Jens Grote

> **Relationship to prior ADRs.** [ADR-007](./ADR-007-tooling-foundation.md) named the
> Assessment Layer as "Layer 4" over the NIST OSCAL Assessment model. This ADR specifies
> that layer. It reuses the mechanisms the sibling layer ADRs already established:
> [ADR-018](./ADR-018-rules-format-oscal-native.md) (L2) and
> [ADR-019](./ADR-019-change-layer-vcs-native.md) (L3) both realize their layer as a thin
> additive profile over stock NIST plus an `oscal4rail` `ns`, validated by an additive
> constraints schema. [ADR-008](./ADR-008-reproducible-schema-acquisition.md) pins the NIST
> schemas by tag + SHA; [ADR-013](./ADR-013-validator-consolidation.md) is the two-pass
> validator this layer plugs into. Requirements come from issues #26 (railway Assessment
> Profile over NIST), #10 (AMC/AltMoC, closed) and #27 (worked example).

## Context

The Assessment Layer records *whether a system satisfies a control*. NIST OSCAL already
provides a **Released** assessment model (`assessment-results`) in OSCAL 1.x; the NIST
reference notes the layer "will be expanded in OSCAL 2.0". The task is therefore not to
invent an assessment format but to decide how OSCAL4Rail **profiles** the existing one so
it carries railway needs without forking.

### Facts (verified 2026-11-10, against the pinned NIST schemas and an independent reader)

Read from `schemas/nist/oscal-assessment-results.json` (OSCAL 1.2.3, draft-07, pinned via
ADR-008), confirmed by building a walking skeleton and parsing it with an independent NIST
reader (`compliance-trestle`), which reads every field below back out of its NIST model:

- `assessment-results` requires `uuid, metadata, import-ap, results`.
- `result` requires `uuid, title, description, start, reviewed-controls`; it has native
  `attestations`, `observations`, `findings`, `risks` slots.
- `finding` requires `uuid, title, description, target`; `finding.target` requires
  `type, target-id, status`.
- **`finding.target.status.state` is binary only: `satisfied | not-satisfied`.**
- `finding.target.status.reason` is a **TokenDatatype** (`anyOf` token | enum
  `pass|fail|other`), **not** free prose — prose belongs in `status.remarks`. (The
  independent reader caught this where the repo JSON-Schema pass alone did not.)
- `property` requires `name, value`; optional `ns` is the sanctioned extension point.
- `responsible-party` requires `role-id, party-uuids`.

**Key constraint (verified, not assumed):** a 4-level railway scale cannot replace the
binary NIST `state`; it must ride on `props` under an OSCAL4Rail `ns`. That *is* the
"profile, not fork" mechanism, identical to how L1/L2/L3 extend NIST.

## Decision Drivers

Derived from the architecture requirements (issues #26/#10/#27), not from the options. Each
driver is the yardstick a considered option is measured against; the yardstick was fixed
before the options were weighed.

1. **K1 — Profiles NIST, no fork (hard).** Every valid OSCAL4Rail assessment MUST be a
   valid NIST assessment (#26 AC "Profiles NIST (not a fork)"; ADR-007; Framework ≠ Content
   ADR-007).
2. **K2 — Four-level railway scale (hard).** `fully | partially | not | not-applicable`
   must be expressible (#26 AC "railway scale").
3. **K3 — assessor-type (high).** `human | agent | hybrid` must be expressible (#26 AC
   "by humans or agents").
4. **K4 — Meaningful Human Control as a frame (hard).** Any autonomous evaluation
   (`agent`/`hybrid`) happens **inside a demonstrable human release**. The release may sit
   at different levels — per step (attestation), at the guardrail (an approved
   agent/MCP/policy definition), or at the seed/instance configuration. L4 MUST let a
   result **name the level** at which the human release sits and make that release
   **referenceable**; it MUST NOT prescribe the level. (Exploration evidence: a mandatory
   human sign-off exists in only one of three real artifacts — it must be enforced
   additively; Goodhart protection.)
5. **K5 — AMC/AltMoC without a bespoke schema (high).** Presumption-of-compliance (AMC
   followed) and AltMoC (alternative chosen → must demonstrate) must be expressible by
   reusing the EASA construct, not a standalone O4R schema (#10, closed).
6. **K6 — Machine-evaluable for human/agent/automation + compliant-by-default in CI
   (hard).** The verdict must be readable by a human, an agent and automation, and the
   artifact must validate through the ADR-013 pass (report + exit code) so a pipeline can
   gate on it ("compliant by default", including in code development).
7. **K7 — Traceability to the catalog (high).** "What applies to me": the result links
   back to the controls via `import-ap` + `reviewed-controls` (NIST-native traceability).
8. **K8 — Owner authority / verbatim (hard).** Assessment criteria live on the control
   (owner-owned, verbatim); L4 invents no requirement text (ADR-007, Invariant 1).

## Decision

**Realize Layer 4 as a thin additive Railway Profile over the NIST `assessment-results`
model.** No bespoke assessment format; NIST stays the base, OSCAL4Rail specifics ride on
`props` under `ns=https://github.com/OpenRailAssociation/oscal4rail/ns`, hardened by a new
additive constraints schema `schemas/oscal4rail/oscal4rail-assessment.schema.json` (same
pattern as `oscal4rail-catalog-constraints.schema.json`).

Concretely, across four decision axes:

1. **Approach = profile over NIST (props/ns).** Every valid O4R assessment is a valid NIST
   assessment; the additive schema is the only own surface (K1, K6, K7, K8).

2. **Four-level scale = dual-encode with a validator cross-check.** The binary NIST
   `finding.target.status.state` is kept for NIST tooling; the 4-level verdict rides on a
   `compliance-level` prop under the O4R `ns`. The validator enforces the mapping
   (`fully → satisfied`; `partially`/`not → not-satisfied`; `not-applicable` signalled via
   the prop), so the two encodings cannot drift (K1, K2, K6). Prose justification goes in
   `status.remarks`; `status.reason` stays a NIST token.

3. **Human control = a declared, referenceable release level.** `assessor-type`
   (`human|agent|hybrid`) is descriptive. The **gate** is the human release, which the
   result MUST declare and reference at one of these levels, owner's choice:
   per-step attestation (`result.attestations` + `responsible-party`), an approved
   guardrail/agent/MCP definition, or an approved seed/instance configuration. L4 requires
   the *level to be named and the release to be referenceable*; it does not mandate which
   level (K4).

4. **AMC/AltMoC = control-level `link rel="recommended-means"` + result evidence.** An AMC
   is a recommended-means link on the control; a result that cites it carries the
   presumption of compliance, a result that does not (AltMoC) MUST carry explicit
   demonstration evidence. No standalone AMC schema (K5, reusing #10).

### Scope note (Framework ≠ Content, ADR-007)

The assessment *criteria* are verbatim, owner-owned text on the control
(`part name="assessment-criteria"`). L4 defines the *shape* of an assessment and the
*additive constraints*; it never authors criteria or verdicts. The worked example under
`examples/assessment/` is illustrative, not a real regulation.

## Considered Options

### Axis A — how L4 relates to NIST

**A1: Own assessment format / fork (rejected).**
- (−) Violates K1 by definition; loses free NIST-tooling interoperability (K6/K7 only with
  own effort). Inconsistent with L1/L2/L3, which all profile NIST.

**A2: Profile NIST via props/ns + additive constraints schema (CHOSEN).**
- (+) Satisfies K1; keeps NIST tooling (an independent NIST reader parses the skeleton).
- (+) Minimal own surface — one additive schema, same pattern as L1 (Occam).
- (+) Carries K2/K3/K4 add-ons on the sanctioned `props/ns` extension point (K5/K7/K8 too).

**A3: Wait for OSCAL 2.0 (rejected).**
- (−) Delivers nothing now; #26/#27 stay open. The 1.x assessment models are Released and
  sufficient to build on.

### Axis B — four-level scale vs. binary NIST `state`

**B1: props only, ignore `state` (rejected).**
- (−) A NIST reader then sees no status → weakens K6 (NIST-tooling interoperability).

**B2: dual-encode `state` + `compliance-level` prop, with a validator cross-check (CHOSEN).**
- (+) K2 and K6 both met; NIST tooling reads `state`, humans/agents read the 4-level prop.
- (+) The cross-check actively protects K1 against the two encodings drifting (Goodhart).

**B3: both fields, no cross-check (rejected).**
- (−) Prop and `state` can silently diverge — the silent-drift/Goodhart case the invariants
  forbid.

### Axis C — where the human release sits (K4)

**C1 attestation at the result / C2 approved-guardrail reference / C3 seed-release
reference (each alone: rejected as the *only* option).**
- (+) Each satisfies K4 for one anchoring level.
- (−) Each covers only one of the three legitimate levels; prescribing one breaks K4's
  "do not mandate the level".

**C4: multi-level — the result declares which level the human release sits at, and makes it
referenceable (CHOSEN).**
- (+) Satisfies K4 as framed: level named + release referenceable, level not prescribed.
- (+) C1/C2/C3 become the permitted *expressions* of C4, not competing designs.

### Axis D — AMC/AltMoC encoding

**D1: a standalone O4R AMC schema (rejected).**
- (−) Excluded by #10 ("no separate oscal4rail-amc schema") and would breach K1.

**D2: control `link rel="recommended-means"` + result evidence (CHOSEN).**
- (+) Expresses presumption-of-compliance and AltMoC with NIST-native means only; reuses
  the EASA construct as prior art (K5), no new schema.

## Consequences

### Positive

- L4 is consistent with L1/L2/L3: profile over NIST, `ns`-props, additive constraints
  schema, ADR-013 two-pass validation. One mental model across all four layers.
- A system's compliance is readable by humans, agents and automation from the same artifact,
  and gateable in CI (K6, "compliant by default").
- "Profile, not fork" is empirically demonstrated: an independent NIST reader
  (compliance-trestle) parses the example and reads the O4R `ns`-props, the finding state,
  the sign-off and `import-ap` back out of its NIST model.

### Negative / trade-offs

- **Dual encoding (B2) is bookkeeping.** Two fields must agree; the burden is moved into the
  validator cross-check rather than removed. Accepted: it is the price of staying
  NIST-tooling-readable while carrying a 4-level scale.
- **C4 shifts responsibility to the owner** to declare the release level honestly. L4 can
  require the declaration to be present and referenceable, but cannot verify that the named
  guardrail/seed release was itself meaningful. Accepted: that is Meaningful Human Control,
  not a tooling guarantee.
- **Deliberate deviation from issue wording.** #27 says "against BS-KI"; the walking skeleton
  uses an illustrative, self-contained catalog to prove integrability first. The BS-KI
  worked example is refined as a follow-up, not newly scoped.

### Re-evaluation trigger (NIST schema evolution)

This decision is bound to the pinned NIST stand (1.2.3; assessment models Released; `state`
binary). **If** a new NIST OSCAL version extends the assessment model — a new pinned tag in
`schemas/nist/manifest.json` (ADR-008), in particular the announced OSCAL 2.0 assessment
expansion — **then** this decision MUST be re-evaluated against drivers K1–K8 and the ADR
status reviewed (Accepted / Superseded). Specifically, a native multi-level verdict in 2.0
would turn B2's dual encoding from a necessity into a simplification opportunity, not a
breaking change.

## Follow-ups

- #26 Schema `schemas/oscal4rail/oscal4rail-assessment.schema.json` — the additive
  constraints (hardens `compliance-level`, `assessor-type`, the required declared
  human-release level) so the ADR-013 pass 2 reports `o4r=pass` instead of `skipped`.
- #26 Spec `docs/reference/assessment-format.md` (this ADR is its decision basis).
- #27 Second worked example demonstrating a C4 level other than per-step attestation
  (e.g. `assessor-type: agent` with an approved-guardrail or seed release reference), so all
  three K4 anchoring levels are shown, and a fuller BS-KI walkthrough.
- Register ADR-020 in arc42 chapter 9 (the master list of architecture decisions).

## References

- Issues #26 (railway Assessment Profile over NIST), #10 (AMC/AltMoC, closed), #27 (example).
- [ADR-007](./ADR-007-tooling-foundation.md), [ADR-008](./ADR-008-reproducible-schema-acquisition.md),
  [ADR-013](./ADR-013-validator-consolidation.md), [ADR-018](./ADR-018-rules-format-oscal-native.md),
  [ADR-019](./ADR-019-change-layer-vcs-native.md).
- `docs/experiments/l4-assessment-exploration.md` (the proof-before-specification exploration).
- NIST OSCAL Assessment Layer: https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/
- EASA — Acceptable Means of Compliance (AMC) and Alternative Means of Compliance (AltMoC):
  https://www.easa.europa.eu/en/document-library/acceptable-means-compliance-amcs-and-alternative-means-compliance-altmocs
