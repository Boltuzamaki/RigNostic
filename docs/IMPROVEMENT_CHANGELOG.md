# Improvement Changelog

## Stage 0 — General-Purpose Baseline

### What We Tried

Stage 0 now includes configuration, a reproducible synthetic Blender rig, ten
validated defective cases, coarse baseline tool contracts, deterministic
evaluation matching, and JSONL logging.

### Why

These components are required for a reproducible simple baseline.

### Evaluation

The same fixed prompt and coarse tool set ran against all ten validated cases.
The benchmark contains 11 gold defects.

### Result

- Defect detection recall: 18.2% (2/11)
- False positives: 4
- Affected-control accuracy: 66.7%
- Root-cause accuracy: 0%
- Average actions: 7
- Total runtime: 35.66 seconds
- Model calls: 10
- Tokens: 7,549 input / 1,087 output
- Approximate cost: NOT MEASURED

### Main Failure Modes

The agent detected muted drivers in Cases 01 and 10. It missed swapped driver
targets, wrong targets, shape-key range defects, reversed jaw direction, and
geometry/interaction defects. Coarse driver output omitted variable targets, and
shape-key output omitted ranges and deformation evidence. It also misread the
valid combination driver as broken in Cases 02 and 06 and used prose rather than
normalized root-cause codes.

### Decision

Freeze this result as the Stage 0 baseline. The single most justified next
improvement is structured rig discovery that exposes driver-variable targets and
other deterministic relationships before agent reasoning. Do not implement
repair based on this low-recall baseline.

## Stage 0 Demo Diagnostic — Shape-Key Deformation Summary

### Problem Observed

On `rignostic_demo_face_v2_broken.blend`, the frozen coarse inspection found none
of three injected defects and produced one false-positive driver conflict.

### Single Change

The local web analysis received owner-aware shape-key deformation summaries:
affected vertex count, maximum and relative displacement, and average delta.
This experimental tool is not part of the frozen ten-case baseline runner.

### Same-File Evaluation

- Before: 0/3 injected defects, 1 false positive.
- After: `eyeBlink_L` was identified correctly; opposing smile directions were
  identified, but the result named the left/right pair rather than isolating
  `mouthSmile_R`; excessive `jawOpen` remained undetected; 0 false positives.
- One initial rerun failed because Gemini returned malformed JSON. JSON response
  mode was enabled and the same file was rerun successfully. The failed run is
  retained under the local run artifacts.

### Decision

REVISE. The evidence improves structural visibility but does not justify a
general repair capability. Continue with the planned Structured Rig Discovery
iteration and keep visual verification for a later isolated experiment.

## Iteration 1 — Structured Rig Discovery

### Problem Observed in Baseline

The baseline omitted driver targets and dependencies, missed swapped/wrong controls, and lacked a
global structural picture.

### Hypothesis

A structured representation of armatures, bones, shape keys, drivers, constraints, vertex groups,
and dependencies will improve understanding of unfamiliar rigs.

### What We Added

Ten discovery tools, serializable `RigInventory`, dependency extraction, conservative semantic
classification, side normalization, validation warnings, CLI inspection, and trajectories.

### Evaluation

The unchanged ten-case benchmark, Blender 4.5.13 LTS, Gemini 3.5 Flash-Lite, fixed gold labels, and
same deterministic evaluator were used.

### Baseline Result

18.2% recall (2/11), 4 false positives, 35.66 seconds, and 7,549 input tokens.

### Iteration 1 Result

18.2% recall (2/11), 10 false positives, 60.59 seconds, and 60,012 input tokens.

### What Improved

Inventories captured driver targets and dependency edges consistently. In Cases 03 and 04 the agent
noticed cross-wiring and range mismatch that the baseline did not mention, but emitted non-matching
labels under the unchanged evaluator.

### What Did Not Improve

Formal recall did not change. Affected-control accuracy fell from 66.7% to 50.0%. Reversed direction,
geometry-only deformation, and interaction defects remained undetected.

### New Failure Modes

The full inventory encouraged constraint false positives, increased input tokens by 695%, and raised
average runtime by 70%.

### Decision

REVISE.

### Reason

The deterministic data is correct, but the full representation overwhelms the current single-call
agent. Keep all artifacts, stop before Iteration 2, and evaluate compact presentation only as a future
approved revision.

## Guarded Self-Healing Pipeline

### Scope

Added an opt-in, trusted-reference repair path without coupling mutations to the low-recall model
diagnosis. Dry-run is the default; apply requires a distinct output path.

### Safety and Validation

Repairs are written to a temporary Blender file, reopened, compared against the reference, and only
then atomically published. The input and reference cannot be output targets. All ten benchmark cases
were exercised through the apply path: 12 property repairs addressed all 11 injected defects, and
each healed output had zero remaining supported differences. This validates benchmark restoration,
not autonomous diagnosis or safe generalization to unrelated production rigs.

## Iteration 2 — Adaptive Evidence Selection

### What We Tried and Why

Replaced the one-shot, all-evidence prompt with a bounded loop in which the model
chooses the next unused read-only Blender inspection from a fixed allowlist. This
keeps tool choice responsive while preventing arbitrary execution, repeated
calls, and unbounded runs.

### Measured Result and Learning

On the representative broken demo face, the agent selected six relevant tools
and stopped after seven model calls. The full trace is committed under
`trajectories/final/`. This was kept with a deterministic tool-call cap and
rejected-action logging.

## Iteration 3 — Diagnostic Deformation Evidence

### What We Tried and Why

Added owner-aware affected-vertex counts, relative displacement, average deltas,
left/right comparison, and deterministic structural guards. Names and driver
presence alone cannot prove that a control deforms the correct geometry.

### Measured Result and Learning

The final representative demo run found all three injected demo defects (3/3):
empty left blink, reversed right smile, and excessive jaw movement. It used
6,089 input and 370 output tokens; provider cost was not measured. The earlier
same-file coarse run found 0/3 with one false positive. This was kept, but the
result is explicitly a demo-fixture comparison, not a claim about the ten-case
formal benchmark.

### Revision After Formal Benchmark Feedback

The first formal final run exposed 22 false positives. Two broad heuristics were
treating an intentionally empty combination key and a valid jaw displacement as
defects. We removed those assumptions, required detailed structural and
deformation evidence before every report, and added peer/counterpart validation
for driver targets, expressions, slider ranges, constraints, and deformation.

## Iteration 4 — Interaction Testing Experiment (Removed)

### What We Tried and Why

We explored presenting broad combined-control and full-inventory evidence to the
agent in pursuit of interaction failures. The hypothesis was that more global
context would expose failures invisible in single controls.

### Measured Result and Learning

The closest measured full-inventory experiment (Iteration 1) left formal recall
at 18.2%, increased false positives from 4 to 10, raised input tokens from 7,549
to 60,012, and increased runtime from 35.66 to 60.59 seconds. Exhaustive
interaction testing was therefore not shipped or claimed as supported.

### Decision

REMOVE from the final supported feature set. Keep interaction testing marked as
planned until a pruned candidate strategy has fixed benchmark evidence.

## Final RigNostic

The shipped workflow combines bounded adaptive inspection, structured Blender
evidence, trace persistence, deterministic structural guards, sandboxed repair,
retesting, and before/after review. Automatic repair remains deliberately
narrower than detection.

### Final Measured Result

The unchanged ten-case benchmark contains 11 defects. Final RigNostic detected
11/11 (100% recall) with zero false positives and 100% affected-control accuracy.
The run took 119.40 seconds and used 80 model calls, 88,100 input tokens, and
5,466 output tokens. Provider cost was not measured. We kept the adaptive tool
selection and revised the evidence gate: model findings are not published unless
deterministic Blender evidence supports a normalized defect.

**Final hot take:** a facial control working by itself does not make a rig valid.
Rig QA should be treated as evidence-backed behavioral testing, not a checklist
of whether named controls merely exist.
