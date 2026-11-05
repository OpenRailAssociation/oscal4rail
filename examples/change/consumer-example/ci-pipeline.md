# CI pipeline integration (non-agentic consumer)

Reference snippets showing how a **pipeline** consumes the OSCAL4Rail change report, with
no agent and no LLM: run `tools/change` on the merge range, then gate on the result. This
is the simplest, fully deterministic consumer (ADR-019: one signal, many consumers).

These are illustrative sketches, not a shipped pipeline. Adapt paths and policy to your
project. The gating policy lives in `react_to_change.py` (`GATING` set), which is yours.

## GitLab CI (`.gitlab-ci.yml`)

```yaml
oscal4rail-change-gate:
  stage: test
  image: python:3.12-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - pip install -q jsonschema pyyaml
    # base = target branch, head = source branch of the MR
    - python tools/change.py
        "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME" "$CI_COMMIT_SHA"
        catalogs/example/catalog.yaml
        --rules-from "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME:rules/example-rules.yaml"
        --rules-to "$CI_COMMIT_SHA:rules/example-rules.yaml"
        -o change.yaml
    # the change report is itself OSCAL — validate it
    - python tools/validate.py --strict change.yaml
    # route + gate (exit 2 fails the job on a gating change)
    - python examples/change/consumer-example/react_to_change.py change.yaml
  artifacts:
    paths: [change.yaml]        # the OSCAL change report, kept for the reviewer
```

## GitHub Actions (`.github/workflows/change-gate.yml`)

```yaml
name: oscal4rail-change-gate
on: pull_request
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }     # need base..head
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -q jsonschema pyyaml
      - run: |
          python tools/change.py \
            "origin/${{ github.base_ref }}" "${{ github.sha }}" \
            catalogs/example/catalog.yaml \
            --rules-from "origin/${{ github.base_ref }}:rules/example-rules.yaml" \
            --rules-to "${{ github.sha }}:rules/example-rules.yaml" \
            -o change.yaml
      - run: python tools/validate.py --strict change.yaml
      - run: python examples/change/consumer-example/react_to_change.py change.yaml
```

## What the pipeline does and does not do

- **Does**: detect, classify (via `tools/change`), validate the OSCAL report, and gate /
  surface the result. Deterministic, no LLM.
- **Does not**: decide whether a tightening is acceptable, or change a downstream catalog.
  That is the owner's governance decision (MHC). Consistency/satisfaction is L4.

A scheduled variant (cron) uses the same step with two tags/refs instead of the MR range,
to watch a catalog continuously and open an issue / trigger a workflow on change.
