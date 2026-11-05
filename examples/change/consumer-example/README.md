# Consuming a change report — operative examples

Illustrative sketches of how a **consumer** reacts to an OSCAL4Rail change report (an OSCAL
`mapping-collection`, ADR-019). These are **not** part of the framework and **not** a
shipped product: the framework delivers the deterministic, machine-readable signal; the
reaction and its policy belong to the consuming organisation (ADR-019 D4/D6).

Because the change report is deterministic, machine-readable OSCAL, **any** mechanism can
consume it — no agent required. One signal, many consumers.

## Two ways to consume

| | Consumer | Trigger | File |
|---|---|---|---|
| **Non-agentic** (primary, simplest) | CI / merge / build pipeline, or a scheduled job | MR, push, or cron | [`ci-pipeline.md`](./ci-pipeline.md) |
| **Agentic** (optional build-up) | a micro-agent per catalog | webhook or schedule | [`agentic.md`](./agentic.md) |

Both read the **same** report with the **same** deterministic logic. The shared core is a
tiny reader/router:

- [`react_to_change.py`](./react_to_change.py) — reads the report, prints the derived
  reaction per change, and sets an exit code for gating. It **reads and routes only**; it
  does not act. Replace its policy (`GATING`/`NOTIFY` sets and the `react()` body) with
  your own.

## Try it

```bash
pip install jsonschema pyyaml
# against the worked example in this repo
python examples/change/consumer-example/react_to_change.py examples/change/example-change.yaml
```

## The boundary (the same for pipeline and agent)

- **Allowed** within the guardrails the organisation sets: detect, classify (via
  `tools/change`), validate, route, gate, notify, open a downstream issue/MR, request an
  L4 re-assessment.
- **Not** the consumer's to do autonomously: approve the change, decide a tightening is
  correct, or modify and merge a downstream catalog. That is the owner's governance
  decision (Meaningful Human Control). Consistency/satisfaction is the Assessment layer
  (L4), and validation checks form, not content (ADR-019 D8).
