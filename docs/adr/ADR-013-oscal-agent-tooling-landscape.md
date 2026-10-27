# ADR-013: OSCAL AI-Agent Tooling Landscape — Adopt vs. Reference

**Status:** Proposed
**Date:** 2026-10-27
**Deciders:** Jens Grote, Simon Freihart

## Context

ADR-007 chose `compliance-trestle` + `oscal-deep-diff` as the tooling foundation and
named `compliance-trestle-mcp` as the AI-agent integration path. Since then, a second
OSCAL-for-AI-agents tool entered the field (`awslabs/mcp-server-for-oscal`) and the
landscape shifted. This ADR records a verified snapshot of the OSCAL AI-agent tooling
landscape (as of 2026-10-27) and decides, per tool, whether OSCAL4Rail **adopts** it as a
dependency/reference or only treats it as a **historical reference**.

Two questions drive this decision:

1. Which existing OSCAL-agent tool, if any, should the downstream GovernanceAgent
   (a *consumer* of OSCAL4Rail catalogs — out of scope for this framework repo, but the
   motivating use-case) build on, rather than re-implementing OSCAL plumbing?
2. Does any existing tool already cover the OSCAL4Rail differentiators (Layer 2 Rules,
   Layer 3 Change Impact, Regulatory Cascade), which would force a re-scoping of this
   framework (cf. ADR-007 Framework ≠ Content)?

## Verified Landscape (2026-10-27)

Sources: GitHub API (`gh api`), PyPI JSON API. All facts below were read from the
primary sources, not inferred.

### A) `awslabs/mcp-server-for-oscal` — ARCHIVED

- License Apache-2.0; Python ≥3.11; pins NIST **OSCAL 1.2.1**; depends on
  `compliance-trestle ≥4.0.1` (same foundation as OSCAL4Rail, ADR-007).
- Repository is **archived** (`isArchived: true`), frozen at `v0.4.0` (2026-04-02); no
  deprecation/successor note in its README.
- Covers all 8 NIST models (query/list/validate), a 4-level validation pipeline
  (well-formedness → JSON Schema → Trestle → oscal-cli), SQLite FTS5 full-text search,
  and a SHA-256 hash-manifest integrity check of bundled content at startup.
- Cloud coupling: `boto3`, `strands-agents`; the `query_oscal_documentation` RAG tool
  requires an AWS Bedrock Knowledge Base (conditionally registered). Core tools run
  locally without remote services.

### B) `dfkunstler/mcp-server-for-oscal` — single-maintainer fork

- Non-archived fork of (A); owns the PyPI package `mcp-server-for-oscal` and has advanced
  it to **v0.7.1** (2026-10-26) while awslabs stayed at v0.4.0. PyPI `project_urls` now
  point to this fork.
- Personal account, 0 stars, no organizational governance → **bus factor 1**, no SLA.
  (Plausibly the original AWS maintainer continuing privately — *not verified*.)

### C) `oscal-compass` — CNCF Sandbox project

- CNCF Sandbox since 2024-06-21 (`.project` metadata); vendor-neutral; project leads
  `degenaro`, `butler54`; 30 repositories; Slack + ADOPTERS.
- `compliance-trestle` (287★, active 2026-10-26) — the OSCAL toolkit OSCAL4Rail already
  builds on (ADR-007).
- `compliance-trestle-mcp` (Apache-2.0, Python) — a thin MCP wrapper over trestle
  (`uvx --from compliance-trestle-mcp trestle-mcp`); no cloud coupling.
- `agentic-agile-authoring` (Apache-2.0, Python, active 2026-10-25) — an ecosystem of
  **portable authoring skills** (`SKILL.md` + `apm.yml`) for the OSCAL lifecycle
  (framework onboarding → catalog → component-definition → assessment → POA&M),
  installable across agent harnesses via **OpenAPM** (`apm-cli`), which also wires each
  skill's declared MCP servers into the harness's native config.

## Gap Analysis against the OSCAL4Rail 4-Layer Model

Both independent OSCAL-agent tools (A and the oscal-compass stack) cover the same NIST
ground and leave the same gaps:

| OSCAL4Rail Layer | Covered by existing agent tooling? | Consequence |
|---|---|---|
| L1 Catalog | Yes (NIST-native: query/list controls, groups, schema) | Do not re-build. Our value = Railway Profile / Constraints on top. |
| L2 Rules (Applicability) | **No** | **Differentiator holds** (Rulemapping adoption, ADR-006). |
| L3 Change Impact | **No** | **Differentiator holds** (structured diff / cascade propagation). |
| L4 Assessment | Yes (NIST-native: Assessment Plan/Results/POA&M) | Do not re-build. Our value = Railway evaluation scales + MHC. |
| Regulatory Cascade | Only flat cross-framework `Mapping Collection`; **no cascade semantics** (specializes/concretizes/propagation) | **Differentiator holds.** |
| Verbatim / round-trip / owner sign-off | **No** | **Differentiator holds** (verifiability by design). |

## Pugh Matrix (reference = `awslabs/mcp-server-for-oscal`, archived)

| Criterion | awslabs (ref) | dfkunstler fork | oscal-compass |
|---|---|---|---|
| Liveness / backing | 0 | S (active, 1 person) | + (CNCF, org) |
| License compatibility (→ Apache-2.0) | 0 | S | S |
| Trestle foundation (= our stack) | 0 | S | + |
| No cloud coupling | 0 (boto3/Bedrock) | S (inherits AWS deps) | + (trestle-native) |
| Railway USP covered (L2/L3/Cascade) | 0 | S | S (also not — stays our value) |
| Enablement pattern (skill portability) | − (monolith) | − | + (OpenAPM/apm.yml) |
| **Net** | reference | ~0 | **strongly +** |

## Decision

1. **`awslabs/mcp-server-for-oscal` → Reference only (historical).** Archived; not a
   dependency. Keep two of its design patterns as references because they serve the
   OSCAL4Rail "verifiability by design" principle:
   - the **SHA-256 hash-manifest integrity check** of bundled content at startup, and
   - the **4-level validation pipeline** ordering (well-formedness → JSON Schema →
     Trestle → oscal-cli).
2. **`dfkunstler/mcp-server-for-oscal` → Reference only.** Code reference acceptable; a
   single-maintainer, 0-star fork is not an acceptable supply-chain dependency.
3. **`oscal-compass` → Adopt as the living reference ecosystem.** It is the de-facto
   successor in the field and shares our trestle foundation:
   - `compliance-trestle-mcp` is the preferred MCP building block for the downstream
     GovernanceAgent (consumer project), superseding the archived AWS server. This
     confirms and updates ADR-007's agent-integration choice with verified 2026-10 data.
   - The `agentic-agile-authoring` **OpenAPM/`apm.yml` skill-portability pattern** is
     adopted as a reference for OSCAL4Rail's owner-enablement skills (harness-agnostic
     skill + declared MCP dependencies), subject to a license check per asset.
4. **Framework scope unchanged (confirms ADR-007).** Two independent OSCAL-agent tools
   cover L1/L4 and leave L2, L3 and the Regulatory Cascade uncovered. The OSCAL4Rail
   differentiators are therefore correctly scoped; no re-scoping is warranted.

## Consequences

**Positive:**
- Avoids re-implementing L1/L4 OSCAL plumbing in the consumer project; reuses the same
  trestle foundation end-to-end.
- Replaces a dead dependency (AWS, archived) with an org-backed, vendor-neutral one.
- Gains a concrete, proven skill-portability pattern for owner enablement.
- Independent corroboration that the Railway USP (L2/L3/Cascade) is real, not assumed.

**Negative / risks (Devil's Advocate):**
- `oscal-compass` is at CNCF **Sandbox** maturity (lowest tier) — no production SLA; and
  `compliance-trestle-mcp` has low adoption (2★). Mitigation: it is a thin wrapper over
  the well-adopted `compliance-trestle` (287★), so the blast radius of the wrapper is small.
- OpenAPM (`apm-cli`, microsoft/apm) is an additional external dependency for the
  enablement tooling; evaluate before committing (Occam's Razor — do not add it to the
  framework core, only to the enablement layer).
- License vigilance: adopt design patterns/structure as reference; do not copy code or
  assets without a per-asset license check (REUSE/`LICENSES/`).

## Follow-ups

- Spike: run `compliance-trestle-mcp` locally against the BS-KI catalog and record the
  tool surface (ties into ADR-007 evaluation methodology).
- Spike: install one `agentic-agile-authoring` skill via `apm-cli` into a harness to
  assess the `apm.yml` MCP-wiring model for our enablement skills.
- Cross-link this ADR from ADR-007 (tooling foundation) and from the README ADR index.

## References

- NIST OSCAL — https://pages.nist.gov/OSCAL/
- `awslabs/mcp-server-for-oscal` (archived) — https://github.com/awslabs/mcp-server-for-oscal
- `oscal-compass` (CNCF Sandbox) — https://oscal-compass.dev/ ·
  https://github.com/oscal-compass
- `compliance-trestle` — https://github.com/oscal-compass/compliance-trestle
- `compliance-trestle-mcp` — https://github.com/oscal-compass/compliance-trestle-mcp
- `agentic-agile-authoring` — https://github.com/oscal-compass/agentic-agile-authoring
- OpenAPM (`apm-cli`) — https://github.com/microsoft/apm
- ADR-006 (Rulemapping as Layer 2), ADR-007 (Tooling Foundation / Framework ≠ Content)

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
