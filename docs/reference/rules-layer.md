# Rules Layer (Layer 2) — reference

> Normative reference for the OSCAL4Rail Rules Layer. Decisions: [ADR-014](../adr/ADR-014-rules-layer-placement.md)
> (placement, version coupling) and [ADR-018](../adr/ADR-018-rules-format-oscal-native.md)
> (OSCAL-native format, Metapath Subset v1, rule-fields convention). Schema:
> [`oscal4rail-rules.schema.json`](../../schemas/oscal4rail/oscal4rail-rules.schema.json).
> Framework ≠ Content ([ADR-007](../adr/ADR-007-tooling-foundation.md)): this document
> defines the *mechanism*; obligation/status/context vocabularies are owner content.

## 1. What Layer 2 answers

Layer 1 (Catalog) carries **what** is required (verbatim statement) and a **static**
applicability matrix (`context × obligation`, see [catalog-format.md §6](./catalog-format.md)).
Layer 2 adds the **decision logic** the catalog deliberately does not carry: under which
conditions a control applies, with which obligation strength, and in which choice
relation to other rules.

## 2. Placement and version coupling (ADR-014)

The logic lives in a **separate artifact** (a `rule-set`), not inline on the control.
The control binds it through the NIST-native `link rel="decision-logic"`. The
`rule-set.metadata.version` **MUST equal** the bound catalog's `metadata.version`; this
equality is enforced by `oscal4rail validate` as an error, not by the schema.

**Two separate files are binding (ADR-018 §10).** The L1 catalog and the L2 rule-set are
always separate documents; a single document mixing both is invalid. A source that mixes
a verbatim statement (L1) with modality/logic (L2) is **split** on migration into a
catalog file and a rule-set file, linked by `control-id`. Therefore `control-id` is
mandatory. Owner convenience is served by the round-trip generator, which co-presents
control + logic without merging the files.

**`catalog-ref` = identity + resolution, not ownership.** The rule-set names the catalog
it serves via `catalog-ref`:
- `catalog-uuid` — the **identity** of the served catalog (its `uuid`); a stable,
  location-independent SSOT anchor. `oscal4rail validate` checks it equals the resolved
  catalog's own `uuid`.
- `href` — the **resolution hint** (where the tool finds the file: path or URL).

The catalog's **owner/publisher and regulation are NOT in `catalog-ref`** — they live in
the catalog's own `metadata` (e.g. `responsible-party`, source-document props), stated
once (SSOT). This avoids holding ownership in two places (silent-drift guard).

## 3. The rule-fields convention (ADR-018 §8)

The framework defines the fields; the owner fills them. Controlled fields use
**owner-declared vocabularies bound to a fixed semantics axis** — the owner invents the
words, the catalog declares what they mean, and the agent reads only the fixed axis.

| Field | Modality | Meaning |
|---|---|---|
| `rule-id` | MUST | stable, semantic ID, never reused |
| `control-id` | MUST | the L1 control this rule governs |
| `modality` | MUST | obligation **strength** (declared label; bound to `binding` + `rank`) |
| `status` | MUST | lifecycle (declared label; bound to `active` + a fixed `lifecycle` axis, §3.1.1) |
| `applies-when` | MAY | decision logic (Metapath Subset v1, §5) |
| `rule-group` + `choice` | MAY | obligation **relation** (`all` / `one-of` / `one-or-more`) |
| `parameters` | MAY | calibratable, optionally dated thresholds |
| `enforcement` | SHOULD | *how* enforced — a **list** of declared labels (`deterministic`/`decision-model`/`agentic`); a rule may be enforced several ways at once. Declaration only, evaluated at L4 |
| `source-ref` | SHOULD | SSOT pointer (document + section); no verbatim duplication |
| `deviations` | MAY | conflict-as-data — declaration only, status at L4 |
| `remarks` | MAY | owner prose, always allowed; never the machine signal |

### 3.1 Two modality dimensions (MECE)

Obligation has two independent dimensions — do not conflate them:

- **Strength** (how binding one rule is): declared vocabulary bound to `binding: bool`
  + `rank: int` (lower = stronger) + `polarity: required | forbidden` (mandate vs.
  prohibition). Example: `MUSS → {binding: true, rank: 1, polarity: required}`,
  `DARF NICHT → {binding: true, rank: 1, polarity: forbidden}`. Without `polarity` a
  mandate and a prohibition would be indistinguishable to the agent.
- **Relation** (choice between rules, "entweder-oder"): a `rule-group` with a fixed
  `choice` of `all | one-of | one-or-more`, mapped onto NIST `parameter-selection/@how-many`.

### 3.2 Status lifecycle axis

`status` carries, besides `active: bool`, a fixed `lifecycle` axis the agent reads instead
of the owner's word:

| `lifecycle` | Meaning |
|---|---|
| `draft` | not yet in force |
| `active` | in force |
| `deprecated` | still binding for existing (legacy) systems, **not** to be used for new ones |
| `superseded` | replaced by another rule; carries `superseded-by: <rule-id>` |
| `withdrawn` | retired without replacement |

`active: bool` and `lifecycle` are consistent by convention (`active` is `true` for
`draft`/`active`/`deprecated` where the rule may still bind something, and `false` for
`withdrawn`; `superseded` depends on whether the superseding rule carries the obligation).
A `deprecated` rule is the typical legacy case: pair it with an `applies-when` that
restricts it to legacy scope, so the rule stays in force only where it must. This axis is
what the Change Impact Layer (L3) reads to classify a change as `deprecated` / `superseded`
/ `withdrawn` (see [change-format](./change-format.md) §4.3).

### 3.3 Why this is both owner-defined and agent-interpretable

The agent never interprets the owner's words. It reads the declared **semantics axis**
(`binding`, `rank`, `active`, `lifecycle`, `kind`, `choice`), which is fixed and small.
This keeps
the format adaptive (any regulation's vocabulary) and deterministic (one machine
meaning). The owner's wording survives verbatim in labels and `remarks`.

## 4. The applicability sources slot (#11)

A rule draws its applicability inputs from a **generic, declared set of sources** so the
same expression language works across regulations without hard-coding dimensions:

- **`context('<dimension>')`** — one dimension of the catalog's applicability `class`
  path (§6), e.g. `location`, `transport`. Dimensions are the catalog's controlled
  vocabulary; the rule-set does not invent them.
- **`param('<id>')`** — a value from `rule-set.parameters`, optionally dated
  (temporal values). The most recent entry with `from <=` the evaluation date wins.
- **Ordinal scales** — a named order declared under `vocabularies.ordinal-scales`
  enables ordinal comparison (`<=`, `>=`) over non-numeric vocabularies.

These are the only external inputs an expression may read. It MUST NOT read the verbatim
statement text, navigate the document tree freely, or call environment/non-deterministic
functions (§5).

## 5. Decision logic: Metapath Subset v1 (ADR-018 §2)

The logic is an OSCAL-native `parameter/constraint/test/expression` string, constrained
to a deterministic subset so results are reproducible and owner-auditable.

**An expression MAY use (EARS, ubiquitous):**

- boolean `and`, `or`, `not(...)`, arbitrarily nested;
- comparison / threshold `=`, `!=`, `<`, `<=`, `>`, `>=` over typed literals;
- ordinal comparison over a declared scale (§4);
- `context('<dimension>')`;
- `param('<id>')`;
- set membership `x = ('a','b','c')`;
- literals: number, quoted string, boolean, ISO-date.

**An expression MUST NOT use (EARS, unwanted):**

- arbitrary axis navigation (`//`, `..`, `following::`, document-order dependence);
- non-deterministic or environment-reading functions (`current-dateTime()`,
  `document()`, `doc()`, randomness, any I/O);
- recursion or user-defined functions;
- any read of the verbatim `statement` text.

### 5.1 Examples (from the worked example)

```
context('location') = 'haltestelle' and context('transport') = 'bahn'
context('location') = 'fahrzeug-innen' and param('schwelle-fahrzeuge') <= 30
```

A boolean AND-group of criteria (the common "all of the following apply" pattern) is a
`rule-group` with `choice: all` whose members each carry their own `applies-when`.

### 5.2 Grammar (EBNF)

The subset as a grammar (ISO 14977 EBNF). An expression is inside Subset v1 exactly if
it derives from `expression`. The validator checks this with
`tools/metapath_subset.py`; it does not evaluate anything (evaluation is Layer 4, §6).

```ebnf
expression  = or-expr ;
or-expr     = and-expr , { "or" , and-expr } ;
and-expr    = term , { "and" , term } ;
term        = "not" , "(" , or-expr , ")"
            | "(" , or-expr , ")"
            | comparison ;
comparison  = operand , comp-op , operand
            | operand , ( "=" | "!=" ) , value-list ;
comp-op     = "=" | "!=" | "<" | "<=" | ">" | ">=" ;
operand     = reference | literal ;
reference   = ( "context" | "param" ) , "(" , string , ")" ;
value-list  = "(" , literal , { "," , literal } , ")" ;
literal     = number | string | boolean ;
boolean     = "true" , "(" , ")" | "false" , "(" , ")" ;
number      = [ "-" ] , digit , { digit } , [ "." , digit , { digit } ] ;
string      = "'" , { character | "''" } , "'"
            | '"' , { character | '""' } , '"' ;
```

Notes on the grammar:

- **`and` binds tighter than `or`**; parentheses group. `not` is written as a function,
  `not(...)`, as in Metapath.
- **Every term is a comparison.** A bare `context('x')` or `param('x')` is not an
  expression; compare it with a literal.
- **Booleans** are written `true()` and `false()`, as in Metapath. A bare `true` would
  be a path step, which the subset does not have.
- **ISO dates** are written as quoted strings in ISO 8601 form (`'2026-01-01'`). The
  grammar treats them as strings; that a value is compared as a date follows from the
  declared parameter and is decided at evaluation.
- **A quote inside a string** is written twice (`'it''s'`).
- **Whitespace** (including line breaks) between tokens is not significant.
- Everything else is outside the subset and rejected: path and axis navigation (`/`,
  `//`, `..`, `axis::`), predicates, variables, attribute access, bare names, and every
  function other than `context()`, `param()`, `not()`, `true()`, `false()`.

## 6. Layer boundary: L2 declares, L4 evaluates (ADR-018 §9)

`enforcement` and `deviations` are **declared** in L2 (how a rule is meant to be
enforced; that a deviation exists with rationale). Whether the rule was enforced, and
whether a deviation is approved/`verified` (the Meaningful Human Control decision point),
is **Layer 4 (Assessment)**, never L2. Do not record assessment state in a rule-set.

## 7. Validation

Run the rule-set through `oscal4rail validate`:

1. **Schema pass** — `oscal4rail-rules.schema.json` (structure, fixed `choice`/`kind`
   enums, required fields).
2. **Tool pass** — cross-artifact consistency, enforced as errors (ADR-018 §10):
   - **separation**: a catalog document carries no rule-set and vice versa;
   - **referential integrity**: `catalog-ref.catalog-uuid` matches the resolved
     catalog's `uuid`; `catalog-ref.href` resolves to a catalog; every
     `rule.control-id` resolves to a control in that catalog;
   - **version equality** with the bound catalog (ADR-014);
   - every `modality`/`status`/`enforcement` label is declared in `vocabularies`;
   - every `rule-group.member` resolves to a `rule-id`;
   - every `rule-id` is unique within the rule-set;
   - every `applies-when.expression` parses under Subset v1 (§5.2);
   - every `param('<id>')` an expression reads is declared in `rule-set.parameters`.

   Not checked: whether a `context('<dimension>')` names an existing dimension. The
   dimensions come from the catalog's applicability `class` path (§4), and the catalog
   format does not yet declare their names in a machine-readable place.

## 8. Rule quality is measured, not asserted

This format is a hypothesis until an agent decides applicability correctly against a
rule set built in it. Build a **golden set** (inputs with known expected outcomes), have
an agent evaluate, and measure the hit rate. This is assessment/tool work (L4 /
[ADR-015](../adr/ADR-015-oscal-agent-tooling-landscape.md) class), tracked separately.

> 🤖 Dieses Dokument wurde mit Unterstützung von KI erstellt (Art. 50 Abs. 4 KI-VO).
