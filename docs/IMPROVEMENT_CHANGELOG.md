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
