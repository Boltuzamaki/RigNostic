# Stage 0 evaluation

The primary Stage 0 metric is defect detection recall:

```text
correct benchmark defects detected / total benchmark defects
```

A correct detection requires an exact normalized match on `defect_type`,
`affected_control`, and `root_cause`. Normalization lowercases fields, converts
spaces and hyphens to underscores, and applies the small public alias table in
`evaluation/evaluator.py`. Each prediction can match at most one gold defect.

The evaluator will also report false positives, affected-control accuracy,
root-cause accuracy, actions, runtime, model calls, tokens when returned by the
provider, and approximate cost when model pricing is configured.

Gold files must only be opened by evaluator code after an agent run. They must
never be included in prompts or Blender tool arguments.

No baseline metrics exist yet. Blender and LLM credentials were unavailable, so
no benchmark cases or agent runs could honestly be produced.

