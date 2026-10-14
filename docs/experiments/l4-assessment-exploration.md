# Exploration: Assessment Layer (L4) as an integrable NIST profile

> Status: exploration (not yet a decision — see ADR backlog). Diátaxis: explanation.
> Relates to issues #26 (railway Assessment Profile over NIST), #27 (BS-KI assessment example), #22 (EASA AMC/AltMoC analysis).
> Approach: proof before specification. Derive the layer from existing artifacts that already carry the assessment function, instead of designing on a blank page.

## Goal

Define L4 so that it **profiles** the NIST OSCAL Assessment Layer rather than forking it: every valid OSCAL4Rail assessment document is also a valid NIST assessment document, plus additive OSCAL4Rail constraints. Upgradeable to OSCAL 2.0 by design — when 2.0 adds native assessment automation, that becomes a simplification, not a breaking change.

## Verified NIST base

Read from `schemas/nist/oscal-assessment-results.json` (OSCAL 1.2.3, JSON Schema draft-07, pinned via ADR-008 with SHA-256):

- `assessment-results` required: `uuid, metadata, import-ap, results`
- `result` required: `uuid, title, description, start, reviewed-controls`; has native `attestations`, `observations`, `findings`, `risks` slots
- `finding` required: `uuid, title, description, target`
- `finding.target` required: `type` (enum `statement-id | objective-id`), `target-id`, `status`
- `finding.target.status.state` enum is **binary only**: `satisfied | not-satisfied`
- `property` required: `name, value`; optional `ns` → **the extension point**
- `responsible-party` required: `role-id, party-uuids`

**Key constraint (verified, not assumed):** NIST `status.state` is binary. A 4-level railway scale cannot replace `state`; it must ride on `props` with an OSCAL4Rail `ns`. That *is* the "profile, not fork" mechanism.

NIST layer rules confirm the two-part split (source: https://pages.nist.gov/OSCAL/learn/concepts/layer/, last updated 2026-01-29):
- Control Layer verbatim: *"Controls may include … objectives, and assessment methods."* → criteria belong in the control.
- Profile verbatim: *"a profile may be used to tailor … control objective, and assessment actions."* → tailoring is the profile's job.
- *"native traceability from the assessment layer to the catalog layer … import mechanism."* → result is a separate instance linked by `import-ap`.
- Note: *"The assessment layer will be expanded in OSCAL 2.0 …"* — but all assessment models are already **Released** in 1.x; we build on those.

## Evidence base (data sources, NOT framework content)

Three existing IT-governance artifacts already carry the L4 function. They use different vocabulary for the same job; the profile is their common abstraction. Sources anonymized (internal data sources, referenced as proof the pattern holds):

| L4 element (NIST) | EA self-declaration catalog (architecture principles) | Architecture-guild AMC set | Agent classification decision tree |
|---|---|---|---|
| assessment criteria @ control | `parts name=assessment-criteria`, 4 levels, verbatim text | — | `question` / `answers` / `paths` |
| recommended means (optional) | — | **AMC = preferred pattern solution** (optional; alternative proof allowed) | — |
| compliance verdict | rating enum (fully / partially / not met / not relevant) | — | category 1..4 |
| human sign-off (MHC) | approver confirmation (bool + text) | **missing** | **missing** |
| POA&M | conditions (deadline / status) | — | single-check / trigger |

Finding: a mandatory human sign-off exists in **only one** of the three. This confirms that OSCAL4Rail must add the sign-off as a required element over NIST (Meaningful Human Control / Goodhart protection) — it is not reliably present in the wild.

## Means-of-compliance semantics come from EASA (not invented here)

Authoritative source: EASA — Acceptable Means of Compliance (AMC) and Alternative Means of Compliance (AltMoC): https://www.easa.europa.eu/en/document-library/acceptable-means-compliance-amcs-and-alternative-means-compliance-altmocs

- **AMC** = non-binding standard issued by the regulator, carrying a **presumption of compliance** when followed.
- **AltMoC** = alternative chosen by the regulated party; **presumption is lost**, compliance must be demonstrated to the authority.

The architecture-guild AMC set is a live implementation of exactly this construct — verbatim: *"Ein AMC ist optional. Du kannst jederzeit auch einen anderen Lösungsweg wählen, dann musst du aber selbst den Nachweis erbringen, dass der gewählte Ansatz die Vorgabe erfüllt."* ("An AMC is optional. You may choose another path, but then you must demonstrate yourself that it satisfies the requirement.")

OSCAL encoding: model AMC as a control-level `link rel=recommended-means`; a result that does **not** cite the AMC is the AltMoC case and must carry explicit demonstration evidence. Presumption-of-compliance = the result references the AMC link. Feeds #22 and #10.

## Proposed design (two parts)

**Part A — criteria in the catalog (static, owner-owned).** Assessment criteria as `part name=assessment-criteria` on the control (verbatim text), with an OSCAL4Rail prop for the normalized level and an optional `link rel=recommended-means` → AMC. Tailoring via the profile.

**Part B — result as a separate instance (dynamic, with mandatory MHC).** Validates against `nist/oscal-assessment-results.json`, linked by `import-ap`. OSCAL4Rail add-ons via `props` (ns = `https://oscal4rail.org/ns`):
- `o4r:compliance-level` ∈ `fully-satisfied | partially-satisfied | not-satisfied | not-applicable`
- `o4r:assessor-type` ∈ `human | agent | hybrid`
- **mandatory human sign-off** — hardened to REQUIRED by the OSCAL4Rail constraints schema.

```
Catalog control (L1)                     Assessment result instance (L4)
─────────────────────                    ───────────────────────────────
part name=assessment-criteria (verbatim)   import-ap → catalog/profile
props: o4r:compliance-level (criteria)      finding.target.status.state  (NIST binary)
link rel=recommended-means → AMC (opt.)     props: o4r:compliance-level  (4-level)
                                            props: o4r:assessor-type
                                            attestations + responsible-party (sign-off, REQUIRED)
                                            findings → POA&M
```

## Open decisions (to resolve in #26, then ADR)

1. **4-level scale ↔ binary NIST `state`.** Keep NIST `state` for tooling + carry `o4r:compliance-level` as a prop. Mapping: fully→satisfied; partially/not→not-satisfied; not-applicable→omit or signal via prop. Risk: double-encoding drift → validator cross-checks prop vs. state.
2. **Where does the sign-off sit?** Candidates: `result.attestations` (NIST-native) + `responsible-party` (role `o4r-approver`), hardened to REQUIRED by the constraints schema. Confirm against the attestations sub-schema.
3. **assessor-type vs. sign-off.** `agent`/`hybrid` assessments still require a human sign-off to count as "met". assessor-type is descriptive; sign-off is the gate.
4. **AMC/AltMoC in OSCAL.** `link rel=recommended-means` on the control; AltMoC = result without AMC citation → explicit demonstration required.

## Next step

Minimal walking skeleton for #27: one finding that (a) validates against `nist/oscal-assessment-results.json` and (b) carries `o4r:compliance-level` + a mandatory sign-off via props/attestations. If NIST tooling (e.g. trestle) reads it cleanly → integrability proven → then freeze an ADR (L4 = NIST assessment profile) and the `schemas/oscal4rail/` assessment constraints schema.

**Dependency note:** L4 sits on the v0.1.1 catalog base (catalog format spec #2 → constraints schema #3 → consolidated validator #5). The assessment constraints schema mirrors the catalog constraints schema pattern, so #3 is the structural blueprint for the L4 schema.

---
> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
