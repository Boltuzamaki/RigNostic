# Architecture

## Stage 0 target

```text
.blend file
     |
     v
Basic Blender tools
     |
     v
One general-purpose LLM agent
     |
     v
Structured defect report
     |
     v
Deterministic evaluator
```

The checked-in Stage 0 infrastructure contains configuration, a headless process
runner, a deterministic synthetic rig and ten-case benchmark, coarse Blender
tools, result schemas, deterministic matching, and trajectory logging. The
executable LLM agent loop and evaluation remain blocked by missing model access.

Stage 0 does not contain RigInventory, semantic control mapping, adaptive test
planning, pairwise testing, repair, rollback, visual verification, or regression
loops.
