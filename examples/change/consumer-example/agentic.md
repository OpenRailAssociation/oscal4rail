# Agentic consumer (optional build-up over the pipeline case)

The same deterministic OSCAL change report can be consumed by an **agent** (a micro-agent
per catalog, triggered by cron or a webhook) instead of a plain pipeline. The agent adds
contextual routing ("does this affect *my* system, and what should happen"), but it reads
the **same** machine-readable artifact and must stay within the guardrails the using
organisation sets (ADR-019 D6).

This is an optional build-up: start with the non-agentic pipeline (`ci-pipeline.md`); add
an agent only where contextual interpretation is worth it.

## Trigger options

- **Scheduled** (daily/weekly): the agent runs `tools/change <last-seen-ref> <HEAD> <catalog>`
  on a watched repository and acts when the report is non-empty.
- **Webhook**: on a push / merge event the forge calls the agent with the base and head refs.

## Agent instruction (prompt sketch)

> You monitor an OSCAL4Rail rule catalog for changes. On each trigger:
> 1. Run `tools/change <base-ref> <head-ref> <catalog-path> [--rules-from … --rules-to …]`
>    to produce the OSCAL change report. Do **not** re-implement the diff; Git provides it.
> 2. Validate it: `tools/validate.py --strict <report>`. If it does not validate, stop and
>    report the tooling error. Do not guess.
> 3. For each `map`: read `control-id`, `@relationship` (the category) and the
>    `changed-field` / old-new props. Read only these machine fields, never the owner's
>    prose, and never infer meaning from wording.
> 4. Decide whether the change affects the systems you are responsible for (your context),
>    and route a reaction that is **within your configured guardrails**: notify the owner,
>    open a downstream issue/MR, request an L4 re-assessment.
> 5. You must **not** approve the change, decide a tightening is correct, or modify and
>    merge a downstream catalog autonomously. That is the owner's governance decision
>    (Meaningful Human Control). Surface it for sign-off instead.

The agent may call `react_to_change.py` as a deterministic tool for steps 3–4, then add its
contextual judgement on top. The determinism stays in the report and the classification;
the agent only adds routing within policy.

## Why an agent is allowed here

Autonomous agents are legitimate and are the point (efficiency). The Meaningful Human
Control is that a human has specified the guardrails and capabilities the agent operates
within, not that a human performs every step (ADR-019 D6). The framework supplies the
deterministic, auditable signal; the organisation owns the policy and the decision.
