# Stage 0 evaluation

The primary Stage 0 metric is defect detection recall:

```text
correct benchmark defects detected / total benchmark defects
```

A correct detection requires an exact normalized match on `defect_type` and
`affected_control`. Root-cause accuracy is measured separately because the
baseline schema permits a free-text likely-cause explanation. Normalization
lowercases fields, converts spaces and hyphens to underscores, and applies the
small public alias table in `evaluation/evaluator.py`. Each prediction can match
at most one gold defect.

The evaluator will also report false positives, affected-control accuracy,
root-cause accuracy, actions, runtime, model calls, tokens when returned by the
provider, and approximate cost when model pricing is configured.

Gold files must only be opened by evaluator code after an agent run. They must
never be included in prompts or Blender tool arguments.

## Recorded Stage 0 result

The fixed Gemini 3.5 Flash Lite baseline attempted all ten cases (11 gold
defects). It detected 2 defects for 18.2% recall, produced 4 false positives,
achieved 66.7% affected-control accuracy, and 0% normalized root-cause accuracy.
Ten model calls used 7,549 input and 1,087 output tokens. Approximate cost is not
reported because pricing was not configured at run time.

The original evaluation implementation incorrectly required the free-text root
cause to equal the categorical gold code for a detection to count. This was
corrected before reporting results; saved agent outputs were not rerun or changed.
