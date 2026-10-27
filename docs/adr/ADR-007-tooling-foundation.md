# ADR-007: compliance-trestle as Tooling Foundation for OSCAL4Rail

**Status:** Proposed
**Date:** 2026-08-03
**Deciders:** Jens Grote

## Context

OSCAL4Rail requires tooling for:
1. Validation of OSCAL artifacts (Catalogs, Profiles, Assessments)
2. Profile Resolution (Cascade level → resolved Catalog)
3. Change Detection (Layer 3: structured diff between Catalog versions)
4. AI-Agent integration (MCP server for automated compliance checking)

For each of these functions, existing open-source tools are available. The question is: **Build a custom CLI from scratch or build on existing tooling ecosystems?**

## Alternatives

### Alternative A: Custom CLI (`oscal4rail` Python tool)

- Custom validator (`validate.py` — exists already as prototype)
- Custom profile resolution
- Custom diff tooling (`diff.py`)
- Custom MCP server

**Advantages:**
- Full control over implementation and UX
- No external dependency
- Lightweight, tailored to railway requirements

**Disadvantages:**
- High development effort (profile resolution alone is complex)
- OSCAL schema updates must be tracked manually
- No community contributing
- MCP server must be built from scratch

### Alternative B: compliance-trestle + oscal-deep-diff

- **compliance-trestle** (IBM/OSCAL-Compass, Apache 2.0, Python) for: Import, Validate, Profile Resolution, Workspace management, Plugin architecture
- **oscal-deep-diff** (NIST, Public Domain, TypeScript/Node) for: Structured diff between OSCAL documents
- **compliance-trestle-mcp** (OSCAL-Compass) for: AI-Agent integration via MCP
- Railway-specific logic as **trestle plugin** (`trestle-oscal4rail`)

**Advantages:**
- Profile resolution works out-of-the-box (evaluated with BS-KI)
- Validation against OSCAL 1.2.1 schema built-in
- Plugin architecture allows Railway extensions without fork
- MCP server already exists
- Active community (IBM, GSA, FedRAMP use it)
- oscal-deep-diff reliably detects Control-level changes (evaluated)

**Disadvantages:**
- Dependency on external project (governance risk)
- trestle is Python, oscal-deep-diff is TypeScript (two runtimes)
- trestle has many dependencies (>30 packages)
- Railway-specific semantics (tightened/relaxed) must still be built yourself

### Alternative C: oscal-cli (NIST, Java)

- Official NIST reference implementation
- Validation, profile resolution, conversion

**Advantages:**
- Official reference
- Most correct implementation

**Disadvantages:**
- Java runtime required
- No plugin architecture
- No MCP server
- Less agile-authoring-friendly

## Decision

**Alternative B: compliance-trestle + oscal-deep-diff as tooling foundation.**

Railway-specific logic will be implemented as a trestle plugin (`trestle-oscal4rail`), adding the following commands:

| Command | Function |
|----------|----------|
| `trestle oscal4rail cascade` | Analyze cascade levels (profile chain) |
| `trestle oscal4rail diff` | Semantic diff with Railway classification (tightened/relaxed/added/removed) |
| `trestle oscal4rail assess` | Generate assessment template with Railway evaluation scale |
| `trestle oscal4rail validate` | Check Railway constraints in addition to NIST schema |

Structural diffing is delegated to oscal-deep-diff (as subprocess or ported subset).

## Evaluation Results

### compliance-trestle v4.2.0

Evaluated on 2026-08-03 with BS-KI v1.0 Catalog:

```
$ trestle import -f bs-ki-de.yaml -o bs-ki-de
✅ Import successful

$ trestle validate -a
✅ VALID (3 unreferenced UUIDs in back-matter — warning, not error)

$ trestle author profile-resolve -n sbb-subset -o resolved-sbb
✅ Resolved Catalog contains only the 5 selected controls
✅ Props and statements fully preserved
✅ Link rel="resolution-source" to source catalog
```

Workspace structure mirrors all OSCAL models:
```
catalogs/ profiles/ assessment-plans/ assessment-results/
component-definitions/ mapping-collections/ system-security-plans/
plan-of-action-and-milestones/
```

### oscal-deep-diff v1.0.0

Evaluated on 2026-08-03 with BS-KI v1.0 → simulated v2.0:

```
Changes inserted:
- Threshold 800 → 500 (text change in bs-ki-2.1)
- Applicability recommended → binding (obligation tightened)
- New control bs-ki-2.99 (added)

Result:
✅ All 3 changes detected
✅ JSON pointer to changed fields
✅ New control identified as "rightOnly"
✅ Performance: 7ms for 42 controls
```

Output format:
```json
{
  "changes": [
    {"change": "property_changed", "leftPointer": "/catalog/groups/0/controls/0/parts/0/prose", ...},
    {"change": "property_changed", "leftPointer": "/catalog/groups/0/controls/0/props/2/value", ...},
    {"change": "array_changed", "rightOnly": [{"rightElement": {"id": "bs-ki-2.99", ...}}]}
  ],
  "score": 230
}
```

## Consequences

### Positive
- Fast time-to-value: profile resolution, validation, import work immediately
- MCP server for AI agents exists
- Community connection to OSCAL-Compass ecosystem
- FedRAMP plugin as reference for own railway plugin

### Negative
- Two runtimes (Python + Node.js) for the complete stack
- Governance risk: dependency on IBM-led OSS project
- oscal-deep-diff is not published on npm (must be installed from GitHub)

### Measures
- trestle plugin as separate package (`trestle-oscal4rail`), not as fork
- oscal-deep-diff subset for required diff logic optionally port to Python (eliminates Node dependency)
- Fallback: If trestle is discontinued, plugin code can be extracted as standalone CLI

## References

- [compliance-trestle](https://github.com/oscal-compass/compliance-trestle) – Apache 2.0
- [compliance-trestle-mcp](https://github.com/oscal-compass/compliance-trestle-mcp) – MCP server
- [oscal-deep-diff](https://github.com/usnistgov/oscal-deep-diff) – Public Domain
- [oscal-cli](https://github.com/usnistgov/oscal-cli) – NIST reference (Java)
- [compliance-trestle-fedramp](https://github.com/oscal-compass/compliance-trestle-fedramp) – Reference for sectoral plugin

---

## Addendum (2026-09-29): Engine Line for the Foundation (Build vs. Adopt)

Clarification as part of foundation work (WP0). Does **not** revoke the decision above,
but sharpens the order for the *first viable foundation*.

**Updated facts (2026-09-29):**
- `compliance-trestle` is now a **CNCF Sandbox Project** (no longer solely
  IBM-driven) — the governance risk from "Consequences/Negative" has decreased.
- NIST provides schemas as versioned release assets (→ [ADR-008](./adr/ADR-008-reproducible-schema-acquisition.md)),
  enabling the validation core **without** trestle.

**Decision for the foundation phase (WP1–WP4):**

The foundation's *engine line* is a **lightweight Python core** (`jsonschema`,
Draft-07, minimal/portable/inspectable — tech stack principle). The tools decided on in ADR-007
remain valid, but in clearly delimited roles:

| Function | Foundation (standard) | Optional reference/backend |
|----------|-----------------------|----------------------------|
| Schema retrieval | NIST release assets + SHA256 (ADR-008) | `oscal-cli`/`make schemas` (audit/fallback) |
| Validation | own Python validator (NIST schema + O4R constraints) | `oscal-cli` / `trestle validate` (cross-check) |
| Profile resolution | (later) | `compliance-trestle` (already evaluated) |
| Diff (Change Engine) | Python diff over OSCAL-JSON + Railway classification | `oscal-deep-diff` as reference/backend |
| AI-Agent integration | out of scope of foundation | `compliance-trestle-mcp` (Project 3) |

**Rationale:** For the governance pitch, an **inspectable, dependency-lean core**
is more valuable than a multi-runtime stack. `trestle`/`oscal-deep-diff`/`oscal-cli` remain the
reference for cross-checks and for functions beyond the foundation (profile resolution,
MCP). The trestle-plugin option (ADR-007 core) is thus **not rejected**, but deferred to the
time after the foundation.
